# test_helper.py
# Deterministic helper used by tester.py
# Must provide the same API as the real helper used by battleship.py

NUM_ROWS = 5
NUM_COLUMNS = 5
SHIP_SIZES = (3, 2)

WATER = 0
SHIP = 1
HIT_WATER = 2
HIT_SHIP = 3

# State for scripted behavior
INPUT_QUEUE = []
_input_index = 0

SHIP_PLACEMENTS = []   # list of (row,col) tuples for computer ship placement
_ship_index = 0

TORPEDO_SEQUENCE = []  # list of (row,col) tuples for computer torpedoes
_torpedo_index = 0

def reset():
    global _input_index, _ship_index, _torpedo_index
    _input_index = 0
    _ship_index = 0
    _torpedo_index = 0

def get_input(msg):
    """Print the prompt (so it's captured) and return the next scripted input."""
    global _input_index
    # print prompt without newline (to emulate input(prompt))
    print(msg, end="")
    if _input_index >= len(INPUT_QUEUE):
        # fallback: return empty string and also print a newline to keep logs tidy
        print()
        return ""
    val = INPUT_QUEUE[_input_index]
    _input_index += 1
    # emulate the user typing it (so it appears in the output)
    print(val)
    return val

def show_msg(msg):
    print(msg)

def show_board(board1, board2=None):
    """
    Only output board content, wrapped in markers so tester can detect it.
    """
    def row_to_str(r):
        return ''.join(
            'x' if c == SHIP else
            '*' if c == HIT_SHIP else
            'o' if c == HIT_WATER else
            '.' for c in r
        )

    print("===SHOW_BOARD===")

    if board2 is None:
        for row in board1:
            print(row_to_str(row))
    else:
        rows1 = [row_to_str(r) for r in board1]
        rows2 = [row_to_str(r) for r in board2]
        for i in range(max(len(rows1), len(rows2))):
            a = rows1[i] if i < len(rows1) else ''
            b = rows2[i] if i < len(rows2) else ''
            print(f"{a} | {b}")

    print("===END_SHOW_BOARD===")

def is_cell_name(s):
    return bool(s) and s[:1].isalpha() and s[1:].isdigit()

def random_cell(cells):
    # deterministic fallback
    return cells[0]

def choose_ship_location(board, size, locations):
    global _ship_index
    if SHIP_PLACEMENTS and _ship_index < len(SHIP_PLACEMENTS):
        loc = SHIP_PLACEMENTS[_ship_index]
        _ship_index += 1
        return loc
    # fallback: return the first available
    return locations[0]

def choose_torpedo_target(board, locations):
    global _torpedo_index
    if TORPEDO_SEQUENCE and _torpedo_index < len(TORPEDO_SEQUENCE):
        loc = TORPEDO_SEQUENCE[_torpedo_index]
        _torpedo_index += 1
        return loc
    return locations[0]

def seed(a):
    pass
