from squares import Square
import random

def cant_move(board, start, stop, history):
    return False

def no_handicap(board, start, stop, history):
    return not (start == Square('E2') and stop == Square('E4'))

def cant_move_pawns(board, start, stop, history):
    return not (board.get(start) and board.get(start).piece.value == 'P')

def cant_move_pawn_and_then_rook(board, start, stop, history):
    if len(history) < 2:
        return True
    last_move = history[-2]
    return not (board.get(start) and board.get(start).piece.value == 'R' and last_move.piece.piece.value == 'P')

# number is how bad the handicap is, 1-10
handicaps = {
    'No handicap': (no_handicap, 1),
    "Can't move": (cant_move, 10),
    "Can't move pawns": (cant_move_pawns, 7),
    "Can't move pawn and then rook": (cant_move_pawn_and_then_rook, 3)
}

# theoretical args for some kind of config, e.g. difficulties, elos, idk
def get_handicaps(x, y):
    # return random.sample(handicaps.keys(), 2)
    return ['No handicap', 'No handicap']
