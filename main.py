import tkinter as tk
import tksvg
import config as cfg

# Create the main window
window = tk.Tk()
window.title("Test")
window.attributes('-fullscreen', True)
window.configure(bg=cfg.colors["background"], bd=0, highlightthickness=0)
# window.geometry("800x800")

square_size = 70

# Setup drawing of chess board
canvas = tk.Canvas(master=window, bg=cfg.colors["background"], offset="nw", bd=0, highlightthickness=0, width=8*square_size, height=8*square_size)

svg_board = f"<svg width=\"{8*square_size}\" height=\"{8*square_size}\">"
for i in range(8):
    for j in range(8):
        if (i+j) % 2 == 0:
            svg_board += f"<rect x=\"{i*square_size}\" y=\"{j*square_size}\" width=\"{square_size}\" height=\"{square_size}\" fill=\"" + cfg.colors["light_square"] + "\"/>"
        else:
            svg_board += f"<rect x=\"{i*square_size}\" y=\"{j*square_size}\" width=\"{square_size}\" height=\"{square_size}\" fill=\"" + cfg.colors["dark_square"] + "\"/>"
svg_board += "</svg>"

board_image = tksvg.SvgImage(master=canvas, data=svg_board)
canvas.create_image((0, 0), image=board_image, anchor="nw")

# Figured out how to position stuff yaaaaaaay!
canvas.pack(side="top", fill="both", expand=True, padx=0, pady=0)

# Run the main event loop
window.mainloop()