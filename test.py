import pygame
import numpy as np

# Initialize Pygame
pygame.init()

# Set up some constants
WIDTH, HEIGHT = 640, 480
WHITE = (255, 255, 255)

# Create the screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Fill the screen white
screen.fill(WHITE)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Get the current mouse position
    x, y = pygame.mouse.get_pos()

    # Capture the area under the cursor
    area = pygame.Surface((20, 20))
    area.blit(screen, (0, 0), (x, y, 20, 20))

    # Convert the surface to a numpy array and invert the colors
    pixels = pygame.surfarray.array3d(area)
    inverted_pixels = 255 - pixels

    # Convert the inverted array back to a surface and blit it to the screen
    inverted_area = pygame.surfarray.make_surface(inverted_pixels)
    screen.blit(inverted_area, (x, y))

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()