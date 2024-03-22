import pygame
import numpy as np
import io

import utils
import objects
import config as cfg


# Initialize Pygame
pygame.init()

# Set up some constants
WIDTH, HEIGHT = 800, 800

# Create the screen
drawer = objects.Drawer(WIDTH, HEIGHT)

objects.Board(drawer, 10, 10, 70)

# Main loop
pygame.mouse.set_visible(False)
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    drawer.step()

# Quit Pygame
pygame.quit()