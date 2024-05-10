import cv2 as cv
import numpy as np
import mediapipe as mp
from typing import NamedTuple
from threading import Thread
from collections import deque
import matplotlib.pyplot as plt

from timeit import default_timer as timer

class HandData(NamedTuple):
    abs_hand: np.ndarray
    origin: np.ndarray
    basis: np.ndarray
    norm_hand: np.ndarray
    handedness: bool
    palm_width: float

def normalize_hand(hand_repr):
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

    return HandData(abs_hand, palm, basis, norm_hand, hand_repr.handedness[0][0].category_name == 'Right', palm_width)

def is_same_hand(hand1, hand2):
    if hand1.handedness != hand2.handedness:
        return False
    
    if abs(hand1.palm_width - hand2.palm_width) > hand1.palm_width * .1:
        return False
    
    return np.linalg.norm(hand1.origin - hand2.origin) < hand1.palm_width * 10

def is_facing_screen(hand):
    return hand.basis[2, 2] < 0

def recognize_tap(before, after):
    dist = np.linalg.norm(before.origin - after.origin)
    if dist > before.palm_width * .5:
        return False

    index_after = ((after.abs_hand[8] - after.origin) / before.palm_width) @ before.basis
    check = index_after[2] > before.norm_hand[8,2] + .15

    return check


def recognize_grab(hand):

    diff = (np.linalg.norm(hand.norm_hand[4] - hand.norm_hand[8])
            + np.linalg.norm(hand.norm_hand[4] - hand.norm_hand[12])
            + np.linalg.norm(hand.norm_hand[8] - hand.norm_hand[12])) / 3
    if diff > .6:
        return False

    thumb_vec = hand.norm_hand[4]
    index_vec = hand.norm_hand[8]
    middle_vec = hand.norm_hand[12]

    thumb_vec = thumb_vec / np.linalg.norm(thumb_vec)
    index_vec = index_vec / np.linalg.norm(index_vec)
    middle_vec = middle_vec / np.linalg.norm(middle_vec)

    dot1 = np.dot(thumb_vec, index_vec)
    dot2 = np.dot(thumb_vec, middle_vec)
    dot3 = np.dot(index_vec, middle_vec)

    if dot1 < .9 or dot2 < .9 or dot3 < .9:
        return False
    
    return True


class HandDetector:
    def __init__(self, model_path='hand_landmarker.task', h_flip=False, delay_ms=200, min_hand_movement=.005):
        self.h_flip = h_flip

        self.cam = cv.VideoCapture(0)
        if not self.cam.isOpened():
            print("Cannot open camera")
            exit(0)

        # fps_input_stream = int(self.cam.get(5))
        self.grabbed, self.frame = self.cam.read()
        if self.grabbed is False:
            print('No frames to read')
            exit(0)

        self.screenspace_hand_positions = deque()

        self.stopped = True
        
        def callback(result: mp.tasks.vision.HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
            if len(result.hand_landmarks) > 0:
                self.screenspace_hand_positions.append((result, timestamp_ms))

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            # min_tracking_confidence=.1,
            result_callback=callback)
        self.hand_landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)

        self.t = Thread(target=self.update, args=())
        self.t.daemon = True


        self.hand_pos = np.zeros(2, dtype=np.float32)
        self.delay_ms = delay_ms
        self.min_hand_movement = min_hand_movement
        self.curr_line = None

    def start(self):
        self.stopped = False
        self.t.start()

    def update(self):
        while not self.stopped:
            self.grabbed, self.frame = self.cam.read()
            if self.grabbed is False:
                print('No frames to read')
                self.stopped = True
                break

            if self.h_flip:
                self.frame = cv.flip(self.frame, 1)

            self.hand_landmarker.detect_async(mp.Image(image_format=mp.ImageFormat.SRGB, data= cv.cvtColor(self.frame, cv.COLOR_BGR2RGB)), int(timer() * 1000))

        self.cam.release()
    
    def process_gestures(self, curr_time_ms):
        transition_time = curr_time_ms - self.delay_ms
        
        if self.curr_line is None:
            while len(self.screenspace_hand_positions) > 1:
                prev_det = self.screenspace_hand_positions[0]
                next_det = self.screenspace_hand_positions[1]

                if next_det[1] >= transition_time:
                    hand1 = normalize_hand(prev_det[0])
                    hand2 = normalize_hand(next_det[0])

                    if not is_same_hand(hand1, hand2) or not is_facing_screen(hand1) or not is_facing_screen(hand2):
                        self.screenspace_hand_positions.popleft()
                        continue

                    self.curr_line = (self.hand_pos, hand1.origin[:2], hand2.origin[:2], transition_time, next_det[1])
                    print(recognize_tap(hand1, hand2), recognize_grab(hand2))
                    break
                
                self.screenspace_hand_positions.popleft()

        if not self.curr_line is None:
            p1 = self.curr_line[0]
            p2 = self.curr_line[1]
            new_pos = p3 = self.curr_line[2]
            t1 = self.curr_line[3]
            t2 = self.curr_line[4]

            if transition_time < t2:
                i = (transition_time - t1) / (t2 - t1)
                l1 = p1 + (p2 - p1) * i
                l2 = p2 + (p3 - p2) * i
                new_pos = l1 + (l2 - l1) * i
            else:
                self.curr_line = None

            if np.linalg.norm(new_pos - self.hand_pos) > self.min_hand_movement:
                self.hand_pos = new_pos

            return True
    
        return False

    def stop(self):
        self.stopped = True