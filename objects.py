from typing import *
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
    def __init__(self, rel_pos: Tuple[int, int], parent=None):
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
            if renderable.is_visible:
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
        self.is_visible = True
        renderer.renderables.append(self)

    def draw(self, screen: pygame.Surface):
        screen.blit(self.surface, self.abs_pos)
    
    def set_visible(self):
        self.is_visible = True
        for child in self.children:
            child.set_visible() 
    
    def set_invisible(self):
        self.is_visible = False
        for child in self.children:
            child.set_invisible()
    
    

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
            if not clickable.is_visible:
                continue
            left, top = clickable.abs_pos[0], clickable.abs_pos[1]
            right, bottom = left + clickable.rect[0], top + clickable.rect[1]

            if left < cursor_pos[0] <= right and top < cursor_pos[1] <= bottom and self.curr_clickable[0] <= clickable.priority:
                self.curr_clickable = (clickable.priority, clickable)
            
            clickable.disable_highlight()

        if self.curr_clickable[1]:
            self.curr_clickable[1].enable_highlight()

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

PIECE_IMAGES = None
BOARD_IMAGE = None
PROMOTION_BUBBLE_IMAGE = None

SQUARE_SURFACE = None

def load_consts():
    global PIECE_IMAGES, BOARD_IMAGE, PROMOTION_BUBBLE_IMAGE, SQUARE_SURFACE
    PIECE_IMAGES = [None] + [pygame.image.load(io.BytesIO(utils.make_svg_piece(side + name, cfg.SQUARE_SIZE).encode())).convert_alpha() for side in "bw" for name in NOTATION.values()]
    BOARD_IMAGE = pygame.image.load(io.BytesIO(utils.make_svg_board(cfg.SQUARE_SIZE).encode())).convert()
    PROMOTION_BUBBLE_IMAGE = pygame.image.load(io.BytesIO(utils.make_svg_promotion(cfg.SQUARE_SIZE).encode())).convert_alpha()
    SQUARE_SURFACE = pygame.Surface((cfg.SQUARE_SIZE, cfg.SQUARE_SIZE)).convert_alpha()
    SQUARE_SURFACE.set_alpha(cfg.SQUARES_ALPHA)

pygame.font.init()

def get_piece_code(piece_type: chess.PieceType, color: chess.Color):
    return color * 6 + piece_type

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
            
            
        # Instatiate Promotion Bubble 
        self.promotion = PromotionBubble(renderer, clicker, (0, 0), self)
        self.promotion.set_invisible()

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
            self.surface.blit(text, (cfg.SQUARE_SIZE * 8 + cfg.BOARD_TEXT_H_DISTANCE, int(cfg.SQUARE_SIZE * (i + .5)) - size[1]//2))

            size = font.size("abcdefgh"[i])
            text = font.render("abcdefgh"[i], cfg.TEXT_ANTIALIAS, cfg.colors["boardtext"], cfg.colors["background"])
            self.surface.blit(text, (int(cfg.SQUARE_SIZE * (i + .5)) - size[0]//2, cfg.SQUARE_SIZE * 8 + cfg.BOARD_TEXT_V_DISTANCE))


    def update_board(self):
        for square in self.gui_squares:
            if piece := self.board.piece_at(square.square_code):
                square.piece_code = get_piece_code(piece.piece_type, piece.color)
            else:
                square.piece_code = 0

        if self.board.is_check():
            self.get_square(self.board.king(self.board.turn)).draw_state = "danger"

    def get_square(self, square_code: int):
        return self.gui_squares[square_code]

    def square_clicked(self, square_code: int, clicking_color: bool = chess.WHITE, promotion: int = None):
        if clicking_color != self.board.turn:
            return

        if self.currently_selected is None:
            self.select_square(square_code)
        else:
            is_legal = any(move.from_square == self.currently_selected and move.to_square == square_code
                           for move in self.board.legal_moves)

            if is_legal:
                if self.board.piece_at(self.currently_selected).piece_type == chess.PAWN and (chess.square_rank(square_code) == 0 or chess.square_rank(square_code) == 7):
                    if promotion is None:
                        # Show promotion bubble
                        self.promotion.setup(square_code, clicking_color)
                    else:
                        self.move_piece(square_code, promotion)
                else: 
                    self.move_piece(square_code)
            else:                    
                if self.currently_selected != square_code:
                    self.deselect_square()
                    if self.board.color_at(square_code) == clicking_color:
                        self.select_square(square_code)
                    else:
                        audio.ILLEGAL_MOVE_SOUND.set_volume(cfg.ILLEGAL_MOVE_VOLUME)
                        audio.ILLEGAL_MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0)
                else:
                    self.deselect_square()

    def select_square(self, square_code: int):
        self.promotion.set_invisible()

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
        self.promotion.set_invisible()

        for square in self.gui_squares:
            square.draw_state = None

        # Check if the king is in check
        if self.board.is_check():
            self.get_square(self.board.king(self.board.turn)).draw_state = "danger"

        self.currently_selected = None

    def move_piece(self, square_code: int, promotion : int = None):
        
        self.board.push(chess.Move(self.currently_selected, square_code, promotion))

        if self.board.is_check():
            audio.CHECK_SOUND.set_volume(cfg.KING_CHECK_VOLUME)
            audio.CHECK_SOUND.play(loops=0, maxtime=0, fade_ms=0)
        else:
            # sound = random.sample(audio.MOVE_SOUNDS, 1)[0]
            audio.MOVE_SOUND.set_volume(cfg.MOVE_VOLUME)
            audio.MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0)

        self.deselect_square()
        self.update_board()

        pygame.event.post(pygame.event.Event(utils.TURN_DONE))


    def reset(self):
        self.deselect_square()
        self.board.reset()
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
        self.parent.square_clicked(self.square_code, chess.WHITE)


class RestartButton(Clickable):
    def __init__(self, renderer: Renderer, clicker: Clicker, rel_pos: Tuple[int, int], board: Board, border_dist=(10, 4)):
        font = pygame.font.Font(cfg.BOARD_TEXT_FONT, cfg.RESTART_BUTTON_TEXT_SIZE)
        size = font.size("restart")
        size = size[0] + border_dist[0]*2, size[1] + border_dist[1]*2

        super().__init__(renderer, clicker, rel_pos, size, cfg.SQUARE_CLICK_PRIORITY)
        self.board = board

        self.surface = pygame.image.load(io.BytesIO(utils.make_svg_restart(size=size, stroke_width=cfg.RESTART_BUTTON_STROKE_WIDTH).encode())).convert_alpha()

        text = font.render("restart", cfg.TEXT_ANTIALIAS, cfg.colors["restart_button"], cfg.colors["background"])
        self.surface.blit(text, border_dist)

    def click(self):
        self.board.reset()

class FloatingText(Renderable):
    def __init__(self, renderer: Renderer, rel_pos: Tuple[int, int], text: str, font_size: int, color: Tuple[int, int, int], font: str = cfg.BOARD_TEXT_FONT, parent: Object=None):
        super().__init__(renderer, rel_pos, parent)

        font = pygame.font.Font(font, font_size)
        self.surface = font.render(text, cfg.TEXT_ANTIALIAS, color, cfg.colors["background"])


# Class to test that the promotion bubble i did is of correct size, <3, gne 
class PromotionBubble(Renderable):
    def __init__(self, renderer: Renderer, clicker: Clicker, rel_pos: Tuple[int, int], board_parent: Board):
        super().__init__(renderer, rel_pos, board_parent)
        self.surface = PROMOTION_BUBBLE_IMAGE 
        self.mirror = False
        self.square_code = None
        self.color = None
        
        self.kb = PromotionButton(renderer, clicker, (0,0), self, chess.KNIGHT)
        self.bb = PromotionButton(renderer, clicker, (0,0), self, chess.BISHOP)
        self.rb = PromotionButton(renderer, clicker, (0,0), self, chess.ROOK)
        self.qb = PromotionButton(renderer, clicker, (0,0), self, chess.QUEEN)

    def setup(self, square_code: int, color: chess.Color):
        self.square_code = square_code
        self.color = color

        self.mirror = (square_code % 8) > 3

        # some magic numbers to make the buttons flush with the bubble
        if self.mirror:
            self.kb.set_rel_pos((cfg.SQUARE_SIZE*0.08,cfg.SQUARE_SIZE*1.29))
            self.bb.set_rel_pos((cfg.SQUARE_SIZE*1.08,cfg.SQUARE_SIZE*1.29))
            self.rb.set_rel_pos((cfg.SQUARE_SIZE*2.08,cfg.SQUARE_SIZE*1.29))
            self.qb.set_rel_pos((cfg.SQUARE_SIZE*3.08,cfg.SQUARE_SIZE*1.29))
            self.set_rel_pos(((square_code % 8 - 3.5)* cfg.SQUARE_SIZE, (7 - square_code // 8) * cfg.SQUARE_SIZE))
        else:
            self.kb.set_rel_pos((cfg.SQUARE_SIZE*0.43,cfg.SQUARE_SIZE*1.29))
            self.bb.set_rel_pos((cfg.SQUARE_SIZE*1.43,cfg.SQUARE_SIZE*1.29))
            self.rb.set_rel_pos((cfg.SQUARE_SIZE*2.43,cfg.SQUARE_SIZE*1.29))
            self.qb.set_rel_pos((cfg.SQUARE_SIZE*3.43,cfg.SQUARE_SIZE*1.29))
            self.set_rel_pos((square_code % 8 * cfg.SQUARE_SIZE, (7 - square_code // 8) * cfg.SQUARE_SIZE))

        self.set_visible()  
    
    def draw(self,screen: pygame.Surface):
        if self.mirror:
            screen.blit(pygame.transform.flip(self.surface, True, False), self.abs_pos)
        else:
            screen.blit(self.surface, self.abs_pos) 
    
    def promotion_clicked(self, piece_code: int, color: chess.Color):
        self.parent.square_clicked(self.square_code, color, piece_code)
        
        

class PromotionButton(Clickable):
    def __init__(self, renderer: Renderer, clicker: Clicker, rel_pos: Tuple[int, int], bubble_parent: PromotionBubble, piece_code: int=0):
        super().__init__(renderer, clicker, rel_pos, (cfg.SQUARE_SIZE, cfg.SQUARE_SIZE), cfg.PROMOTION_CLICK_PRIORITY, bubble_parent)

        self.piece_code = piece_code

    def draw(self, screen: pygame.Surface):
        if self.is_highlighted:
            SQUARE_SURFACE.fill(cfg.colors["promotion_highlight"])
            screen.blit(SQUARE_SURFACE, self.abs_pos)
        
        if self.piece_code != 0:
            screen.blit(PIECE_IMAGES[get_piece_code(self.piece_code, self.parent.color)], self.abs_pos)

    def click(self):
        self.parent.promotion_clicked(self.piece_code, chess.WHITE)