import cv2 as cv
import numpy as np
import mediapipe as mp
from threading import Thread
from collections import deque

import config as cfg

from timeit import default_timer as timer

class Hand:
    def __init__(self, hand_repr, timestamp_ms, prev_click=False):
        abs_hand = np.array([(landmark.x, landmark.y, landmark.z) for landmark in hand_repr.hand_landmarks[0]])

        palm = abs_hand[0] * .5 + abs_hand[5] * .125 + abs_hand[9] * .125 + abs_hand[13] * .125 + abs_hand[17] * .125 # Center of palm

        palm_width = np.linalg.norm(abs_hand[5] - abs_hand[17]) # Distance between index and pinky base
        rel_hand = (abs_hand - palm) / palm_width # Normalize to palm

        wrist = rel_hand[0]
        index_base = rel_hand[5]
        middle_base = rel_hand[9]
        pinky_base = rel_hand[17]

        palm_normal = np.cross(index_base - wrist, pinky_base - wrist)
        palm_normal = palm_normal / np.linalg.norm(palm_normal)
        
        if hand_repr.handedness[0][0].category_name == 'Left':
            palm_normal = -palm_normal

        pinky_normal = np.cross(palm_normal, middle_base - wrist)
        pinky_normal = pinky_normal / np.linalg.norm(pinky_normal)

        fingers_normal = np.cross(pinky_normal, palm_normal)
        fingers_normal = fingers_normal / np.linalg.norm(fingers_normal)

        if hand_repr.handedness[0][0].category_name == 'Left':
            pinky_normal = -pinky_normal

        basis = np.array([pinky_normal, fingers_normal, palm_normal]).T
        norm_hand = rel_hand @ basis

        self.abs_hand = abs_hand
        self.origin = palm
        self.orig_screen = self.origin[:2]
        self.basis = basis
        self.norm_hand = norm_hand
        self.handedness = hand_repr.handedness[0][0].category_name == 'Right'
        self.palm_width = palm_width
        self.timestamp_ms = timestamp_ms
        self.is_click = self._is_clicking(prev_click)

    def is_same(self, other):
        if self.handedness != other.handedness:
            return False
        
        if abs(self.palm_width - other.palm_width) > self.palm_width * cfg.MIN_PALM_WIDTH_DIFFERENCE:
            return False
        
        return np.linalg.norm(self.origin - other.origin) < self.palm_width * cfg.MAX_HAND_MOVEMENT

    def is_facing_screen(self):
        return self.basis[2, 2] < 0
    
    def _is_clicking(self, prev_click=False):

        thumb_vec = self.norm_hand[4]
        index_vec = self.norm_hand[8]

        thumb_vec = thumb_vec / np.linalg.norm(thumb_vec)
        index_vec = index_vec / np.linalg.norm(index_vec)

        dot = np.dot(thumb_vec, index_vec)
        dist = np.linalg.norm(thumb_vec - index_vec)

        return dot >= (cfg.DOT_CLICK_HYST if prev_click else cfg.DOT_CLICK) and dist <= (cfg.DIST_CLICK_HYST if prev_click else cfg.DIST_CLICK)
    
    def scaled(self, limits):
        return np.clip((self.orig_screen - limits[0]) / (limits[1] - limits[0]), 0, 1)

class HandDetector:
    def __init__(self, model_path='hand_landmarker.task', h_flip=False, cursor_speed=.5, delete_gesture_ms=200, end_tracking_ms=700, min_cursor_movement=.01, scales=[[.25,.25],[.75,.75]]):
        self.h_flip = h_flip

        self.cam = cv.VideoCapture(0)
        if not self.cam.isOpened():
            print("Cannot open camera")
            exit(0)

        self.scales = np.array(scales)

        self.cursor_pos = np.zeros(2, dtype=np.float32)
        self.min_cursor_movement = min_cursor_movement
        self.cursor_speed = cursor_speed
        self.clicks = deque()
        self.prev_click = False
        self.end_tracking_ms = end_tracking_ms
        self.delete_gesture_ms = delete_gesture_ms
        self.reset = True
        self.last_timestamp = None
        self.curr_hand = None
        self.prev_hand = None
        
        def callback(result: mp.tasks.vision.HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
            if len(result.hand_landmarks) > 0:
                if self.curr_hand is None:
                    self.curr_hand = Hand(result, timestamp_ms)
                else:
                    self.prev_hand = self.curr_hand
                    self.curr_hand = Hand(result, timestamp_ms, self.prev_hand.is_click)
                self.clicks.append((self.curr_hand.is_click, timestamp_ms))
            self.go = True
                

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            result_callback=callback)
        self.hand_landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)

        self.t = Thread(target=self.update, args=())
        self.t.daemon = True
        self.stopped = True

    def set_scales(self, scales):
        self.scales = np.array(scales)

    def start(self):
        self.stopped = False
        self.curr_hand = None
        self.prev_hand = None
        self.clicks = deque()
        self.last_timestamp = None
        self.reset = True
        self.prev_click = False
        self.t.start()

    def stop(self):
        self.stopped = True

    def update(self):
        self.go = True
        while not self.stopped:
            self.grabbed, self.frame = self.cam.read()
            if self.grabbed is False:
                print('No frames to read')
                self.stopped = True
                break

            if self.h_flip:
                self.frame = cv.flip(self.frame, 1)
            if self.go:
                self.frame.flags.writeable = False
                self.go = False
                self.hand_landmarker.detect_async(mp.Image(image_format=mp.ImageFormat.SRGB, data= cv.cvtColor(self.frame, cv.COLOR_BGR2RGB)), int(timer() * 1000))

        self.cam.release()
    
    def process_gestures(self, curr_time_ms):
        if self.last_timestamp is None:
            self.last_timestamp = curr_time_ms

        delta_t = (curr_time_ms - self.last_timestamp) / 1000
        self.last_timestamp = curr_time_ms

        if self.curr_hand is None:
            return (None, False, False, -1000)
        
        if self.reset:
            self.reset = False
            self.cursor_pos = self.curr_hand.scaled(self.scales)
        
        if not self.prev_hand is None:
            if not self.prev_hand.is_same(self.curr_hand):
                pass # Do something? Hands are different!

            dist = np.linalg.norm(self.prev_hand.scaled(self.scales) - self.cursor_pos)
            if dist <= self.min_cursor_movement:
                self.prev_hand = None


        dist = np.linalg.norm(self.curr_hand.scaled(self.scales) - self.cursor_pos)
        if self.prev_hand is None:
            # Linear interpolation
            if dist > self.min_cursor_movement:
                perc = min(1, self.cursor_speed * delta_t / dist)
                self.cursor_pos = np.clip(self.cursor_pos + (self.curr_hand.scaled(self.scales) - self.cursor_pos) * perc ,0,1)
        else:
            # Quadratic interpolation
            if dist > self.min_cursor_movement:
                perc = min(1, self.cursor_speed * delta_t / dist)

                p1 = self.cursor_pos + (self.prev_hand.scaled(self.scales) - self.cursor_pos) * perc
                p2 = self.prev_hand.scaled(self.scales) + (self.curr_hand.scaled(self.scales) - self.prev_hand.scaled(self.scales)) * perc

                self.cursor_pos = np.clip(p1 + (p2 - p1) * perc, 0, 1)

        # self.curr_hand.return_index_thumb()

        while len(self.clicks) > 0:
            click, timestamp = self.clicks[0]
            if timestamp + self.delete_gesture_ms >= curr_time_ms:
                break
            self.clicks.popleft() 

        is_click = False
        for click, timestamp in self.clicks:
            is_click = is_click or click

        release = self.prev_click and not is_click
        click = not self.prev_click and is_click
        self.prev_click = is_click

        check = self.curr_hand.timestamp_ms + self.end_tracking_ms >= curr_time_ms
        if not check:
            self.curr_hand = None
            self.prev_hand = None
            self.click = deque()
            self.prev_click = False
            self.reset = True
            return (None, False, False, -1000)
        return self.cursor_pos, click, release, self.curr_hand.timestamp_ms