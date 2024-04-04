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
restart_button = objects.RestartButton(renderer, clicker, (650, 20), board)

font = pygame.font.Font("resources\FreeSerif.ttf", 32)
pieces_test = font.render("Test: ♔♕♖♗♘♙♚♛♜♝♞♟︎", True, cfg.colors["boardtext"], cfg.colors["background"])

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
    renderer.screen.blit(pieces_test, (10, 700))


# Quit Pygame
pygame.quit()