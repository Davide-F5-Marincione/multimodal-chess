from typing import *
import random
import pygame
import chess
import io

import config as cfg
import audio
import utils


"""
This class is the base class for all objects in the game.
It has a parent-child relationship with other objects.
"""
class Object:
    def __init__(self, rel_pos: Tuple[int, int], parent:Self=None):
        self.parent = parent
        if parent:
            self.parent.children.append(self)
        self.children = []

        self.set_rel_pos(rel_pos)

    def set_rel_pos(self, rel_pos: Tuple[int, int]):
        self.rel_pos = rel_pos
        
        if self.parent:
            rel_pos = self.parent.get_abs_pos()
            self.abs_pos = rel_pos[0] + self.rel_pos[0], rel_pos[1] + self.rel_pos[1]
        else:
            self.abs_pos = self.rel_pos

        for child in self.children:
            child.set_rel_pos(child.get_rel_pos())
    
    def get_rel_pos(self):
        return self.rel_pos
    
    def get_abs_pos(self):
        return self.abs_pos

"""
This class represents a renderer that draws objects on the screen.
"""
class Renderer:
    def __init__(self, size: Tuple[int, int]):
        self.size = size
        self.screen = pygame.display.set_mode(size)
        self.screen.fill(cfg.colors["background"])

        self.renderables = []

        self.cursor_mask = utils.plus_cursor_mask(cfg.cursor["size"], cfg.cursor["bottom"], cfg.cursor["top"])[:, :, None]

    def step(self, cursor_pos: Tuple[int, int]):
        for renderable in self.renderables:
            renderable.draw(self.screen)

        cursor_pos = cursor_pos[0] - cfg.cursor["offset"], cursor_pos[1] - cfg.cursor["offset"]

        # Capture the area under the cursor
        area = pygame.Surface((cfg.cursor["size"], cfg.cursor["size"]))
        area.blit(self.screen, (0, 0), (*cursor_pos, cfg.cursor["size"], cfg.cursor["size"]))

        # Convert the surface to a numpy array and make the colors contrasting
        inverted_pixels = self.cursor_mask + pygame.surfarray.array3d(area)

        # Convert the inverted array back to a surface and blit it to the screen
        inverted_area = pygame.surfarray.make_surface(inverted_pixels)
        self.screen.blit(inverted_area, cursor_pos)

        # Update the display
        pygame.display.flip()

        # Reset colors
        self.screen.blit(area, cursor_pos)


"""
This class is the base class for all renderable objects in the game.
"""
class Renderable(Object):
    def __init__(self, renderer: Renderer, rel_pos: Tuple[int, int], parent: Object=None):
        super().__init__(rel_pos, parent)

        self.surface = None
        renderer.renderables.append(self)

    def draw(self, screen: pygame.Surface):
        screen.blit(self.surface, self.abs_pos)


"""
This class is responsible for colliding clicks to objects.
"""
class Clicker:
    def __init__(self):
        self.clickables = []
        self.curr_clickable = (-1, None)    #priority, object 

    def highlight(self, cursor_pos: Tuple[int, int]):
        # Should be done with a quadtree (?) Naaaaah, it's O(n)
        self.curr_clickable = (-1, None)
        for clickable in self.clickables:
            left, top = clickable.abs_pos[0], clickable.abs_pos[1]
            right, bottom = left + clickable.rect[0], top + clickable.rect[1]

            if left <= cursor_pos[0] <= right and top <= cursor_pos[1] <= bottom and self.curr_clickable[0] <= clickable.priority:
                    clickable.enable_highlight()
                    self.curr_clickable = (clickable.priority, clickable)
            else:
                clickable.disable_highlight()

    def execute_click(self):
        if self.curr_clickable[1]:
            self.curr_clickable[1].click()

"""
This class is the base class for all clickable objects in the game.
"""
class Clickable(Renderable):
    def __init__(self, renderer: Renderer, clicker: Clicker, rel_pos: Tuple[int, int], rect: Tuple[int, int], priority=0, parent: Object=None):
        super().__init__(renderer, rel_pos, parent)
        self.rect = rect
        self.is_highlighted = False
        self.priority = priority

        clicker.clickables.append(self)

    def enable_highlight(self):
        self.is_highlighted = True

    def disable_highlight(self):
        self.is_highlighted = False

    def click(self):
        pass


NOTATION = dict(
    pawn = "P",
    knight = "N",
    bishop = "B",
    rook = "R",
    queen = "Q",
    king = "K"
)

PIECE_IMAGES = [None] + [pygame.image.load(io.BytesIO(utils.make_svg_piece(side + name, cfg.SQUARE_SIZE).encode())) for side in "bw" for name in NOTATION.values()]
BOARD_IMAGE = pygame.image.load(io.BytesIO(utils.make_svg_board(cfg.SQUARE_SIZE).encode()))
PROMOTION_BUBBLE_IMAGE = pygame.image.load(io.BytesIO(utils.make_svg_promotion(cfg.SQUARE_SIZE).encode()))

SQUARE_SURFACE = pygame.Surface((cfg.SQUARE_SIZE, cfg.SQUARE_SIZE))
SQUARE_SURFACE.set_alpha(cfg.SQUARES_ALPHA)

pygame.font.init()

"""
This class represents the board.
"""
class Board(Renderable):
    def __init__(self, renderer: Renderer, clicker: Clicker, rel_pos: Tuple[int, int], starting_fen: str=None):
        super().__init__(renderer, rel_pos)

        self.currently_selected = None

        self.gui_squares = [None] * 64
        for file in range(8):
            for rank in range(8):
                square_code = chess.square(file, (7-rank))
                self.gui_squares[square_code] = GUISquare(renderer, clicker, (file*cfg.SQUARE_SIZE, rank*cfg.SQUARE_SIZE), self, square_code, piece_code=0)

        if starting_fen:
            self.board = chess.Board(starting_fen)
        else:
            self.board = chess.Board()

        # self.promotion = PromotionBubble(renderer, (0, 0), self) # No need for this rn

        self.update_board()

        # Create board surface
        self.surface = pygame.Surface(size=(cfg.SQUARE_SIZE * 9, cfg.SQUARE_SIZE * 9))
        self.surface.fill(cfg.colors["background"])
        self.surface.blit(BOARD_IMAGE, (0, 0))
        
        # Add rank and file labels
        font = pygame.font.Font(cfg.BOARD_TEXT_FONT, cfg.BOARD_TEXT_SIZE)
        for i in range(8):
            size = font.size("87654321"[i])
            text = font.render("87654321"[i], cfg.TEXT_ANTIALIAS, cfg.colors["boardtext"], cfg.colors["background"])
            self.surface.blit(text, (cfg.SQUARE_SIZE * 8 + cfg.BOARD_TEXT_DISTANCE, int(cfg.SQUARE_SIZE * (i + .5)) - size[1]//2))

            size = font.size("abcdefgh"[i])
            text = font.render("abcdefgh"[i], cfg.TEXT_ANTIALIAS, cfg.colors["boardtext"], cfg.colors["background"])
            self.surface.blit(text, (int(cfg.SQUARE_SIZE * (i + .5)) - size[0]//2, cfg.SQUARE_SIZE * 8 + cfg.BOARD_TEXT_DISTANCE))


    def update_board(self):
        for square in self.gui_squares:
            if piece := self.board.piece_at(square.square_code):
                square.piece_code = piece.color * 6 + piece.piece_type
            else:
                square.piece_code = 0

        if self.board.is_check():
            self.get_square(self.board.king(self.board.turn)).draw_state = "danger"

    def get_square(self, square_code: int):
        return self.gui_squares[square_code]

    def square_clicked(self, square_code: int):
        if self.currently_selected:
            is_legal = any(move.from_square == self.currently_selected and move.to_square == square_code
                           for move in self.board.legal_moves)

            if is_legal:
                self.move_piece(square_code)
            else:
                if self.currently_selected != square_code:
                    audio.ILLEGAL_MOVE_SOUND.set_volume(cfg.ILLEGAL_MOVE_VOLUME)
                    audio.ILLEGAL_MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0)
                self.deselect_square()
        else:
            self.select_square(square_code)

    def select_square(self, square_code: int):
        gui_square = self.get_square(square_code)
        if gui_square.piece_code == 0 or (gui_square.piece_code > 6) != self.board.turn:
            return
        gui_square.draw_state = "selected"
        self.currently_selected = square_code

        for move in self.board.legal_moves:
            if move.from_square == square_code:
                self.get_square(move.to_square).draw_state = "moveable"

                # Castling highlight
                if self.board.piece_at(square_code).piece_type == chess.KING:
                    match move.to_square:
                        case chess.G1: self.get_square(chess.F1).draw_state = "moveable"
                        case chess.C1: self.get_square(chess.D1).draw_state = "moveable"
                        case chess.G8: self.get_square(chess.F8).draw_state = "moveable"
                        case chess.C8: self.get_square(chess.D8).draw_state = "moveable"

    def deselect_square(self):
        for square in self.gui_squares:
            square.draw_state = None

        # Check if the king is in check
        if self.board.is_check():
            self.get_square(self.board.king(self.board.turn)).draw_state = "danger"

        self.currently_selected = None

    def move_piece(self, square_code: int):
        if self.board.piece_at(self.currently_selected).piece_type == chess.PAWN and (chess.square_rank(square_code) == 0 or chess.square_rank(square_code) == 7):
            # Add a way to choose the promotion piece
            self.board.push(chess.Move(self.currently_selected, square_code, promotion=chess.QUEEN))
        else:
            self.board.push(chess.Move(self.currently_selected, square_code))


        if self.board.is_check():
            audio.CHECK_SOUND.set_volume(cfg.KING_CHECK_VOLUME)
            audio.CHECK_SOUND.play(loops=0, maxtime=0, fade_ms=0)
        else:
            # sound = random.sample(audio.MOVE_SOUNDS, 1)[0]
            audio.MOVE_SOUND.set_volume(cfg.MOVE_VOLUME)
            audio.MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0)

        self.deselect_square()
        self.update_board()


"""
This class represents a square on the board.
"""
class GUISquare(Clickable):
    def __init__(self, renderer: Renderer, clicker: Clicker, rel_pos: Tuple[int, int], board_parent: Board, square_code: int, piece_code: int=0):
        super().__init__(renderer, clicker, rel_pos, (cfg.SQUARE_SIZE, cfg.SQUARE_SIZE), cfg.SQUARE_CLICK_PRIORITY, board_parent)
        self.draw_state = None

        self.square_code = square_code
        self.piece_code = piece_code

    def draw(self, screen: pygame.Surface):
        if self.is_highlighted:
            SQUARE_SURFACE.fill(cfg.colors["highlight"])
            screen.blit(SQUARE_SURFACE, self.abs_pos)

        if self.draw_state:
            SQUARE_SURFACE.fill(cfg.colors[self.draw_state])
            screen.blit(SQUARE_SURFACE, self.abs_pos)
        
        if self.piece_code != 0:
            screen.blit(PIECE_IMAGES[self.piece_code], self.abs_pos)

    def click(self):
        self.parent.square_clicked(self.square_code)


# Class to test that the promotion bubble i did is of correct size, <3
# class PromotionBubble(Renderable):
#     def __init__(self, renderer: Renderer, rel_pos: Tuple[int, int], parent: Object = None):
#         super().__init__(renderer, rel_pos, parent)
#         self.surface = PROMOTION_BUBBLE_IMAGE