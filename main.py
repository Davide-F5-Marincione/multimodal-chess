import pygame

import objects
import config as cfg


# Initialize Pygame
pygame.init()

# Set up some constants
WIDTH, HEIGHT = 800, 800

# Create the screen
renderer = objects.Renderer((WIDTH, HEIGHT))
clicker = objects.Clicker()

objects.load_consts()

board = objects.Board(renderer, clicker, (10, 10))
objects.FloatingText(renderer, (10, 700), "Press \'R\' to restart", 16, cfg.colors["boardtext"])

# Main loop
pygame.mouse.set_visible(False)
running = True
while running:

    mouse_pos = pygame.mouse.get_pos()
    clicker.highlight(mouse_pos)
    for event in pygame.event.get():
        match event.type:
            case pygame.QUIT:
                running = False
            case pygame.MOUSEBUTTONDOWN:
                clicker.execute_click()
            case pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    board.reset()       

    renderer.step(mouse_pos)

# Quit Pygame
pygame.quit()