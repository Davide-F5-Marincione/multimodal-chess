import pygame
import chess.engine

import utils
import objects
import config as cfg


# Initialize Pygame
pygame.init()

# Set up some constants
WIDTH, HEIGHT = 800, 800

# Create the screen
renderer = objects.Renderer(objects.Point(WIDTH, HEIGHT))
clicker = objects.Clicker(renderer)

objects.load_consts()

engine = chess.engine.SimpleEngine.popen_uci(".\stockfish\stockfish-windows-x86-64-avx2.exe")
engine.configure({
    "Skill Level": 20
})

board = objects.Board(renderer, clicker, objects.Point(10, 10))
context_text = objects.FloatingText(renderer, objects.Point(10, 700), "Press \'R\' to restart", 16, cfg.colors["boardtext"])

# Main loop
pygame.mouse.set_visible(False)
running = True
game_ended = False
engine_move = None

while running:
    mouse_pos = objects.Point(*pygame.mouse.get_pos())         
    clicker.highlight(mouse_pos)
    for event in pygame.event.get():
        match event.type:
            case pygame.QUIT:
                running = False
            case pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicker.execute_click()
            case pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    clicker.execute_click(False)
            case pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    clicker.cursor.release()
                    board.reset()
                    context_text.set_text("Press \'R\' to restart", cfg.colors["boardtext"])
                    game_ended = False
            case utils.TURN_DONE:
                if not game_ended:
                    if board.board.turn == chess.BLACK:
                        engine_move = engine.play(board.board, chess.engine.Limit(time=cfg.AI_THINK_TIME))
                        engine_move = engine_move.move
                        board.square_clicked(engine_move.from_square, chess.BLACK)
                        pygame.time.set_timer(pygame.event.Event(utils.ELAPSED_AI_MOVING_TIME), cfg.AI_MOVING_TIME, loops=1)
            case utils.ELAPSED_AI_MOVING_TIME:
                if not game_ended:
                    board.square_clicked(engine_move.to_square, chess.BLACK, engine_move.promotion)
                    engine_move = None
            case utils.GAME_ENDED:
                game_ended = True
                context_text.set_text("Game ended! Press \'R\' to restart", cfg.colors["redtext"])
                
    renderer.step(mouse_pos)

engine.close()

# Quit Pygame
pygame.quit()