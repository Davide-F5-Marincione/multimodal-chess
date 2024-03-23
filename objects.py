import pygame
import io

import config as cfg
import utils

"""
This class is the base class for all objects in the game.
It has a parent-child relationship with other objects.
"""
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

"""
This class is the base class for all drawable objects in the game.
"""
class Drawable(Object):
    def __init__(self, drawer, x, y, parent=None):
        super().__init__(x, y, parent)

        drawer.drawables.append(self)

    def draw(self, screen):
        pass

"""
This class is the base class for all clickable objects in the game.
"""
class Clickable(Drawable):
    def __init__(self, drawer, x, y, parent, clicker, rect):
        super().__init__(drawer, x, y, parent)
        self.rect = rect
        self.is_highlighted = False

        clicker.clickables.append(self)

    def enable_highlight(self):
        self.is_highlighted = True

    def disable_highlight(self):
        self.is_highlighted = False

    def click(self):
        pass



NOTATION = dict(
    pawn = "",
    knight = "N",
    bishop = "B",
    rook = "R",
    queen = "Q",
    king = "K"
)

PIECE_IMAGES = {side + name: pygame.image.load(io.BytesIO(utils.make_svg_piece(side + name, cfg.SQUARE_SIZE).encode())) for side in "bw" for name in NOTATION.values()}
BOARD_IMAGE = pygame.image.load(io.BytesIO(utils.make_svg_board(cfg.SQUARE_SIZE).encode()))

SQUARE_SURFACE = pygame.Surface((cfg.SQUARE_SIZE, cfg.SQUARE_SIZE))
SQUARE_SURFACE.set_alpha(cfg.SQUARES_ALPHA)

"""
This class represents a square on the board.
"""
class Square(Clickable):
    def __init__(self, drawer, x, y, board_parent, clicker, rank, file, curr_piece=""):
        super().__init__(drawer, x, y, board_parent, clicker, (cfg.SQUARE_SIZE, cfg.SQUARE_SIZE))
        self.draw_state = None

        self.rank = rank
        self.file = file
        self.curr_piece = curr_piece

    def draw(self, screen):
        if self.is_highlighted:
            SQUARE_SURFACE.fill(cfg.colors["highlight"])
            screen.blit(SQUARE_SURFACE, (self.abs_x, self.abs_y))

        match self.draw_state:
            case "selected":
                SQUARE_SURFACE.fill(cfg.colors["selected"])
                screen.blit(SQUARE_SURFACE, (self.abs_x, self.abs_y))
            case "moveable":
                SQUARE_SURFACE.fill(cfg.colors["moveable"])
                screen.blit(SQUARE_SURFACE, (self.abs_x, self.abs_y))
            case "danger":
                SQUARE_SURFACE.fill(cfg.colors["danger"])
                screen.blit(SQUARE_SURFACE, (self.abs_x, self.abs_y))
        
        if len(self.curr_piece) > 0:
            screen.blit(PIECE_IMAGES[self.curr_piece], (self.abs_x, self.abs_y))

    def click(self):
        self.parent._square_clicked(self.rank, self.file)


"""
This class represents the board.
"""
class Board(Drawable):
    def __init__(self, drawer, clicker, x, y):
        super().__init__(drawer, x, y)

        self.currently_selected = None

        self.squares = []
        for rank in range(8):
            for file in range(8):
                self.squares.append(Square(drawer, file*cfg.SQUARE_SIZE, (7 - rank)*cfg.SQUARE_SIZE, self, clicker, 7-rank, file))

        self.squares[11].curr_piece = "w" + NOTATION["pawn"]

    def draw(self, screen):
        screen.blit(BOARD_IMAGE, (self.abs_x, self.abs_y))

    def get_square(self, rank, file):
        return self.squares[(7-rank)*8 + file]

    def _square_clicked(self, rank, file):
        square = self.get_square(rank, file)

        if square == self.currently_selected:
            self._deselect_square()
            return
        
        if self.currently_selected:
            self._move_piece(rank, file)
        else:
            self._select_square(rank, file)

    def _select_square(self, rank, file):
        square = self.get_square(rank, file)
        if square.curr_piece == "":
            return
        square.draw_state = "selected"
        self.currently_selected = square

    def _deselect_square(self):
        self.currently_selected.draw_state = None
        self.currently_selected = None

    def _move_piece(self, rank, file):
        from_square = self.currently_selected
        to_square = self.get_square(rank, file)

        to_square.curr_piece = from_square.curr_piece
        from_square.curr_piece = ""

        self._deselect_square()


"""
This class represents a drawer that draws objects on the screen.
"""
class Drawer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        self.screen.fill(cfg.colors["background"])

        self.drawables = []

        self.cursor_mask = utils.plus_cursor_mask(cfg.cursor["size"], cfg.cursor["bottom"], cfg.cursor["top"])[:, :, None]

    def step(self, x, y):
        for drawable in self.drawables:
            drawable.draw(self.screen)

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

"""
This class is responsible for colliding clicks to objects.
"""
class Clicker:
    def __init__(self):
        self.clickables = []
        self.curr_clickable = []

    def highlight(self, x, y):
        # Should be done with a quadtree (?)
        self.curr_clickable.clear()
        for clickable in self.clickables:
            a,b,c,d = clickable.abs_x, clickable.abs_y, clickable.abs_x + clickable.rect[0], clickable.abs_y + clickable.rect[1]

            if a <= x <= c and b <= y <= d:
                clickable.enable_highlight()
                self.curr_clickable.append(clickable)
            else:
                clickable.disable_highlight()

    def find_clicked(self):
        for clickable in self.curr_clickable:
            clickable.click()