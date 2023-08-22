from squares import Square, Rank, File
from chess import Color, Piece, ColoredPiece
from settings import LOCAL
import random


def try_move(board, start, stop, history):
    new_board = board.copy()
    new_board.move(start, stop, history.whose_turn(), None, history)
    return new_board

def get_adjacent_squares(board, square):
    r = square.rank().to_index()
    f = square.file().to_index()
    adj_sqs = []
    for i in range(3):
        for j in range(3):
            if 0 <= r + i - 1 <= 7 and 0 <= f + j - 1 <= 7 and not (i == 1 and j == 1):
                adj_sqs.append(square.shift(i - 1, j - 1))
    return adj_sqs

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
    piece = board.get(start)
    pr, f = start.to_coordinates()
    above_rank = pr + 1 if piece.color == Color.WHITE else pr - 1
    if above_rank >= 0 and above_rank < 8:
        above_piece = board.board[above_rank][start.file().to_index()]
        if above_piece and above_piece.piece == Piece.PAWN:
            return False
    return True

def true_gentleman(board, start, stop, history):
    ss = board.get(stop)
    if ss and ss.piece:
        return not (ss.piece == Piece.QUEEN and ss.color != history.whose_turn())
    return True

def forward_march(board, start, stop, history):
    start_r, f = start.to_coordinates()
    stop_r, sf = stop.to_coordinates()
    if history.whose_turn() == Color.WHITE:
        return stop_r >= start_r
    else:
        return stop_r <= start_r

def hipster(board, start, stop, history):
    history = history.history
    if len(history) < 1:
        return True
    last_move = history[-1]
    p = board.get(start).piece
    lp = last_move.piece.piece
    return p != lp

def stoic(board, start, stop, history):
    p = board.get(start) and board.get(start).piece
    return p != Piece.KING

def conscientious_objectors(board, start, stop, history):
    p = board.get(start)
    stop_p = board.get(stop)
    if p and stop_p:
        return not (stop_p.color != history.whose_turn() and p.piece == Piece.PAWN)
    else:
        return True

def outflanked(board, start, stop, history):
    stop_piece = board.get(stop)
    return not ((stop.file() == File.A or stop.file() == File.H) and \
                stop_piece and stop_piece.color != history.whose_turn())

def no_shuffling(board, start, stop, history):
    piece = board.get(start)
    return not (piece and piece.piece == Piece.ROOK and start.rank() == stop.rank()) 

def horse_tranquilizer(board, start, stop, history):
    start_p = board.get(start)
    stop_p = board.get(stop)
    if start_p and stop_p:
        return not (start_p.piece == Piece.KNIGHT and stop_p.color != history.whose_turn())
    else:
        return True

def rushing_river(board, start, stop, history):
    return not (board.get(start).piece != Piece.PAWN and stop.rank() in [Rank.Fourth, Rank.Fifth])

def pawn_battle(board, start, stop, history):
    player_pawns = board.loc(ColoredPiece(history.whose_turn(), Piece.PAWN))
    opp_pawns = board.loc(ColoredPiece(history.whose_turn().other(), Piece.PAWN))
    return len(player_pawns) >= len(opp_pawns)

def horse_eats_first(board, start, stop, history):
    knights = board.loc(ColoredPiece(history.whose_turn(), Piece.KNIGHT))
    stop_piece = board.get(stop)
    if stop_piece:
        print(stop_piece.color)
    return not (len(knights) > 0 and stop_piece and stop_piece.color != history.whose_turn() and board.get(start).piece != Piece.KNIGHT)

def royal_berth(board, start, stop, history):
    king_pos = board.cache.kings[history.whose_turn()]
    if not king_pos:
        return True
    return board.get(start).piece == Piece.KING or \
        abs(king_pos.rank().to_index() - stop.rank().to_index()) > 1 or \
        abs(king_pos.file().to_index() - stop.file().to_index()) > 1

def protected_pawns(board, start, stop, history):
    if board.get(start).piece != Piece.PAWN:
        return True
    new_board = try_move(board, start, stop, history)
    return new_board.is_attacked(stop, history.whose_turn(), history)

def pack_mentality(board, start, stop, history):
    sqs = get_adjacent_squares(board, stop)
    adj_pcs = [sq for sq in sqs if board.get(sq) and board.get(sq).color == history.whose_turn() and sq != start]
    return len(adj_pcs) > 0 

def spice_of_life(board, start, stop, history):
    history = history.history
    if len(history) < 2:
        return True
    last_move = history[-2]
    return not (board.get(start) and board.get(start).piece == last_move.piece.piece)

def jumpy(board, start, stop, history):
    c = history.whose_turn()
    for square in Square:
        if  board.get(square) and board.get(square).color == c and \
            board.is_attacked(square, c.other(), history) and board.legal_moves(square, history, c):
            return board.is_attacked(start, c.other(), history)
    return True

def eye_for_an_eye(board, start, stop, history):
    if len(history.history) > 0 and history.history[-1].capture:
        return board.get(stop) 
    else:
        return True

def no_recapture(board, start, stop, history):
    if len(history.history) > 0:
        
    return True

# Not finished
def far_right_leader(board, start, stop, history):
    pawn_sqs = board.loc(ColoredPiece(history.whose_turn(), Piece.PAWN))
    pawn_coords = [p.to_coordinates() for p in pawn_sqs]
    return True


# Not finished
def horsey_hops(board, start, stop, history):
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
    "Can't move pieces that are directly behind one of your pawns": (peons_first, 2),
    "You cannot capture your opponent's queen": (true_gentleman, 2),
    "Your pieces cannot move backwards": (forward_march, 4),
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
    "Your pieces must move to squares adjacent to another one of your piece": (pack_mentality, 4),
    "You can't move the same piece type twice in a row (Spice of Life)": (spice_of_life, 3), 
    "When possible, you must move a piece that is being attacked": (jumpy, 4), 
    "If your opponent captures something, you must capture something in response (or lose)": (eye_for_an_eye, 5), 
}

# Stuff in here won't randomly get assigned but you can interact with it by changing get_handicaps 
# So you can push new handicaps without worrying about breaking the game
untested_handicaps = {
    "Your rightmost pawn must be your most-advanced pawn at all times": (far_right_leader, 3),
    "If your knight can hop over a non-pawn piece, it must": (horsey_hops, 2), 
    "You cannot recapture": (no_recapture, 4)
}

descriptions = {v[0]: k for k, v in handicaps.items()}
descriptions.update({v[0]: k for k, v in untested_handicaps.items()})

# theoretical args for some kind of config, e.g. difficulties, elos, idk


def get_handicaps(x, y):
    # So I can't forget to undo anything weird
    if not LOCAL:
        return random.sample(handicaps.keys(), 2)
    else:
        # This is Gabe's line. For Gabe's use only. Keep out. No girls allowed. 
        handicaps.update(untested_handicaps)
        return descriptions[eye_for_an_eye], descriptions[eye_for_an_eye] 
    # return descriptions[cant_move_to_half_of_squares_at_random], descriptions[lose_if_no_queen]
    # return descriptions[cant_move_to_opponents_side_of_board], descriptions[cant_move_to_opponents_side_of_board]
