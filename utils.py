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