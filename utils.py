import pygame
import numpy as np


import config as cfg

def make_svg_board(square_size = 70):
    svg_board = f"<svg width=\"{8*square_size}\" height=\"{8*square_size}\">"
    for i in range(8):
        for j in range(8):
            if (i+j) % 2 == 0:
                svg_board += f"<rect x=\"{i*square_size}\" y=\"{j*square_size}\" width=\"{square_size}\" height=\"{square_size}\" fill=\"" + cfg.colors["light_square"] + "\"/>"
            else:
                svg_board += f"<rect x=\"{i*square_size}\" y=\"{j*square_size}\" width=\"{square_size}\" height=\"{square_size}\" fill=\"" + cfg.colors["dark_square"] + "\"/>"
    svg_board += "</svg>"

    return svg_board

def plus_cursor_mask(size=19, bottom=7, top=11):
    # Create an empty ndarray of size*size filled with zeros
    plus_array = np.zeros((size, size), dtype=np.uint8)
    
    # Set the plus sign pattern in the array
    plus_array[bottom:top+1, :] = 127
    plus_array[:, bottom:top+1] = 127
    
    return plus_array

def update_display(screen):
    # Get the current mouse position
    x, y = pygame.mouse.get_pos()

    x = x - cfg.cursor["offset"]
    y = y - cfg.cursor["offset"]

    # Capture the area under the cursor
    area = pygame.Surface((cfg.cursor["size"], cfg.cursor["size"]))
    area.blit(screen, (0, 0), (x, y, cfg.cursor["size"], cfg.cursor["size"]))

    # Convert the surface to a numpy array and make the colors contrasting
    inverted_pixels = update_display.cursor_mask + pygame.surfarray.array3d(area)

    # Convert the inverted array back to a surface and blit it to the screen
    inverted_area = pygame.surfarray.make_surface(inverted_pixels)
    screen.blit(inverted_area, (x, y))

    # Update the display
    pygame.display.flip()

    # Reset colors
    screen.blit(area, (x, y))

update_display.cursor_mask = plus_cursor_mask(cfg.cursor["size"], cfg.cursor["bottom"], cfg.cursor["top"])[:, :, None]