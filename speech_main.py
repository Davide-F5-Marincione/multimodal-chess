import pygame
import chess.engine
from timeit import default_timer as timer

import utils
import objects
import config as cfg
import gesture_code
import speech_manager as sm 
import audio

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
    "Skill Level": 1
})

board = objects.Board(renderer, clicker, objects.Point(10, 10))
context_text = objects.FloatingText(renderer, objects.Point(10, 700), "Press \'R\' to restart", 16, cfg.colors["boardtext"])
hand_detector = gesture_code.HandDetector(h_flip=True,scales=[[.25, .25], [.75, .75]])
speech_manager =  sm.SpeechManager(board)     # Speech Manger references Board 


# Main loop
pygame.mouse.set_visible(False)
running = True
game_ended = False
engine_move = None
cursor_pos = objects.Point(0, 0)
mouse_pos = objects.Point(0, 0)
mouse_timestamp = -1000
last_interaction = -1000

hand_detector.start()
speech_manager.start()


while running:
    # Handling Mouse and Hand -> Registering Click and Hand Movements 
    curr_time = int(timer() * 1000)     # Current Time 
    new_mouse_pos = objects.Point(*pygame.mouse.get_pos())
    if new_mouse_pos != mouse_pos:
        mouse_pos = new_mouse_pos
        mouse_timestamp = curr_time
    hand_cursor_pos, hand_click, hand_release, hand_timestamp = hand_detector.process_gestures(curr_time)

    if mouse_timestamp >= hand_timestamp:
        cursor_pos = mouse_pos
    else:
        cursor_pos = objects.Point(int(hand_cursor_pos[0] * WIDTH), int(hand_cursor_pos[1] * HEIGHT))
        if hand_click:
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1))
        if hand_release:
            pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1))
    
    clicker.highlight(cursor_pos)
    
    # Execution of Click 
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
    
    if clicker.cursor.holding is None and board.board.turn == chess.WHITE:
        command, some_command = speech_manager.resolve_commands(curr_time)
        # Execute command 
        if command:
            src, tgt, prm = command
            if src is not None: # if src is not None, then it's a move/capture/castle (/w promotion maybe)
                board.deselect_square() # to disable previously clicked squares.

                # simulate clicks on the board
                board.square_clicked(src, chess.WHITE)
                board.square_clicked(tgt, chess.WHITE, prm)
            elif board.promotion.is_visible: # if src is None, then it can only be a pure promotion.
                # simulate promotion click
                board.square_clicked(board.promotion.square_code, chess.WHITE, prm)
            else:
                audio.ILLEGAL_MOVE_SOUND.set_volume(cfg.ILLEGAL_MOVE_VOLUME)
                audio.ILLEGAL_MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0)
        elif some_command:
            audio.ILLEGAL_MOVE_SOUND.set_volume(cfg.ILLEGAL_MOVE_VOLUME)
            audio.ILLEGAL_MOVE_SOUND.play(loops=0, maxtime=0, fade_ms=0)
    
    renderer.step(cursor_pos)

engine.close()
speech_manager.stop()

# Quit Pygame
pygame.quit()