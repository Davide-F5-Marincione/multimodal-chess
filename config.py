colors = dict(
    background = "#1d212b",
    light_square = "#f0d9b5",
    dark_square = "#b58863",
    highlight = "#f8f8f8",
    selected = "#274c1e",
    moveable = "#7ff461",
    danger = "#f64141",
    boardtext = "#f0f0f0",
    redtext = "#CB0202",
    promotion_highlight = "#7ff461",
    restart = "#4DE094",
    takeback = "#4DE0DB",
)

SQUARES_ALPHA = 128
SQUARE_SIZE = 70

TEXT_ANTIALIAS = True

BOARD_TEXT_SIZE = 20
BOARD_TEXT_H_DISTANCE = 10
BOARD_TEXT_V_DISTANCE = 7
BOARD_TEXT_FONT = "resources\RobotoMono-VariableFont_wght.ttf"


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

CURSOR_ORDER = 999
CURSOR_SHADOW_ORDER = -999
BOARD_ORDER = 0
GUISQUARE_ORDER = 1
PROMOTION_BUBBLE_ORDER = 2
PROMOTION_SQUARE_ORDER = 3


VOCAL_COMMANDS_TIMOUT = 500


MIN_PALM_WIDTH_DIFFERENCE = .1
MAX_HAND_MOVEMENT = 10


# Former values
DOT_CLICK_HYST = .8
DOT_CLICK = .8
DIST_CLICK_HYST = .4
DIST_CLICK = .4

# new values, no hysteresis and no dot product check
# DOT_CLICK_HYST = 0
# DOT_CLICK = 0
# DIST_CLICK_HYST = .4
# DIST_CLICK = .4