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

def make_svg_piece(piece_type, piece_size = 70):
    with open(f"resources/{piece_type}.svg") as f:
        svg_piece = f.read()

    svg_piece = svg_piece.replace("width=\"45\" height=\"45\"",
                                  f"width=\"{piece_size}\" height=\"{piece_size}\" transform=\"scale({piece_size/45})\"")

    return svg_piece


def make_svg_promotion(piece_size = 70):
    with open(f"resources/promotionprompt.svg") as f:
        svg_promotion = f.read()

    svg_promotion = svg_promotion.replace("width=\"315\" height=\"165\"",
                                  f"width=\"{int(piece_size * 4.5)}\" height=\"{int(piece_size * 2.357142857142857)}\" transform=\"scale({piece_size/70})\"")

    return svg_promotion

def make_svg_reset(size=(140, 50), stroke_width=4):
    with open(f"resources/resetbutton.svg") as f:
        text = f.read()

    text = text.replace("outer_width", f"{size[0]}")
    text = text.replace("inner_width", f"{size[0] - stroke_width}")
    text = text.replace("outer_height", f"{size[1]}")
    text = text.replace("inner_height", f"{size[1] - stroke_width}")

    text = text.replace("stroke_width", f"{stroke_width}")
    text = text.replace("x_pos", f"{stroke_width//2}")
    text = text.replace("y_pos", f"{stroke_width//2}")

    text = text.replace("rx_val", f"7")
    text = text.replace("ry_val", f"7")

    text = text.replace("stroke_color", cfg.colors["reset_button"])
    text = text.replace("fill_val", cfg.colors["background"])

    return text


def plus_cursor_mask(size=19, bottom=7, top=11):
    # Create an empty ndarray of size*size filled with zeros
    plus_array = np.zeros((size, size), dtype=np.uint8)
    
    # Set the plus sign pattern in the array
    plus_array[bottom:top+1, :] = 127
    plus_array[:, bottom:top+1] = 127
    
    return plus_array