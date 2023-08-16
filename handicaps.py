from squares import Square, Rank, File
from chess import Color, Piece
import random

def no_handicap(board, start, stop, history):
    return True

def cant_move_pawns(board, start, stop, history):
    return not (board.get(start) and board.get(start).piece == Piece.PAWN)

def cant_move_pawn_and_then_rook(board, start, stop, history):
    history = history.history
    if len(history) < 2:
        return True
    last_move = history[-2]
    return not (board.get(start) and board.get(start).piece == Piece.ROOK and last_move.piece.piece == Piece.PAWN)

def die_after_moving_pawn(board, start, stop, history):
    history = history.history
    if len(history) < 2:
        return True
    last_move = history[-2]
    return not last_move.piece.piece.value == 'P'

def lose_if_no_queen(board, start, stop, history):
    color = history.whose_turn
    for square in Square:
        if board.get(square) and board.get(square).piece == Piece.QUEEN and board.get(square).color == color:
            return True
    return False

# This doesn't work b/c check isn't implemented
def skittish(board, start, stop, history):
    history = history.history
    if history:
        print(history[-1].check)
    return not history or not history[-1].check or board.get(start).piece == Piece.KING

def bongcloud(board, start, stop, history):
    # TODO
    return False

def cant_move_to_opponents_side_of_board(board, start, stop, history):
    color = history.whose_turn
    ranks = [Rank.First, Rank.Second, Rank.Third, Rank.Fourth] if color == Color.BLACK else [Rank.Fifth, Rank.Sixth, Rank.Seventh, Rank.Eighth]
    return not stop.rank() in ranks

# number is how bad the handicap is, 1-10
handicaps = {
    'No handicap': (no_handicap, 1),
    "Can't move pawns": (cant_move_pawns, 7),
    "Can't move pawn and then rook": (cant_move_pawn_and_then_rook, 3),
    "Die after moving pawn": (die_after_moving_pawn, 7),
    "Lose if you have no queen": (lose_if_no_queen, 7),
    "When you get checked, you must move your king": (skittish, 2),
    # Commented out since it would randomly just end some games instantly lol
    # "When your king is on the back rank, you can only move pawns and kings": (bongcloud, 2),
    "Can't move to opponent's side of board": (cant_move_to_opponents_side_of_board, 5),
}

# theoretical args for some kind of config, e.g. difficulties, elos, idk
def get_handicaps(x, y):
    # return ["Can't move to opponent's side of board", "No handicap"]
    return random.sample(handicaps.keys(), 2)
