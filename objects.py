from typing import *
import pygame
import bisect
import chess
import io

import config as cfg
import audio
import utils


class Point(NamedTuple):
    x: int
    y: int


"""
This class is the base class for all objects in the game.
It has a parent-child relationship with other objects.
"""
class Object:
    def __init__(self, rel_pos: Point, parent=None):
        Object.COUNTER += 1
        self.id = Object.COUNTER

        self.parent = parent
        if parent:
            self.parent.children.append(self)
        self.children = []

        self.set_rel_pos(rel_pos)

    def set_rel_pos(self, rel_pos: Point):
        self.rel_pos = rel_pos
        
        if self.parent:
            rel_pos = self.parent.get_abs_pos()
            self.abs_pos = Point(rel_pos.x + self.rel_pos.x, rel_pos.y + self.rel_pos.y)
        else:
            self.abs_pos = self.rel_pos

        for child in self.children:
            child.set_rel_pos(child.get_rel_pos())
    
    def get_rel_pos(self):
        return self.rel_pos
    
    def get_abs_pos(self):
        return self.abs_pos
    
    def __eq__(self, other):
        if not isinstance(other, Object):
            return False
        return self.id == other.id
    
    def __lt__(self, other):
        if not isinstance(other, Object):
            return False
        return self.id < other.id
    
    def __gt__(self, other):
        if not isinstance(other, Object):
            return False
        return self.id > other.id
    
Object.COUNTER = 0


class RenderContext(NamedTuple):
    screen: pygame.Surface
    cursor_pos: Point


"""
This class represents a renderer that draws objects on the screen.
"""
class Renderer:
    def __init__(self, size: Point):
        self.size = size
        self.screen = pygame.display.set_mode(size)

        self.renderables = []

    def add_renderable(self, renderable):
        bisect.insort(self.renderables, (renderable.order, renderable))

    def step(self, cursor_pos: Point):
        self.screen.fill(cfg.colors["background"])
        render_context = RenderContext(self.screen, cursor_pos)

        for _, renderable in self.renderables:
            if renderable.is_visible:
                renderable.draw(render_context)

        # Update the display
        pygame.display.flip()


"""
This class is the base class for all renderable objects in the game.
"""
class Renderable(Object):
    def __init__(self, renderer: Renderer, rel_pos: Point, parent: Object=None, order=0):
        super().__init__(rel_pos, parent)

        self.surface = None
        self.is_visible = True
        self.order = order
        renderer.add_renderable(self)

    def draw(self, context: RenderContext):
        context.screen.blit(self.surface, self.abs_pos)
    
    def set_visible(self):
        self.is_visible = True
        for child in self.children:
            child.set_visible() 
    
    def set_invisible(self):
        self.is_visible = False
        for child in self.children:
            child.set_invisible()

class Cursor(Renderable):
    def __init__(self, renderer: Renderer):
        super().__init__(renderer, Point(0,0), order=cfg.CURSOR_ORDER)

        self.surface = pygame.Surface((cfg.cursor["size"], cfg.cursor["size"]))
        self.mask = utils.plus_cursor_mask(cfg.cursor["size"], cfg.cursor["bottom"], cfg.cursor["top"])[:, :, None]

        self.holding = None

        # CursorShadow(renderer, self)

    def draw(self, context: RenderContext):
        if self.holding:
            self.holding.hold_draw(context)

        self.set_rel_pos(Point(context.cursor_pos.x - cfg.cursor["offset"], context.cursor_pos.y - cfg.cursor["offset"]))

        self.surface.blit(context.screen, (0, 0), (*self.abs_pos, cfg.cursor["size"], cfg.cursor["size"]))
        context.screen.blit(pygame.surfarray.make_surface(self.mask + pygame.surfarray.array3d(self.surface)), self.abs_pos)

    def release(self):
        if self.holding:
            self.holding.held = False
        self.holding = None


# class CursorShadow(Renderable):
#     def __init__(self, renderer: Renderer, parent: Cursor):
#         super().__init__(renderer, Point(0,0), parent, order=cfg.CURSOR_SHADOW_ORDER)

#     def draw(self, context: RenderContext):
#         context.screen.blit(self.parent.surface, self.abs_pos)
    

"""
This class is responsible for colliding clicks to objects.
"""
class Clicker:
    def __init__(self, renderer: Renderer):
        self.clickables = []
        self.curr_clickable = None
        self.cursor = Cursor(renderer)

    def add_clickable(self, clickable):
        bisect.insort(self.clickables, (clickable.order, clickable))

    def highlight(self, cursor_pos: Point):
        # Should be done with a quadtree (?) Naaaaah, it's O(n)
        found = None
        for _, clickable in self.clickables[::-1]:
            if not clickable.is_visible:
                continue
            left, top = clickable.abs_pos.x, clickable.abs_pos.y
            right, bottom = left + clickable.rect.x, top + clickable.rect.y

            if left < cursor_pos.x <= right and top < cursor_pos.y <= bottom:
                found = clickable
                break
        
        if not found is None:
            if found != self.curr_clickable:
                if self.curr_clickable:
                    self.curr_clickable.disable_highlight()
                self.curr_clickable = found
                self.curr_clickable.enable_highlight()
        else:
            if self.curr_clickable:
                self.curr_clickable.disable_highlight()
                self.curr_clickable = None

    def execute_click(self, is_button_down=True):
        if not is_button_down:
            self.cursor.release()

        if self.curr_clickable:
            if is_button_down:
                self.curr_clickable.click(self.cursor)
            else:
                self.curr_clickable.declick()


"""
This class is the base class for all clickable objects in the game.
"""
class Clickable(Renderable):
    def __init__(self, renderer: Renderer, clicker: Clicker, rel_pos: Point, rect: Point, order=0, parent: Object=None):
        super().__init__(renderer, rel_pos, parent, order)
        self.rect = rect
        self.is_highlighted = False

        clicker.add_clickable(self)

    def enable_highlight(self):
        self.is_highlighted = True

    def disable_highlight(self):
        self.is_highlighted = False

    def click(self, cursor: Cursor):
        pass

    def declick(self):
        pass

    def hold_draw(self, context: RenderContext):
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
    def __init__(self, renderer: Renderer, clicker: Clicker, rel_pos: Point, starting_fen: str=None):
        super().__init__(renderer, rel_pos, order=cfg.BOARD_ORDER)
        
        self.currently_selected = None

        self.gui_squares = [None] * 64
        for file in range(8):
            for rank in range(8):
                square_code = chess.square(file, (7-rank))
                self.gui_squares[square_code] = GUISquare(renderer, clicker, Point(file*cfg.SQUARE_SIZE, rank*cfg.SQUARE_SIZE), self, square_code, piece_code=0)

        if starting_fen:
            self.board = chess.Board(starting_fen)
        else:
            self.board = chess.Board()
            
            
        # Instatiate Promotion Bubble 
        self.promotion = PromotionBubble(renderer, clicker, Point(0, 0), self)
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

    def square_clicked(self, square_code: int, clicking_color: bool = chess.WHITE, promotion: int = None, can_select=True):
        if clicking_color != self.board.turn:
            return

        if self.currently_selected is None:
            if can_select:
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
                        if can_select:
                            self.select_square(square_code)
                    # else: # Play sound every time we do an "illegal move"... Do we really want to do this?
                    #     audio.ILLEGAL_MOVE_SOUND.set_volume(cfg.ILLEGAL_MOVE_VOLUME)
                    #     audio.ILLEGAL_MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0)
                # else: # Deselect square when we click back on it... Do we really want to do this?
                #     self.deselect_square()

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

        if self.board.is_game_over():
            pygame.event.post(pygame.event.Event(utils.GAME_ENDED))
        else:
            pygame.event.post(pygame.event.Event(utils.TURN_DONE))


    def reset(self):
        self.board.reset()

        self.deselect_square()
        self.update_board()


"""
This class represents a square on the board.
"""
class GUISquare(Clickable):
    def __init__(self, renderer: Renderer, clicker: Clicker, rel_pos: Point, board_parent: Board, square_code: int, piece_code: int=0):
        super().__init__(renderer, clicker, rel_pos, Point(cfg.SQUARE_SIZE, cfg.SQUARE_SIZE), cfg.GUISQUARE_ORDER, board_parent)
        self.draw_state = None

        self.square_code = square_code
        self.piece_code = piece_code
        self.held = False

    def draw(self, context: RenderContext):
        if self.is_highlighted:
            SQUARE_SURFACE.fill(cfg.colors["highlight"])
            context.screen.blit(SQUARE_SURFACE, self.abs_pos)

        if self.draw_state:
            SQUARE_SURFACE.fill(cfg.colors[self.draw_state])
            context.screen.blit(SQUARE_SURFACE, self.abs_pos)
        
        if self.piece_code != 0:
            if self.held:
                # Draw in place
                PIECE_IMAGES[self.piece_code].set_alpha(cfg.SQUARES_ALPHA)
                context.screen.blit(PIECE_IMAGES[self.piece_code], self.abs_pos)
                PIECE_IMAGES[self.piece_code].set_alpha(255)
            else:
                context.screen.blit(PIECE_IMAGES[self.piece_code], self.abs_pos)

    def _click(self, can_select=True):
        self.parent.square_clicked(self.square_code, chess.WHITE, can_select=can_select)

    def click(self, cursor: Cursor):
        if self.piece_code != 0:
            cursor.holding = self
            self.held = True
        self._click()

    def declick(self):
        self._click(False)

    def hold_draw(self, context: RenderContext):
        # Draw under cursor
        context.screen.blit(PIECE_IMAGES[self.piece_code], Point(context.cursor_pos.x - cfg.SQUARE_SIZE//2, context.cursor_pos.y - cfg.SQUARE_SIZE//2))


class FloatingText(Renderable):
    def __init__(self, renderer: Renderer, rel_pos: Point, text: str, font_size: int, color: Tuple[int, int, int], font: str = cfg.BOARD_TEXT_FONT, parent: Object=None, order=3):
        super().__init__(renderer, rel_pos, parent, order)

        self.font = pygame.font.Font(font, font_size)
        self.set_text(text, color)

    def set_text(self, text: str, color: Tuple[int, int, int] = None):
        if color:
            self.curr_color = color
        self.surface = self.font.render(text, cfg.TEXT_ANTIALIAS, self.curr_color, cfg.colors["background"])


# Class to test that the promotion bubble i did is of correct size, <3, gne 
class PromotionBubble(Renderable):
    def __init__(self, renderer: Renderer, clicker: Clicker, rel_pos: Point, board_parent: Board):
        super().__init__(renderer, rel_pos, board_parent, cfg.PROMOTION_BUBBLE_ORDER)
        self.surface = PROMOTION_BUBBLE_IMAGE 
        self.mirror = False
        self.square_code = None
        self.color = None
        
        self.kb = PromotionButton(renderer, clicker, Point(0,0), self, chess.KNIGHT)
        self.bb = PromotionButton(renderer, clicker, Point(0,0), self, chess.BISHOP)
        self.rb = PromotionButton(renderer, clicker, Point(0,0), self, chess.ROOK)
        self.qb = PromotionButton(renderer, clicker, Point(0,0), self, chess.QUEEN)

    def setup(self, square_code: int, color: chess.Color):
        self.square_code = square_code
        self.color = color

        self.mirror = (square_code % 8) > 3

        # some magic numbers to make the buttons flush with the bubble
        if self.mirror:
            self.kb.set_rel_pos(Point(cfg.SQUARE_SIZE*0.08,cfg.SQUARE_SIZE*1.29))
            self.bb.set_rel_pos(Point(cfg.SQUARE_SIZE*1.08,cfg.SQUARE_SIZE*1.29))
            self.rb.set_rel_pos(Point(cfg.SQUARE_SIZE*2.08,cfg.SQUARE_SIZE*1.29))
            self.qb.set_rel_pos(Point(cfg.SQUARE_SIZE*3.08,cfg.SQUARE_SIZE*1.29))
            self.set_rel_pos(Point((square_code % 8 - 3.5)* cfg.SQUARE_SIZE, (7 - square_code // 8) * cfg.SQUARE_SIZE))
        else:
            self.kb.set_rel_pos(Point(cfg.SQUARE_SIZE*0.43,cfg.SQUARE_SIZE*1.29))
            self.bb.set_rel_pos(Point(cfg.SQUARE_SIZE*1.43,cfg.SQUARE_SIZE*1.29))
            self.rb.set_rel_pos(Point(cfg.SQUARE_SIZE*2.43,cfg.SQUARE_SIZE*1.29))
            self.qb.set_rel_pos(Point(cfg.SQUARE_SIZE*3.43,cfg.SQUARE_SIZE*1.29))
            self.set_rel_pos(Point(square_code % 8 * cfg.SQUARE_SIZE, (7 - square_code // 8) * cfg.SQUARE_SIZE))

        self.set_visible()  
    
    def draw(self, context: RenderContext):
        if self.mirror:
            context.screen.blit(pygame.transform.flip(self.surface, True, False), self.abs_pos)
        else:
            context.screen.blit(self.surface, self.abs_pos) 
    
    def promotion_clicked(self, piece_code: int, color: chess.Color):
        self.parent.square_clicked(self.square_code, color, piece_code)
        

class PromotionButton(Clickable):
    def __init__(self, renderer: Renderer, clicker: Clicker, rel_pos: Point, bubble_parent: PromotionBubble, piece_code: int=0):
        super().__init__(renderer, clicker, rel_pos, Point(cfg.SQUARE_SIZE, cfg.SQUARE_SIZE), cfg.PROMOTION_SQUARE_ORDER, bubble_parent)

        self.piece_code = piece_code

    def draw(self, context: RenderContext):
        if self.is_highlighted:
            SQUARE_SURFACE.fill(cfg.colors["promotion_highlight"])
            context.screen.blit(SQUARE_SURFACE, self.abs_pos)
        
        if self.piece_code != 0:
            context.screen.blit(PIECE_IMAGES[get_piece_code(self.piece_code, self.parent.color)], self.abs_pos)

    def click(self, cursor: Cursor):
        self.parent.promotion_clicked(self.piece_code, chess.WHITE)