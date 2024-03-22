import pygame
import io

import config as cfg
import utils

class Object:
    def __init__(self, x, y, parent=None):
        self.parent = parent
        self.parent.children.append(self) if parent else None
        self.children = []

        self.set_rel_pos(x, y)

    def set_rel_pos(self, x, y):
        self.rel_x = x
        self.rel_y = y
        
        if self.parent:
            x,y = self.parent.get_abs_pos()
            self.abs_x = x + self.rel_x
            self.abs_y = y + self.rel_y
        else:
            self.abs_x = self.rel_x
            self.abs_y = self.rel_y

        for child in self.children:
            child.set_rel_pos(*child.get_rel_pos())
    
    def get_rel_pos(self):
        return self.rel_x, self.rel_y
    
    def get_abs_pos(self):
        return self.abs_x, self.abs_y


class Drawable(Object):
    def __init__(self, drawer, x, y, parent=None):
        super().__init__(x, y, parent)

        drawer.drawables.append(self)

    def draw(self, screen):
        pass

class Board(Drawable):
    def __init__(self, drawer, x, y, square_size):
        super().__init__(drawer, x, y)
        self.square_size = square_size
        self.img = pygame.image.load(io.BytesIO(utils.make_svg_board(square_size).encode()))

        self.pieces = []
        self.pieces.append(Piece(drawer, square_size//2, square_size//2, self))

    def draw(self, screen):
        screen.blit(self.img, (self.abs_x, self.abs_y))

class Piece(Drawable):
    def __init__(self, drawer, x, y, board_parent, piece_type="lp"):
        super().__init__(drawer, x, y, board_parent)
        self.piece_type = piece_type
        self.img = pygame.image.load("resources/" + piece_type + ".svg")

    def draw(self, screen):
        screen.blit(self.img, (self.abs_x, self.abs_x))

class Drawer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.screen.fill(cfg.colors["background"])

        self.drawables = []

        self.cursor_mask = utils.plus_cursor_mask(cfg.cursor["size"], cfg.cursor["bottom"], cfg.cursor["top"])[:, :, None]

    def step(self):
        for drawable in self.drawables:
            drawable.draw(self.screen)

        # Get the current mouse position
        x, y = pygame.mouse.get_pos()

        x = x - cfg.cursor["offset"]
        y = y - cfg.cursor["offset"]

        # Capture the area under the cursor
        area = pygame.Surface((cfg.cursor["size"], cfg.cursor["size"]))
        area.blit(self.screen, (0, 0), (x, y, cfg.cursor["size"], cfg.cursor["size"]))

        # Convert the surface to a numpy array and make the colors contrasting
        inverted_pixels = self.cursor_mask + pygame.surfarray.array3d(area)

        # Convert the inverted array back to a surface and blit it to the screen
        inverted_area = pygame.surfarray.make_surface(inverted_pixels)
        self.screen.blit(inverted_area, (x, y))

        # Update the display
        pygame.display.flip()

        # Reset colors
        self.screen.blit(area, (x, y))