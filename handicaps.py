from squares import Square
import random

def no_handicap(board, start, stop, history):
    return True

def cant_move_pawns(board, start, stop, history):
    return not (board.get(start) and board.get(start).piece.value == 'P')

def cant_move_pawn_and_then_rook(board, start, stop, history):
    if len(history) < 2:
        return True
    last_move = history[-2]
    return not (board.get(start) and board.get(start).piece.value == 'R' and last_move.piece.piece.value == 'P')

def die_after_moving_pawn(board, start, stop, history):
    if len(history) < 2:
        return True
    last_move = history[-2]
    return not last_move.piece.piece.value == 'P'

def lose_if_no_queen(board, start, stop, history):
    color = 'W' if not history or history[-1].piece.color.value == 'B' else 'B'
    for square in Square:
        if board.get(square) and board.get(square).piece.value == 'Q' and board.get(square).color.value == color:
            return True
    return False

# This doesn't work b/c check isn't implemented
def skittish(board, start, stop, history):
    if history:
        print(history[-1].check)
    return not history or not history[-1].check or board.get(start).piece.value == 'K'

def bongcloud(board, start, stop, history):
    # TODO
    return False

# number is how bad the handicap is, 1-10
handicaps = {
    'No handicap': (no_handicap, 1),
    "Can't move pawns": (cant_move_pawns, 7),
    "Can't move pawn and then rook": (cant_move_pawn_and_then_rook, 3),
    "Die after moving pawn": (die_after_moving_pawn, 7),
    "Lose if you have no queen": (lose_if_no_queen, 7),
    "When you get checked, you must move your king": (skittish, 2),
    "When your king is on the back rank, you can only move pawns and kings": (bongcloud, 2)
}

# theoretical args for some kind of config, e.g. difficulties, elos, idk
def get_handicaps(x, y):
    return random.sample(handicaps.keys(), 2)
