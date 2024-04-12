colors = dict(
    background = "#1d212b",
    light_square = "#f0d9b5",
    dark_square = "#b58863",
    highlight = "#f8f8f8",
    selected = "#274c1e",
    moveable = "#7ff461",
    danger = "#f64141",
    boardtext = "#f0f0f0",
    restart_button = "#c4c4c4",
    promotion_highlight = "#7ff461"
)

SQUARES_ALPHA = 128
SQUARE_SIZE = 70
SQUARE_CLICK_PRIORITY = 0

TEXT_ANTIALIAS = True

BOARD_TEXT_SIZE = 20
BOARD_TEXT_H_DISTANCE = 10
BOARD_TEXT_V_DISTANCE = 7
BOARD_TEXT_FONT = "resources\RobotoMono-VariableFont_wght.ttf"

RESTART_BUTTON_TEXT_SIZE = 18
RESTART_BUTTON_STROKE_WIDTH = 4

cursor = dict(
    offset = 9,
    size = 19,
    bottom = 7,
    top = 11
)

MOVE_VOLUME = .6
ILLEGAL_MOVE_VOLUME = .15
KING_CHECK_VOLUME = .5


AI_THINK_TIME = 0.1
AI_MOVING_TIME = 1000

PROMOTION_CLICK_PRIORITY = 1