import tkinter as tk
import tksvg
import config as cfg
from PIL import ImageGrab, ImageTk, ImageOps


class InvertingCursor(tk.Canvas):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.cursor_image = None
        self.cursor = None

    def update_cursor(self):
        # Capture an image of the area under the cursor
        x, y = self.winfo_pointerxy()
        screenshot = ImageGrab.grab(bbox=(x, y, x+20, y+20))
        inverted = ImageOps.invert(screenshot)
        self.cursor_image = ImageTk.PhotoImage(inverted)

        # If the cursor already exists, move it to the new position
        if self.cursor:
            self.delete(self.cursor)
        self.cursor = self.create_image(x - self.winfo_rootx(), y - self.winfo_rooty(), image=self.cursor_image)

    def track_cursor(self):
        self.update_cursor()
        self.after(10, self.track_cursor)  # Update the cursor position every 10 ms



# Create the main window
window = tk.Tk()
window.title("Test")
# window.attributes('-fullscreen', True)
window.configure(bg=cfg.colors["background"], bd=0, highlightthickness=0)
# window.geometry("800x800")

square_size = 70

# Setup drawing of chess board

canvas = InvertingCursor(master=window, bg=cfg.colors["background"], offset="nw", bd=0, highlightthickness=0, width=8*square_size, height=8*square_size)

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

canvas.track_cursor()


# Run the main event loop
window.mainloop()

