import pygame

import objects


# Initialize Pygame
pygame.init()

# Set up some constants
WIDTH, HEIGHT = 800, 800

# Create the screen
renderer = objects.Renderer((WIDTH, HEIGHT))
clicker = objects.Clicker()

objects.Board(renderer, clicker, (10, 10))

# Main loop
pygame.mouse.set_visible(False)
running = True
while running:

    mouse_pos = pygame.mouse.get_pos()
    clicker.highlight(mouse_pos)
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN:
            clicker.execute_click()
        if event.type == pygame.QUIT:
            running = False

    renderer.step(mouse_pos)

# Quit Pygame
pygame.quit()