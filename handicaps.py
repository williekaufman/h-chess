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

def peons_first(board, start, stop, history):
    piece = board.get(start).piece
    pr, f = start.to_coordinates()
    above_rank = pr + 1 if piece.color == Color.WHITE else pr - 1
    if above_rank >= 0 and above_rank < 8:
        above_sq = board.board[above_rank, start.file()]
        if board.get(above_sq) and board.get(above_sq).piece == Piece.PAWN:
            return False
    return True

def true_gentleman(board, start, stop, history):
    ss = board.get(stop)
    if ss and ss.piece:
        return ss.piece == Piece.QUEEN and ss.piece.color != history.whose_turn()   
    return True

def forward_march(board, start, stop, history):
    start_r, f = start.to_coordinates()
    stop_r, sf = stop.to_coordinates()
    if history.whose_turn() == Color.WHITE:
        return stop_r < start_r
    else:
        return stop_r >= start_r

def hipster(board, start, stop, history):
    history = history.history
    if len(history) < 1:
        return True
    last_move = history[-1]
    p = board.get(start) and board.get(start).piece
    lp = board.get(last_move.start()) and board.get(last_move.start()).piece
    return p != lp

def stoic(board, start, stop, history):
    p = board.get(start) and board.get(start).piece
    return p != Piece.KING

def conscientious_objectors(board, start, stop, history):
    p = board.get(start) and board.get(start).piece
    stop_p = board.get(stop) and board.get(stop).piece
    if p and stop_p:
        return stop_p.color != history.whose_turn() and p == Piece.PAWN
    else:
        return True

def outflanked(board, start, stop, history):
    stop_r, stop_f = board.stop
    return not ((board.get(stop).file() == File.A or File.H) and (board.get(stop).piece) and board.get(stop).piece.color != history.whose_turn())

def no_shuffling(board, start, stop, history):
    piece = board.get(start)
    return not (piece and piece.piece == Piece.ROOK and start.rank() == stop.rank()) 

def horse_tranquilizer(board, start, stop, history):
    start_p = board.get(start)
    stop_p = board.get(stop)
    return not (start_p.piece and stop_p.piece and start_p.piece == Piece.KNIGHT and stop_p.piece.color != history.whose_turn())

def rushing_river(board, start, stop, history):
    return not (board.get(start).piece != Piece.PAWN and stop.rank() in [Rank.Fourth, Rank.Fifth])

def pawn_battle(board, start, stop, history):
    player_pawns = board.loc(ColoredPiece(history.whose_turn(), Piece.PAWN))
    opp_pawns = board.loc(ColoredPiece(history.whose_turn().other(), Piece.PAWN))
    return len(player_pawns) >= len(opp_pawns)

def horse_eats_first(board, start, stop, history):
    knights = board.loc(ColoredPiece(history.whose_turn(), Piece.KNIGHT))
    return not (knights and board.get(start).piece and board.get(start).piece == Piece.KNIGHT)

def royal_berth(board, start, stop, history):
    king_pos = board.cache.kings[history.whose_turn()]
    if not king_pos:
        return True
    return board.get(start).piece == Piece.KING or \
        abs(king_pos.rank().to_index() - stop.rank().to_index()) > 1 or \
        abs(king_pos.file().to_index() - stop.file().to_index()) > 1

def protected_pawns(board, start, stop, history):
    return board.get(start).piece != Piece.PAWN or board.is_attacked(stop, history.whose_turn().other())

# Not finished
def far_right_leader(board, start, stop, history):
    pawn_sqs = board.loc(ColoredPiece(history.whose_turn(), Piece.PAWN))
    pawn_coords = [p.to_coordinates() for p in pawn_sqs]

    return True

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
    "Can't move to half of squares, re-randomized every move": (cant_move_to_half_of_squares_at_random, 5),
    # These haven't been tested yet
    "Can't move pieces that are directly behind one of your pawns": (peons_first, 2),
    "You cannot capture your opponent's queen": (true_gentleman, 2),
    "Your pieces cannot move backwards": (forward_march, 3),
    "You can't move a piece of the same type your opponent just moved": (hipster, 2),
    "You can't move your king": (stoic, 2),
    "Your pawns can't capture": (conscientious_objectors, 3),
    "You can't capture on the A or the H file": (outflanked, 2), 
    "Your rooks can't move sideways": (no_shuffling, 2), 
    "Your knights can't capture": (horse_tranquilizer, 1), 
    "You can't move non-pawns onto the fourth or fifth ranks": (rushing_river, 3),
    "Lose if you have fewer pawns than your opponent at the start of your turn": (pawn_battle, 3),
    "As long as you have a knight, you can only capture with knights": (horse_eats_first, 3), 
    "You can't move anything next to your king": (royal_berth, 3),
    "Your pawns can only move to defended squares": (protected_pawns, 2), 
    "Your rightmost pawn must be your most-advanced pawn at all times": (far_right_leader, 3)
}

descriptions = {v[0]: k for k, v in handicaps.items()}

# theoretical args for some kind of config, e.g. difficulties, elos, idk


def get_handicaps(x, y):
    # So I can't forget to undo anything weird
    if not LOCAL:
        return random.sample(handicaps.keys(), 2)
    # This is Gabe's line. For Gabe's use only. Keep out. No girls allowed. 
    return random.sample(handicaps.keys(), 2)
    # return descriptions[cant_move_to_half_of_squares_at_random], descriptions[lose_if_no_queen]
    # return descriptions[cant_move_to_opponents_side_of_board], descriptions[cant_move_to_opponents_side_of_board]
