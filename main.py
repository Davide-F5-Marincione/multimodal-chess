import pygame
import numpy as np
import io

import utils
import config as cfg


# Initialize Pygame
pygame.init()

# Set up some constants
WIDTH, HEIGHT = 800, 800

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))

screen.fill(cfg.colors["background"])

board = pygame.image.load(io.BytesIO(utils.make_svg_board().encode()))

# Main loop
pygame.mouse.set_visible(False)
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.blit(board, (0, 0))

    utils.update_display(screen)

# Quit Pygame
pygame.quit()