import pygame
import chess.engine
from timeit import default_timer as timer
from datetime import datetime

import utils
import objects
import config as cfg
import gesture_code
import speech_manager as sm 
import audio
import json
import os

os.makedirs("./recordings", exist_ok=True)

# get current datetime
recording_start = datetime.now()
actions = []
curr_action = None
ai_moves = []

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

# If starting_fen is None, then the default starting position is used
# Otherwise that starting fen setup is used,
# here are some FEN strings:
# 'Almost to promotion': "2r5/1P6/8/5pk1/1KP1q1p1/1Q6/8/8"
# 'Yesterday's lichess puzzle': "5rk1/pP2pp2/3p2p1/2pPb2p/2Q1N1q1/1R2P3/3B1PPP/6K1 b"
# 'Bongcloud opening': "r2qk2r/ppp1bppp/2n1bn2/3pp3/4P3/3P1P2/PPP2KPP/RNB1QBNR"
#
# Site to make other FEN strings: http://www.netreal.de/Forsyth-Edwards-Notation/index.php

STARTING_FEN = "r2qk2r/ppp1bppp/2n1bn2/3pp3/4P3/3P1P2/PPP2KPP/RNB1QBNR" # Add string HERE!

board = objects.Board(renderer, clicker, objects.Point(10, 10), starting_fen=STARTING_FEN)


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

last_board_move = board.last_move


if board.board.turn == chess.BLACK:
    # Add end turn event to let ai run.
    pygame.event.post(pygame.event.Event(utils.TURN_DONE))

last_action_type = None

while running:
    prev_cursor_pos = cursor_pos
    down_button = 0
    up_button = 0

    # Handling Mouse and Hand -> Registering Click and Hand Movements 
    curr_time = int(timer() * 1000)     # Current Time 
    new_mouse_pos = objects.Point(*pygame.mouse.get_pos())
    if new_mouse_pos != mouse_pos:
        last_action_type = 0
        mouse_pos = new_mouse_pos
        mouse_timestamp = curr_time
    hand_cursor_pos, hand_click, hand_release, hand_timestamp = hand_detector.process_gestures(curr_time)

    if mouse_timestamp >= hand_timestamp:
        cursor_pos = mouse_pos
    else:
        last_action_type = 1
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
                    down_button += 1
            case pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    clicker.execute_click(False)
                    up_button += 1
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
                    ai_moves.append(board.last_move)
            case utils.GAME_ENDED:
                game_ended = True
                context_text.set_text("Game ended! Press \'R\' to restart", cfg.colors["redtext"])
    
    utterances = 0

    if clicker.cursor.holding is None and hand_cursor_pos is None and board.board.turn == chess.WHITE:
        utterances = len(speech_manager.commands)
        command, some_command = speech_manager.resolve_commands(curr_time)
        # Execute command 
        if command:
            last_action_type = 2
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

    now = str(datetime.now())
    cursor_dist = ((prev_cursor_pos[0] - cursor_pos[0]) ** 2 + (prev_cursor_pos[1] - cursor_pos[1]) ** 2) ** .5
    did_move = None
    if last_board_move != board.last_move:
        if board.board.turn == chess.BLACK:
            did_move = board.last_move
            last_board_move = board.last_move

    match last_action_type:
        case 0: # Mouse action
            if curr_action is not None:
                if curr_action["action_type"] != "mouse":
                    curr_action["action_end"] = now
                    actions.append(curr_action)
                    curr_action = {"action_start": now, "action_type": "mouse", "action_dist": 0.0, "down_button": 0, "up_button": 0, "moves": []}
            else:
                curr_action = {"action_start": now, "action_type": "mouse", "action_dist": 0.0, "down_button": 0, "up_button": 0, "moves": []}
            curr_action["action_dist"] += cursor_dist
            curr_action["down_button"] += down_button
            curr_action["up_button"] += up_button
        case 1: # Hand action
            if curr_action is not None:
                if curr_action["action_type"] != "hand":
                    curr_action["action_end"] = now
                    actions.append(curr_action)
                    curr_action = {"action_start": now, "action_type": "hand", "action_dist": 0.0, "down_button": 0, "up_button": 0, "moves": []}
            else:
                curr_action = {"action_start": now, "action_type": "hand", "action_dist": 0.0, "down_button": 0, "up_button": 0, "moves": []}
            curr_action["action_dist"] += cursor_dist
            curr_action["down_button"] += down_button
            curr_action["up_button"] += up_button
        case 2: # Speech action
            if curr_action is not None:
                if curr_action["action_type"] != "speech":
                    curr_action["action_end"] = now
                    actions.append(curr_action)
                    curr_action = {"action_start": now, "action_type": "speech", "utterances": 0, "moves": []}
            else:
                curr_action = {"action_start": now, "action_type": "speech", "utterances": 0, "moves": []}
            curr_action["utterances"] += utterances
    
    if curr_action is not None and did_move:
        curr_action["moves"].append(did_move)

            
engine.close()
speech_manager.stop()

# Quit Pygame
pygame.quit()

if curr_action is not None:
    actions.append(curr_action)
with open("./recordings/recording_" + recording_start.strftime("%Y-%m-%d_%H-%M-%S") + ".json", "w") as f:
    json.dump({"fen":STARTING_FEN,"player":actions, "ai": ai_moves}, f)