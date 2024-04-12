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
renderer = objects.Renderer((WIDTH, HEIGHT))
clicker = objects.Clicker()

objects.load_consts()

engine = chess.engine.SimpleEngine.popen_uci(".\stockfish\stockfish-windows-x86-64-avx2.exe")
engine.configure({
    "Skill Level": 1
})

board = objects.Board(renderer, clicker, (10, 10))
objects.FloatingText(renderer, (10, 700), "Press \'R\' to restart", 16, cfg.colors["boardtext"])

# Main loop
pygame.mouse.set_visible(False)
running = True
engine_move = None
elapsed_time = 0

while running:

    mouse_pos = pygame.mouse.get_pos()         
    clicker.highlight(mouse_pos)
    for event in pygame.event.get():
        match event.type:
            case pygame.QUIT:
                running = False
            case pygame.MOUSEBUTTONDOWN:
                clicker.execute_click()
            case pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    board.reset()
            case utils.TURN_DONE:
                if board.board.turn == chess.BLACK:
                    engine_move = engine.play(board.board, chess.engine.Limit(time=cfg.AI_THINK_TIME))
                    engine_move = engine_move.move
                    board.square_clicked(engine_move.from_square, chess.BLACK)
                    pygame.time.set_timer(pygame.event.Event(utils.ELAPSED_AI_MOVING_TIME), cfg.AI_MOVING_TIME, loops=1)
            case utils.ELAPSED_AI_MOVING_TIME:
                board.square_clicked(engine_move.to_square, chess.BLACK, engine_move.promotion)
                engine_move = None
                elapsed_time = 0


    renderer.step(mouse_pos)

engine.close()

# Quit Pygame
pygame.quit()