from squares import Square, Rank, File
from chess import Color, Piece, ColoredPiece
from settings import LOCAL
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
    return board.loc(ColoredPiece(history.whose_turn(), Piece.QUEEN))

# This doesn't work b/c check isn't implemented


def skittish(board, start, stop, history):
    # Use board.cache
    history = history.history
    if history:
        print(history[-1].check)
    return not history or not history[-1].check or board.get(start).piece == Piece.KING


def bongcloud(board, start, stop, history):
    king_pos = board.cache.kings[history.whose_turn()]
    if not king_pos:
        # You should probably have a king but idk not my problem if you don't
        return True
    if king_pos.rank() == (Rank.First if history.whose_turn() == Color.WHITE else Rank.Eighth):
        # piece should never be None but idk
        piece = board.get(start) and board.get(start).piece
        return piece in [Piece.PAWN, Piece.KING]
    return True


def cant_move_to_opponents_side_of_board(board, start, stop, history):
    color = history.whose_turn()
    ranks = [Rank.First, Rank.Second, Rank.Third, Rank.Fourth]
    if color == Color.WHITE:
        ranks = [rank.flip() for rank in ranks]
    return not stop.rank() in ranks

def cant_move_to_half_of_squares_at_random(board, start, stop, history):
    random.seed(board.cache.rand)
    squares = random.sample(list(Square), 32)
    return stop in squares


# number is how bad the handicap is, 1-10
handicaps = {
    'No handicap': (no_handicap, 1),
    "Can't move pawns": (cant_move_pawns, 7),
    "Can't move pawn and then rook": (cant_move_pawn_and_then_rook, 3),
    "Die after moving pawn": (die_after_moving_pawn, 7),
    "Lose if you have no queen": (lose_if_no_queen, 7),
    "While in check, you must move your king": (skittish, 2),
    "When your king is on the back rank, you can only move pawns and kings": (bongcloud, 2),
    "Can't move to opponent's side of board": (cant_move_to_opponents_side_of_board, 5),
    "Can't move to half of squares, re-randomized every move": (cant_move_to_half_of_squares_at_random, 5)
}

descriptions = {v[0]: k for k, v in handicaps.items()}

# theoretical args for some kind of config, e.g. difficulties, elos, idk


def get_handicaps(x, y):
    # So I can't forget to undo anything weird
    if not LOCAL:
        return random.sample(handicaps.keys(), 2)
    return descriptions[cant_move_to_half_of_squares_at_random], descriptions[lose_if_no_queen]
    # return descriptions[cant_move_to_opponents_side_of_board], descriptions[cant_move_to_opponents_side_of_board]
