import pygame
from timeit import default_timer as timer

import objects
import config as cfg
import gesture_code


# Initialize Pygame
pygame.init()

# Set up some constants
WIDTH, HEIGHT = 800, 800

# Create the screen
renderer = objects.Renderer(objects.Point(WIDTH, HEIGHT))
clicker = objects.Clicker(renderer)

objects.load_consts()

context_text = objects.FloatingText(renderer, objects.Point(300, 400), "No hand detected", 16, cfg.colors["boardtext"])
hand_detector = gesture_code.HandDetector(h_flip=True)

# Main loop
pygame.mouse.set_visible(False)
running = True
cursor_pos = objects.Point(0, 0)
mouse_pos = objects.Point(0, 0)

hand_detector.start()

while running:
    curr_time = int(timer() * 1000)
    new_mouse_pos = objects.Point(*pygame.mouse.get_pos())
    is_tracking = hand_detector.process_gestures(curr_time)

    if new_mouse_pos != mouse_pos:
        mouse_pos = new_mouse_pos
        cursor_pos = mouse_pos
    else:
        if is_tracking:
            context_text.set_text("Detecting hand")
            cursor_pos = objects.Point(int(hand_detector.hand_pos[0] * WIDTH), int(hand_detector.hand_pos[1] * HEIGHT))
        else:
            context_text.set_text("No hand detected")
    
    clicker.highlight(cursor_pos)
    for event in pygame.event.get():
        match event.type:
            case pygame.QUIT:
                running = False
            case pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicker.execute_click()
            case pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    clicker.execute_click(False)
                
    renderer.step(cursor_pos)

hand_detector.stop()

# Quit Pygame
pygame.quit()