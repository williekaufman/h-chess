from squares import Square, Rank, File
from chess import Color, Piece, ColoredPiece, HandicapInputs, starting_board, History
from settings import LOCAL
import random


def try_move(board, start, stop, history):
    new_board = board.copy()
    new_board.move(start, stop, history.whose_turn(), None, history)
    return new_board

def get_adjacent_squares(square):
    adj_sqs = []
    for i in range(3):
        for j in range(3):
            if not (i == j == 1):
                adj_sqs.append(square.shift(i - 1, j - 1))
    return [sq for sq in adj_sqs if sq]

def no_handicap(start, stop, inputs):
    return True

def cant_move_pawns(start, stop, inputs):
    board = inputs.board
    return not (board.get(start) and board.get(start).piece == Piece.PAWN)


def cant_move_pawn_and_then_rook(start, stop, inputs):
    board, history = inputs.board, inputs.history.history
    if len(history) < 2:
        return True
    last_move = history[-2]
    return not (board.get(start) and board.get(start).piece == Piece.ROOK and last_move.piece.piece == Piece.PAWN)


def die_after_moving_pawn(start, stop, inputs):
    history = inputs.history.history
    if len(history) < 2:
        return True
    last_move = history[-2]
    return not last_move.piece.piece.value == 'P'


def lose_if_no_queen(start, stop, inputs):
    board, history = inputs.board, inputs.history
    return board.loc(ColoredPiece(history.whose_turn(), Piece.QUEEN))

# This doesn't work b/c check isn't implemented
def skittish(start, stop, inputs):
    # Use board.cache
    board, history = inputs.board, inputs.history.history 
    if history:
        print(history[-1].check)
    return not history or not history[-1].check or board.get(start).piece == Piece.KING


def bongcloud(start, stop, inputs):
    board, history = inputs.board, inputs.history
    king_pos = board.cache.kings[history.whose_turn()]
    if not king_pos:
        # You should probably have a king but idk not my problem if you don't
        return True
    if king_pos.rank() == (Rank.First if history.whose_turn() == Color.WHITE else Rank.Eighth):
        # piece should never be None but idk
        piece = board.get(start) and board.get(start).piece
        return piece in [Piece.PAWN, Piece.KING]
    return True


def cant_move_to_opponents_side_of_board(start, stop, inputs):
    history = inputs.history
    color = history.whose_turn()
    ranks = [Rank.First, Rank.Second, Rank.Third, Rank.Fourth]
    if color == Color.WHITE:
        ranks = [rank.flip() for rank in ranks]
    return not stop.rank() in ranks

def cant_move_to_half_of_squares_at_random(start, stop, inputs):
    board = inputs.board
    random.seed(board.cache.rand)
    squares = random.sample(list(Square), 32)
    return stop in squares

def peons_first(start, stop, inputs):
    board = inputs.board
    piece = board.get(start)
    pr, f = start.to_coordinates()
    above_rank = pr + 1 if piece.color == Color.WHITE else pr - 1
    if above_rank >= 0 and above_rank < 8:
        above_piece = board.board[above_rank][start.file().to_index()]
        if above_piece and above_piece.piece == Piece.PAWN:
            return False
    return True

def true_gentleman(start, stop, inputs):
    board, history = inputs.board, inputs.history
    ss = board.get(stop)
    if ss and ss.piece:
        return not (ss.piece == Piece.QUEEN and ss.color != history.whose_turn())
    return True

def forward_march(start, stop, inputs):
    return stop.rank().more_agg_or_equal(start.rank(), inputs.history.whose_turn())

def hipster(start, stop, inputs):
    board, history = inputs.board, inputs.history.history
    if len(history) < 1:
        return True
    last_move = history[-1]
    p = board.get(start).piece
    lp = last_move.piece.piece
    return p != lp

def stoic(start, stop, inputs):
    board = inputs.board
    p = board.get(start) and board.get(start).piece
    return p != Piece.KING

def conscientious_objectors(start, stop, inputs):
    board, history = inputs.board, inputs.history
    p = board.get(start)
    stop_p = board.get(stop)
    if p and stop_p:
        return not (stop_p.color != history.whose_turn() and p.piece == Piece.PAWN)
    else:
        return True

def outflanked(start, stop, inputs):
    board, history = inputs.board, inputs.history
    stop_piece = board.get(stop)
    return not ((stop.file() == File.A or stop.file() == File.H) and \
                stop_piece and stop_piece.color != history.whose_turn())

def no_shuffling(start, stop, inputs):
    board = inputs.board
    piece = board.get(start)
    return not (piece and piece.piece == Piece.ROOK and start.rank() == stop.rank()) 

def horse_tranquilizer(start, stop, inputs):
    board, history = inputs.board, inputs.history
    start_p = board.get(start)
    stop_p = board.get(stop)
    if start_p and stop_p:
        return not (start_p.piece == Piece.KNIGHT and stop_p.color != history.whose_turn())
    else:
        return True

def rushing_river(start, stop, inputs):
    board = inputs.board
    return not (board.get(start).piece != Piece.PAWN and stop.rank() in [Rank.Fourth, Rank.Fifth])

def pawn_battle(start, stop, inputs):
    board, history = inputs.board, inputs.history
    player_pawns = board.loc(ColoredPiece(history.whose_turn(), Piece.PAWN))
    opp_pawns = board.loc(ColoredPiece(history.whose_turn().other(), Piece.PAWN))
    return len(player_pawns) >= len(opp_pawns)

def horse_eats_first(start, stop, inputs):
    board, history = inputs.board, inputs.history
    knights = board.loc(ColoredPiece(history.whose_turn(), Piece.KNIGHT))
    stop_piece = board.get(stop)
    return not (len(knights) > 0 and stop_piece and stop_piece.color != history.whose_turn() and board.get(start).piece != Piece.KNIGHT)

def royal_berth(start, stop, inputs):
    board, history = inputs.board, inputs.history
    king_pos = board.cache.kings[history.whose_turn()]
    if not king_pos:
        return True
    return board.get(start).piece == Piece.KING or \
        abs(king_pos.rank().to_index() - stop.rank().to_index()) > 1 or \
        abs(king_pos.file().to_index() - stop.file().to_index()) > 1

def protected_pawns(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if board.get(start).piece != Piece.PAWN:
        return True
    new_board = try_move(board, start, stop, history)
    return new_board.is_attacked(stop, history.whose_turn(), history)

def pack_mentality(start, stop, inputs):
    board, history = inputs.board, inputs.history
    sqs = get_adjacent_squares(stop)
    adj_pcs = [sq for sq in sqs if board.get(sq) and board.get(sq).color == history.whose_turn() and sq != start]
    return len(adj_pcs) > 0 

def spice_of_life(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if (last_move := history.last_move(history.whose_turn())):
        return not (board.get(start) and board.get(start).piece == last_move.piece.piece)
    return True

def jumpy(start, stop, inputs):
    board, history = inputs.board, inputs.history
    c = history.whose_turn()
    for square in Square:
        if  board.get(square) and board.get(square).color == c and \
            board.is_attacked(square, c.other(), history) and board.legal_moves(square, history, c):
            return board.is_attacked(start, c.other(), history)
    return True

def eye_for_an_eye(start, stop, inputs):
    board, history = inputs.board, inputs.history.history
    if history and history[-1].capture:
        return board.get(stop) 
    else:
        return True

def turn_other_cheek(start, stop, inputs):
    history = inputs.history.history
    if history and history[-1].capture:
        return history[-1].stop != stop
    return True

# Not finished
def far_right_leader(start, stop, inputs):
    board, history = inputs.board, inputs.history
    pawn_sqs = board.loc(ColoredPiece(history.whose_turn(), Piece.PAWN))
    pawn_coords = [p.to_coordinates() for p in pawn_sqs]
    return True

def hedonic_treadmill(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if (last_move := history.last_move()): 
        return board.get(start).points() >= last_move.piece.points()
    else:
        return True

def going_the_distance(start, stop, inputs):
    if (last_move := inputs.history.last_move()):
        return start.distance(stop) >= last_move.start.distance(last_move.stop)
    else:
        return True

def social_distancing(start, stop, inputs):
    board, history = inputs.board, inputs.history
    sqs = get_adjacent_squares(stop)
    adj_pcs = [sq for sq in sqs if board.get(sq) and board.get(sq).color != history.whose_turn()]
    return len(adj_pcs) == 0 

def human_shield(start, stop, inputs):
    board, history = inputs.board, inputs.history
    piece = board.get(start)
    pr, f = stop.to_coordinates()
    col_sign = 1 if piece.color == Color.WHITE else -1 
    above_rank = pr + col_sign
    while(0 <= above_rank <= 7):
        above_piece = board.board[above_rank][stop.file().to_index()]
        if above_piece and above_piece.piece == Piece.PAWN and above_piece.color == history.whose_turn():
            return True
        above_rank += col_sign

    # If there's no pawn above, then this is legal iff it's a capture
    return board.get(stop) or piece.piece == Piece.PAWN

def simon_says(start, stop, inputs):
    if (last_move := inputs.history.last_move()):
        return last_move.stop.color() == stop.color()
    else:
        return True
    
def hopscotch(start, stop, inputs):
    history = inputs.history
    if (last_move := history.last_move(history.whose_turn())):
        return last_move.stop.color() != stop.color()
    else:
        return True

def drag(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if not board.loc(ColoredPiece(history.whose_turn(), Piece.QUEEN)):
        return False
    return (not (board.get(start).piece == Piece.QUEEN) or stop in get_adjacent_squares(start))

def chasm(start, stop, inputs):
    return not stop.rank() in [Rank.Fourth, Rank.Fifth]

def pawn_of_the_hill(start, stop, inputs):
    board, history = inputs.board, inputs.history
    new_board = try_move(board, start, stop, history)
    center_pieces = [new_board.get(Square('E4')), new_board.get(Square('E5')), new_board.get(Square('D4')), new_board.get(Square('D5'))]
    p = ColoredPiece(history.whose_turn(), Piece.PAWN)
    return [cp for cp in center_pieces if cp and p.equals(cp)]

def modest(start, stop, inputs):
    board, history = inputs.board, inputs.history
    def helper(b):
        pieces = [b.get(s) for s in list(Square) if b.get(s)]
        ap_ps = [p for p in pieces if p.color == history.whose_turn()]
        nap_ps = [p for p in pieces if p.color != history.whose_turn()]
        return len(ap_ps) <= len(nap_ps)
    new_board = try_move(board, start, stop, history)
    return helper(board) and helper(new_board)

def boastful(start, stop, inputs):
    board, history = inputs.board, inputs.history
    def helper(b):
        pieces = [b.get(s) for s in list(Square) if b.get(s)]
        ap_ps = [p for p in pieces if p.color == history.whose_turn()]
        nap_ps = [p for p in pieces if p.color != history.whose_turn()]
        return len(ap_ps) >= len(nap_ps)
    new_board = try_move(board, start, stop, history)
    return helper(board) and helper(new_board)

# Broken somehow
def closed_book(start, stop, inputs):
    board, history = inputs.board, inputs.history
    def helper(b):
        for file in list(File):
            sqs = Square.of_file(file)
            pawns = [p for p in Square.of_file(file) if (b.get(p) and b.get(p).piece == Piece.PAWN)]
            if not pawns:
                return False
        return True
    new_board = try_move(board, start, stop, history)
    return helper(board) and helper(new_board)

# number is how bad the handicap is, 1-10
handicaps = {
    'No handicap': (no_handicap, 0),
    "Can't move pawns": (cant_move_pawns, 7),
    "Can't move pawn and then rook": (cant_move_pawn_and_then_rook, 3),
    "Die after moving pawn": (die_after_moving_pawn, 7),
    "Lose if you have no queen": (lose_if_no_queen, 7),
    "While in check, you must move your king": (skittish, 2),
    "When your king is on the back rank, you can only move pawns and kings": (bongcloud, 2),
    "Can't move to opponent's side of board": (cant_move_to_opponents_side_of_board, 5),
    "Can't move to half of squares, re-randomized every move": (cant_move_to_half_of_squares_at_random, 5),
    "Peons First: Can't move pieces that are directly behind one of your pawns": (peons_first, 2),
    "True Gentleman: You cannot capture your opponent's queen": (true_gentleman, 2),
    "Forward March: Your pieces cannot move backwards": (forward_march, 4),
    "Hipster: You can't move a piece of the same type your opponent just moved": (hipster, 2),
    "Stoic: You can't move your king": (stoic, 2),
    "Conscientious Objectors: Your pawns can't capture": (conscientious_objectors, 3),
    "Outflanked: You can't capture on the A or the H file": (outflanked, 1), 
    "No Shuffling: Your rooks can't move sideways": (no_shuffling, 2), 
    "Horse Tranquilizer: Your knights can't capture": (horse_tranquilizer, 1), 
    "Rushing River: You can't move non-pawns onto the fourth or fifth ranks": (rushing_river, 3),
    "Pawn Battle: Lose if you have fewer pawns than your opponent at the start of your turn": (pawn_battle, 3),
    "Horse Eats First: As long as you have a knight, you can only capture with knights": (horse_eats_first, 3), 
    "Royal Berth: You can't move anything next to your king": (royal_berth, 3),
    "Protected Pawns: Your pawns can only move to defended squares": (protected_pawns, 2), 
    "Pack Mentality: Your pieces must move to squares adjacent to another one of your pieces": (pack_mentality, 4),
    "Jumpy: When possible, you must move a piece that is being attacked": (jumpy, 4), 
    "Eye for an Eye: If your opponent captures something, you must capture something in response (or lose)": (eye_for_an_eye, 5), 
    "Turn the Other Cheek: You cannot recapture": (turn_other_cheek, 4),
    "Social Distancing: You cannot move pieces adjacent to your opponent’s pieces": (social_distancing, 6),
    "Human Shield: You can only make non-pawn, non-capturing moves to squares that are behind one of your pawns": (human_shield, 6),
    "Drag: Your queen is actually a king. It can only move like a king, and if it is taken, you lose": (drag, 5),
    "Chasm: You cannot move into the middle two ranks": (chasm, 5),
    "Pawn of the Hill: You must end your turn with a pawn in one of the four center squares": (pawn_of_the_hill, 6), 
    "Modest: You can never have more pieces than your opponent": (modest, 7),
    "Boastful: You can never have fewer pieces than your opponent": (boastful, 7), 
    "Closed book: You lose if there is ever an open file": (closed_book, 7),
    "Hedonic Treadmill: You must move a piece at least as valuable as your opponent’s last moved piece": (hedonic_treadmill, 6), 
    "Spice of Life: You can't move the same piece type twice in a row": (spice_of_life, 3), 
    "Simon Says: You must move onto the same color square as your opponent's last move": (simon_says, 5),
    "Hopscotch: You must alternate moving to white and black squares": (hopscotch, 5),
    "Going the Distance: You must move as least as far (manhattan distance) as your opponent's last move": (going_the_distance, 5), 
}

# Stuff in here won't randomly get assigned but you can interact with it by changing get_handicaps 
# So you can push new handicaps without worrying about breaking the game
untested_handicaps = {

}

descriptions = {v[0]: k for k, v in handicaps.items()}
descriptions.update({v[0]: k for k, v in untested_handicaps.items()})

# theoretical args for some kind of config, e.g. difficulties, elos, idk


# This just checks that none of them throw errors when called
# Doesn't check logic or anything
# Hopefully just catches stupid things like calling piece.piece.piece.piece 
# when you wanted piece.piece.piece or whatever
def test_all_handicaps():
    inputs = HandicapInputs(starting_board(), History())
    for v in handicaps.values():
        v[0](Square.A1, Square.A2, inputs)


def get_handicaps(x, y):
    # So I can't forget to undo anything weird
    if not LOCAL:
        return random.sample(handicaps.keys(), 2)
    else:
        # This is Gabe's line. For Gabe's use only. Keep out. No girls allowed. 
        handicaps.update(untested_handicaps)
        return descriptions[going_the_distance], descriptions[closed_book] 
    # return descriptions[cant_move_to_half_of_squares_at_random], descriptions[lose_if_no_queen]
    # return descriptions[cant_move_to_opponents_side_of_board], descriptions[cant_move_to_opponents_side_of_board]
