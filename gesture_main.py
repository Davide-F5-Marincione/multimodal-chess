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

context_text = objects.FloatingText(renderer, objects.Point(300, 400), "Mouse tracking", 16, cfg.colors["boardtext"])
interaction_text = objects.FloatingText(renderer, objects.Point(300, 450), "No interaction", 16, cfg.colors["boardtext"])
hand_detector = gesture_code.HandDetector(h_flip=True, scales=[[.25, .25], [.75, .75]])

# Main loop
pygame.mouse.set_visible(False)
running = True
cursor_pos = objects.Point(0, 0)
mouse_pos = objects.Point(0, 0)
mouse_timestamp = -1000
last_interaction = -1000

hand_detector.start()

while running:
    curr_time = int(timer() * 1000)
    new_mouse_pos = objects.Point(*pygame.mouse.get_pos())
    if new_mouse_pos != mouse_pos:
        mouse_pos = new_mouse_pos
        mouse_timestamp = curr_time
    hand_cursor_pos, hand_click, hand_release, hand_timestamp = hand_detector.process_gestures(curr_time)

    if mouse_timestamp >= hand_timestamp:
        cursor_pos = mouse_pos
        context_text.set_text("Mouse tracking")
    else:
        cursor_pos = objects.Point(int(hand_cursor_pos[0] * WIDTH), int(hand_cursor_pos[1] * HEIGHT))
        context_text.set_text("Hand tracking")
        if hand_click:
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1))
        if hand_release:
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1))
    
    clicker.highlight(cursor_pos)
    for event in pygame.event.get():
        match event.type:
            case pygame.QUIT:
                running = False
            case pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicker.execute_click()
                    interaction_text.set_text("Click")
                    last_interaction = curr_time
            case pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    clicker.execute_click(False)
                    interaction_text.set_text("Release")
                    last_interaction = curr_time

    if curr_time - last_interaction > 1000:
        interaction_text.set_text("No interaction")


    renderer.step(cursor_pos)

hand_detector.stop()

# Quit Pygame
pygame.quit()