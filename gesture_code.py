import cv2 as cv
import mediapipe as mp
from typing import List
from threading import Thread

from timeit import default_timer as timer

def extract_hand_pos(landmarks):
    x = landmarks[0].x * .5 + landmarks[5].x * .125 + landmarks[9].x * .125 + landmarks[13].x * .125 + landmarks[17].x * .125
    y = landmarks[0].y * .5 + landmarks[5].y * .125 + landmarks[9].y * .125 + landmarks[13].y * .125 + landmarks[17].y * .125
    z = landmarks[0].z * .5 + landmarks[5].z * .125 + landmarks[9].z * .125 + landmarks[13].z * .125 + landmarks[17].z * .125
    return x, y, z

def avg_hand_pos(hand_pos1, hand_pos2, alpha=.5):
    return tuple(map(lambda x, y: (1-alpha)*x + alpha*y, hand_pos1, hand_pos2))


class HandDetector:
    def __init__(self, model_path='hand_landmarker.task', h_flip=False, alpha=.86, reset_time_ms=1000, decay_v=.86):
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
        self.stopped = True
        self.reset = False

        self.hand_info = ((0,0,0), 0, (0,0,0))
        self.alpha = alpha
        self.last_seen = 0
        self.prev_callback = 0
        
        def callback(result: mp.tasks.vision.HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
            prev_timestamp = self.prev_callback
            self.prev_callback = timestamp_ms
            if len(result.hand_landmarks):
                self.last_seen = self.prev_callback
                if self.reset:
                    self.reset = False
                    self.hand_info = extract_hand_pos(result.hand_landmarks[0]), int(result.handedness[0][0] == "Left"), (0,0,0)
                else:
                    curr_handedness = int(result.handedness[0][0] == "Left")
                    curr_hand_pos = extract_hand_pos(result.hand_landmarks[0])
                    new_hand_pos = avg_hand_pos(curr_hand_pos, self.hand_info[0], self.alpha)
                    self.hand_info = new_hand_pos, (1-alpha) * curr_handedness + alpha * self.hand_info[1], tuple(map(lambda x, y: (x - y) / (timestamp_ms - prev_timestamp), new_hand_pos, self.hand_info[0]))
            else:
                if timestamp_ms - self.last_seen > reset_time_ms:
                    self.reset = True
                elif self.reset is False:
                    self.hand_info = tuple(map(lambda x, y: x + y * (self.prev_callback - prev_timestamp), self.hand_info[0], self.hand_info[2])), (1-alpha) * curr_handedness + alpha * self.hand_info[1], tuple(map(lambda x, y: (x - y) / (timestamp_ms - prev_timestamp), new_hand_pos, self.hand_info[0]))


        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            result_callback=callback)
        self.hand_landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)

        self.t = Thread(target=self.update, args=())
        self.t.daemon = True

    def start(self):
        self.reset = True
        self.stopped = False
        self.t.start()

    def update(self):
        while True:
            if self.stopped is True:
                break
            self.result = None
            self.grabbed, self.frame = self.cam.read()
            if self.grabbed is False:
                print('No frames to read')
                self.stopped = True
                break

            if self.h_flip:
                self.frame = cv.flip(self.frame, 1)
            
            frame_timestamp_ms = int(timer() * 1000)
            self.hand_landmarker.detect_async(mp.Image(image_format=mp.ImageFormat.SRGB, data= cv.cvtColor(self.frame, cv.COLOR_BGR2RGB)), frame_timestamp_ms)

        self.cam.release()

    def read(self):
        return self.hand_info, self.reset
    
    def stop(self):
        self.stopped = True