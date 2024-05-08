import pygame

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

while running:
    new_mouse_pos = objects.Point(*pygame.mouse.get_pos())
    hand_detector.update()
    if new_mouse_pos != mouse_pos:
        mouse_pos = new_mouse_pos
        cursor_pos = mouse_pos
    else:
        if not hand_detector.reset:
            if hand_detector.handedness > .5:
                context_text.set_text("Right hand detected")
            else:
                context_text.set_text("Left hand detected")

            cursor_pos = objects.Point(int(hand_detector.cursor_pos[0] * WIDTH), int(hand_detector.cursor_pos[1] * HEIGHT))
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