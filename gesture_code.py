import cv2 as cv
import numpy as np
import mediapipe as mp

from timeit import default_timer as timer

def extract_hand_pos(landmarks):
    x = landmarks[0].x * .5 + landmarks[5].x * .125 + landmarks[9].x * .125 + landmarks[13].x * .125 + landmarks[17].x * .125
    y = landmarks[0].y * .5 + landmarks[5].y * .125 + landmarks[9].y * .125 + landmarks[13].y * .125 + landmarks[17].y * .125
    z = landmarks[0].z * .5 + landmarks[5].z * .125 + landmarks[9].z * .125 + landmarks[13].z * .125 + landmarks[17].z * .125
    return np.array((x, y, z), dtype=np.float32)

class HandDetector:
    def __init__(self, model_path='hand_landmarker.task', h_flip=False, alpha=.86, in_time=.1, reset_delay=1):
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

        self.screenspace_hand_pos = np.zeros(3, dtype=np.float32)
        self.cursor_pos = np.zeros(3, dtype=np.float32)
        self.cursor_vel = np.zeros(3, dtype=np.float32)
        self.cursor_acc = np.zeros(3, dtype=np.float32)
        self.alpha = alpha

        self.handedness = 0
        self.screenspace_handedness = 0

        self.reset_delay = reset_delay
        self.in_time = in_time
        self.reset = True
        self.last_seen_time = 0

        self.prev_time = 0
        
        def callback(result: mp.tasks.vision.HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
            self.result = result
                    
        self.result = None

        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            result_callback=callback)
        self.hand_landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)


    def update(self):
        self.grabbed, self.frame = self.cam.read()
        if self.grabbed is False:
            print('No frames to read')
            self.stopped = True
            return None

        if self.h_flip:
            self.frame = cv.flip(self.frame, 1)

        curr_time = timer()
        delta_time = curr_time - self.prev_time
        
        self.hand_landmarker.detect_async(mp.Image(image_format=mp.ImageFormat.SRGB, data= cv.cvtColor(self.frame, cv.COLOR_BGR2RGB)), int(curr_time * 1000))

        ran = False

        if not self.result is None:
            if len(self.result.hand_landmarks):
                ran = True
                self.last_seen_time = curr_time
                self.screenspace_hand_pos = extract_hand_pos(self.result.hand_landmarks[0])
                self.screenspace_handedness = float(int(self.result.handedness[0][0].category_name == "Left"))
                if self.reset:
                    self.reset = False
                    self.cursor_pos = self.screenspace_hand_pos
                    self.handedness = self.screenspace_handedness
        
        self.cursor_pos = self.cursor_pos + (self.screenspace_hand_pos - self.cursor_pos) * self.alpha * delta_time / self.in_time
        self.handedness = self.handedness + (self.screenspace_handedness - self.handedness) * self.alpha * delta_time / self.in_time

        if not ran:
            if curr_time - self.last_seen_time > self.reset_delay:
                self.reset = True

        self.prev_time = curr_time

    def stop(self):
        self.cam.release()