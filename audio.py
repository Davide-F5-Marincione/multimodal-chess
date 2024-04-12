import pygame

pygame.mixer.init()
# Tried making them my own... not great
# MOVE_SOUNDS = [pygame.mixer.Sound(f"resources/sounds/move{i}.wav") for i in range(1, 5)]

# Found at https://www.chess.com/forum/view/general/chessboard-sound-files
MOVE_SOUND = pygame.mixer.Sound(f"resources/sounds/chess-com-move.mp3")
ILLEGAL_MOVE_SOUND = pygame.mixer.Sound(f"resources/sounds/illegal_move.mp3")
CHECK_SOUND = pygame.mixer.Sound(f"resources/sounds/king_check.mp3")