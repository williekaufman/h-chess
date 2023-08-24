from squares import Square, Rank, File
from chess import Color, Piece, ColoredPiece, HandicapInputs, starting_board, empty_board, History
from settings import LOCAL
from collections import defaultdict
import random


def try_move(board, start, stop, history):
    new_board = board.copy()
    new_board.move(start, stop, history.whose_turn(), None, history)
    return new_board


def get_adjacent_squares(square):
    adj_sqs = []
    for i in range(3):
        for j in range(3):
            adj_sqs.append(square.shift(i - 1, j - 1))
    return [sq for sq in adj_sqs if sq and sq != square]


def get_orthogonally_adjacent_squares(square):
    return [sq for sq in get_adjacent_squares(square) if sq.distance(square) == 1]


def get_diagonally_adjacent_squares(square):
    return [sq for sq in get_adjacent_squares(square) if sq.distance(square) == 2]


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
        return True
    if king_pos.rank() == (Rank.First if history.whose_turn() == Color.WHITE else Rank.Eighth):
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


def cant_move_to_one_color_at_random(start, stop, inputs):
    color = Color.WHITE if inputs.board.cache.rand > 0.5 else Color.BLACK
    return stop.color() == color


def must_move_specific_piece_type_at_random(start, stop, inputs):
    board = inputs.board
    random.seed(board.cache.rand)
    has_legal_moves = {p: False for p in Piece}
    for square in Square:
        if board.get(square) and board.get(square).color == inputs.history.whose_turn():
            if board.legal_moves(square, inputs.history, inputs.history.whose_turn()):
                has_legal_moves[board.get(square).piece] = True
    pieces = [p for p in has_legal_moves.keys() if has_legal_moves[p]]
    if not pieces:
        return False
    piece = random.choice(pieces)
    return board.get(start).piece == piece


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
    return board.capture(start, stop, history) != Piece.QUEEN


def forward_march(start, stop, inputs):
    return stop.rank().more_adv_than_or_equal(start.rank(), inputs.history.whose_turn())


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
    return not ((stop.file() == File.A or stop.file() == File.H) and
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
    opp_pawns = board.loc(ColoredPiece(
        history.whose_turn().other(), Piece.PAWN))
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
    adj_pcs = [sq for sq in sqs if board.get(sq) and board.get(
        sq).color == history.whose_turn() and sq != start]
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
        if board.get(square) and board.get(square).color == c and \
                board.is_attacked(square, c.other(), history) and board.legal_moves(square, history, c):
            return board.is_attacked(start, c.other(), history)
    return True


def eye_for_an_eye(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if history.last_move() and history.last_move().capture:
        return board.capture(start, stop, history)
    else:
        return True


def turn_other_cheek(start, stop, inputs):
    history = inputs.history.history
    if history and history[-1].capture:
        return history[-1].stop != stop
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
    adj_pcs = [sq for sq in sqs if board.get(
        sq) and board.get(sq).color != history.whose_turn()]
    return len(adj_pcs) == 0


def human_shield(start, stop, inputs):
    board, history = inputs.board, inputs.history
    piece = board.get(start)
    pr, f = stop.to_coordinates()
    col_sign = 1 if piece.color == Color.WHITE else -1
    above_rank = pr + col_sign
    while (0 <= above_rank <= 7):
        above_piece = board.board[above_rank][stop.file().to_index()]
        if above_piece and above_piece.piece == Piece.PAWN and above_piece.color == history.whose_turn():
            return True
        above_rank += col_sign

    # If there's no pawn above, then this is legal iff it's a capture
    return board.capture(start, stop, history) or piece.piece == Piece.PAWN


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
    center_pieces = [new_board.get(Square('E4')), new_board.get(
        Square('E5')), new_board.get(Square('D4')), new_board.get(Square('D5'))]
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


def closed_book(start, stop, inputs):
    board, history = inputs.board, inputs.history

    def helper(b):
        for file in list(File):
            pawns = [p for p in file.squares() if (
                b.get(p) and b.get(p).piece == Piece.PAWN)]
            if not pawns:
                return False
        return True
    new_board = try_move(board, start, stop, history)
    return helper(board) and helper(new_board)


def cage_the_king(start, stop, inputs):
    board, history = inputs.board, inputs.history
    opp_king_sq = board.loc(ColoredPiece(
        history.whose_turn().other(), Piece.KING))[0]
    start_r = Rank.First if history.whose_turn() == Color.BLACK else Rank.Eighth
    return opp_king_sq.rank() == start_r


def inside_the_lines(start, stop, inputs):
    return not stop.file() in [File.A, File.H]


def left_for_dead(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if board.capture(start, stop, history):
        return stop.file().more_left_than(start.file(), inputs.history.whose_turn())
    return True


def taking_turns(start, stop, inputs):
    piece_counter = inputs.history.pieces_moved(include_zero=True)
    piece_counter[inputs.board.get(start).piece] += 1
    return max(piece_counter.values()) - min(piece_counter.values()) <= 1


def follow_the_shadow(start, stop, inputs):
    h = inputs.history.history
    board = inputs.board
    c = inputs.history.whose_turn()
    if len(h) > 0:
        target_sq = h[-1].start
        # To do
        for square in Square:
            if board.get(square) and board.get(square).color == c and \
                    target_sq.value in board.legal_moves(square, inputs.history, c):
                return stop == target_sq

    return True

# This works it's just not a super interesting handicap so leaving it in untested,
# just wanted to the test the history.pieces_moved() logic


def loneliest_number(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if board.get(start).piece == Piece.PAWN:
        return Piece.PAWN not in history.pieces_moved()
    return True


def only_capture_each_piece_type_once(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if (captured_piece := board.capture(start, stop, history)):
        return captured_piece.piece not in history.pieces_captured()
    return True


def no_captures(start, stop, inputs):
    board, history = inputs.board, inputs.history
    return not board.capture(start, stop, history)


def out_in_front(start, stop, inputs):
    board = inputs.board
    c = inputs.history.whose_turn()
    return not [sq for sq in Square if sq.file() == start.file() and board.get(sq) and board.get(sq).color == c and sq.rank().more_adv_than(start.rank(), c)]


def abstinence(start, stop, inputs):
    board = inputs.board
    opp = inputs.history.whose_turn().other()
    for sq in Square:
        if board.get(sq) and board.get(sq).color == opp and board.get(sq).piece != Piece.PAWN:
            p = board.get(sq).piece
            for adj_sq in get_adjacent_squares(sq):
                if board.get(adj_sq) and board.get(adj_sq).color == opp and board.get(adj_sq).piece == p:
                    return False
    return True


def flanking_attack(start, stop, inputs):
    board, history = inputs.board, inputs.history
    return start.file() in [File.A, File.H] or not board.capture(start, stop, history)


def your_own_size(start, stop, inputs):
    board = inputs.board
    captured_piece = board.capture(start, stop, inputs.history)
    return (not captured_piece) or captured_piece.piece in [board.get(start).piece, Piece.KING]


def ego_clash(start, stop, inputs):
    board = inputs.board
    c = inputs.history.whose_turn()
    new_board = try_move(board, start, stop, inputs.history)
    for file in File:
        if [s for s in file.squares() if new_board.get(s) and new_board.get(s).color == c and new_board.get(s).piece != Piece.PAWN]:
            return False
    return True


def in_mourning(start, stop, inputs):
    return inputs.board.get(start).piece not in inputs.history.pieces_captured()


def cowering_in_fear(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if (pieces_captured := history.pieces_captured(history.whose_turn().other())):
        return board.get(start).piece.points() >= max([piece.points() for piece in pieces_captured.keys()])
    return True


def yin_and_yang(start, stop, inputs):
    if inputs.board.capture(start, stop, inputs.history):
        return stop.color() == Color.BLACK
    else:
        return stop.color() == Color.WHITE


def color_swap(start, stop, inputs):
    return start.color() != stop.color()


def eat_your_vegetables(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if (captured_piece := board.capture(start, stop, history)):
        return captured_piece.piece == Piece.PAWN or not board.loc(ColoredPiece(history.whose_turn().other(), Piece.PAWN))
    return True


def chain_of_command(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if len(history.history) > 1:
        last_piece = history.history[-2].piece.piece
        return last_piece == Piece.KING or last_piece.points() <= board.get(start).points()
    else:
        return True


def pioneer(start, stop, inputs):
    board, history = inputs.board, inputs.history
    return not [s for s in stop.rank().squares() if board.get(s) and board.get(s).color == history.whose_turn()]


def friendly_fire(start, stop, inputs):
    board, history = inputs.board, inputs.history
    new_board = try_move(board, start, stop, history)
    return new_board.is_attacked(stop, history.whose_turn(), history)


def x_marks_the_spot(start, stop, inputs):
    board, history = inputs.board, inputs.history
    return \
        (board.get(start).piece == Piece.PAWN) or \
        board.capture(start, stop, history) or \
        stop.rank().to_index() == stop.file().to_index() or \
        stop.rank().flip().to_index() == stop.file().to_index()


def flight_over_fight(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if history.last_move() and history.last_move().capture:
        return stop.rank().less_adv_than(start.rank(), history.whose_turn())
    else:
        return True


def helicopter_parent(start, stop, inputs):
    return sum(inputs.history.pieces_captured(inputs.history.whose_turn().other()).values()) < 3


def deer_in_the_headlights(start, stop, inputs):
    return not inputs.board.is_attacked(start, inputs.history.whose_turn().other(), inputs.history)


def impulsive(start, stop, inputs):
    board, history = inputs.board, inputs.history
    c = history.whose_turn()
    for s in Square:
        if board.get(s) and board.get(s).color == c:
            mvs = [Square(x) for x in board.legal_moves(s, history, c)]
            if [m for m in mvs if board.capture(s, m, history)]:
                return board.capture(start, stop, history)
    return True


def spread_out(start, stop, inputs):
    board, history = inputs.board, inputs.history
    return not [sq for sq in get_adjacent_squares(stop) if board.get(sq) and board.get(sq).color == history.whose_turn() and sq != start]


def left_to_right(start, stop, inputs):
    board, history = inputs.board, inputs.history
    c = history.whose_turn()
    if len(history.history) > 1:
        last_file = history.history[-2].stop.file()
        if last_file == File.H and c == Color.WHITE \
                or last_file == File.A and c == Color.BLACK:
            return True
        else:
            return last_file.more_left_than(stop.file(), c)
    else:
        return True


def leaps_and_bounds(start, stop, inputs):
    return not start.is_adjacent(stop)

# Not finished


def hold_them_back(start, stop, inputs):
    board, history = inputs.board, inputs.history
    c = history.whose_turn()
    if c == Color.WHITE:
        our_side = [s for s in Square if s.rank().less_adv_than(Rank.Fifth, c)]
    else:
        our_side = [s for s in Square if s.rank(
        ).less_adv_than(Rank.Fourth, c)]
    return not [s for s in our_side if board.get(s) and board.get(s).piece == Piece.PAWN and board.get(s).color != c]


def xray_defense(start, stop, inputs):
    board, history = inputs.board, inputs.history
    c = history.whose_turn()
    king_sq = board.loc_singleton(ColoredPiece(c, Piece.KING))
    for s in Square:
        if board.get(s) and board.get(s).color == c.other():
            new_board = empty_board()
            new_board.set(s, board.get(s))
            if new_board.is_attacked(king_sq, c.other(), history):
                return False
    return True


def outcast(start, stop, inputs):
    return stop.rank() not in [Rank.Fourth, Rank.Fifth] and stop.file() not in [File.D, File.E]


def final_countdown(start, stop, inputs):
    return len(inputs.history.history) < 18


def lead_by_example(start, stop, inputs):
    board = inputs.board
    c = inputs.history.whose_turn()
    king_pos = board.cache.kings[c]
    if not king_pos:
        return True
    if board.get(start).piece in [Piece.KING, Piece.PAWN]:
        return True
    return stop.rank().less_adv_than_or_equal(king_pos.rank(), c)


def knight_errant(start, stop, inputs):
    board = inputs.board
    return board.get(start).piece == Piece.KNIGHT or [sq for sq in get_adjacent_squares(start) if board.get(sq) and board.get(sq).piece == Piece.KNIGHT]


def slippery(start, stop, inputs):
    board = inputs.board
    max_distance = max([sq.distance(start) for sq in Square if sq.value in board.legal_moves(
        start, inputs.history, inputs.history.whose_turn())])
    return start.distance(stop) == max_distance


def monkey_see(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if board.capture(start, stop, history):
        return board.get(start).piece in history.pieces_captured_with(history.whose_turn().other())
    return True


def rook_buddies(start, stop, inputs):
    if inputs.board.get(start).piece == Piece.ROOK:
        return inputs.board.cache.rooks_have_connected[inputs.history.whose_turn()]
    return True


def stop_stalling(start, stop, inputs):
    return not start.rank() == stop.rank()


def remorseful(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if board.capture(start, stop, history) and (last_move := history.last_move(history.whose_turn())):
        return not last_move.capture
    return True


def get_down_mr_president(start, stop, inputs):
    board, history = inputs.board, inputs.history
    king_pos = board.cache.kings[history.whose_turn()]
    if not king_pos:
        return True
    if board.is_attacked(king_pos, history.whose_turn().other(), history):
        return board.get(start).piece != Piece.KING
    return True


def bottled_lightning(start, stop, inputs):
    board, history = inputs.board, inputs.history
    king_pos = board.cache.kings[history.whose_turn()]
    if not king_pos:
        return True
    return board.get(start).piece == Piece.KING or not board.legal_moves(king_pos, history, history.whose_turn())


def pilgrimage(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if (captured_piece := board.capture(start, stop, history)) and captured_piece.piece not in [Piece.KING, Piece.PAWN]:
        return board.cache.king_has_reached_last_rank[history.whose_turn()]
    return True


def leveling_up(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if (captured_piece := board.capture(start, stop, history)):
        pieces_captured = history.pieces_captured()
        if captured_piece.piece not in pieces_captured and captured_piece.piece not in [Piece.PAWN]:
            return {
                Piece.KNIGHT: Piece.PAWN,
                Piece.BISHOP: Piece.KNIGHT,
                Piece.ROOK: Piece.BISHOP,
                Piece.QUEEN: Piece.ROOK,
                Piece.KING: Piece.QUEEN
            }[captured_piece.piece] in pieces_captured
    return True


def flatterer(start, stop, inputs):
    board, history = inputs.board, inputs.history
    last_move = history.last_move()
    if not last_move:
        return True
    target_square = Square.of_rank_and_file(
        last_move.stop.rank().flip(), last_move.stop.file())
    piece = last_move.piece.piece
    for square in board.loc(ColoredPiece(history.whose_turn(), piece)):
        if target_square.value in board.legal_moves(square, history, history.whose_turn()):
            return stop == target_square and board.get(start).piece == piece
    return True


# Comment so I can search for the bottom of the handicaps


# number is how bad the handicap is, 1-10
# capture-based handicaps are maybe all broken with enpassant(s)
tested_handicaps = {
    "Simp: Lose if you have no queen": (lose_if_no_queen, 7),
    "Skittish: While in check, you must move your king": (skittish, 2),
    "Bongcloud: When your king is on the back rank, you can only move pawns and kings": (bongcloud, 2),
    "Home Base: Can't move to opponent's side of board": (cant_move_to_opponents_side_of_board, 5),
    "Unlucky: Can't move to half of squares, re-randomized every move": (cant_move_to_half_of_squares_at_random, 5),
    "Colorblind: Can't move to squares of one color, re-randomized every move": (cant_move_to_one_color_at_random, 5),
    "Flavor of the month: Must move a specific piece type, re-randomized every move": (must_move_specific_piece_type_at_random, 8),
    "Peons First: Can't move pieces that are directly behind one of your pawns": (peons_first, 2),
    "True Gentleman: You cannot capture your opponent's queen": (true_gentleman, 2),
    "Forward March: Your pieces cannot move backwards": (forward_march, 4),
    "Hipster: You can't move a piece of the same type your opponent just moved": (hipster, 2),
    "Stoic: You can't move your king": (stoic, 2),
    "Conscientious Objectors: Your pawns can't capture": (conscientious_objectors, 3),
    "Outflanked: You can't capture on the rim": (outflanked, 1),
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
    "Hedonic Treadmill: You must move a piece at least as valuable as your opponent’s last moved piece": (hedonic_treadmill, 6),
    "Spice of Life: You can't move the same piece type twice in a row": (spice_of_life, 3),
    "Simon Says: You must move onto the same color square as your opponent's last move": (simon_says, 5),
    "Hopscotch: You must alternate moving to white and black squares": (hopscotch, 5),
    "Going the Distance: You must move as least as far (manhattan distance) as your opponent's last move": (going_the_distance, 5),
    "Closed book: You lose if there is ever an open file": (closed_book, 7),
    "Cage the King: If your opponent's king leaves its starting rank, you lose": (cage_the_king, 5),
    "Inside the Lines: You cannot move onto the edge of the board": (inside_the_lines, 4),
    "Taking Turns: All of your piece types have to have moved an amount of times that are within 1 of each other": (taking_turns, 5),
    "Left for Dead: You can only capture to the left": (left_for_dead, 6),
    "Follow the shadow: When your opponent moves from square A to square B, you must move to square A if possible": (follow_the_shadow, 7),
    "Out in Front: You can only move the most advanced piece in every file": (out_in_front, 6),
    "Abstinence: If your opponent ever has two non-pawn pieces of the same type adjacent to each other, you lose": (abstinence, 6),
    "Flanking attack: You can only capture from rim": (flanking_attack, 6),
    "Element of Surprise: Only capture each piece type once": (only_capture_each_piece_type_once, 5),
    "Your Own Size: Pieces can only take pieces of the same type (anything can take King)": (your_own_size, 7),
    "Ego Clash: You can never have two non-pawns on the same file": (ego_clash, 7),
    "In Mourning: You cannot move pieces of the same type as one that you have captured": (in_mourning, 8),
    "Cowering in Fear: You cannot move a piece of less value than one your opponent has taken": (cowering_in_fear, 7),
    "Yin and Yang: Capturing moves must occur on black squares. Non-capturing moves must occur on white squares": (yin_and_yang, 9),
    "Color swap: When you move a piece, the destination square and starting square must be different colors": (color_swap, 9),
    "Eat your vegetables: You must take all your opponent's pawns before taking any non-pawn piece": (eat_your_vegetables, 8),
    "Chain of command: Unless you just moved your king, you cannot move a less valuable piece than last move": (chain_of_command, 7),
    "Pioneer: You cannot move onto a rank that you already occupy": (pioneer, 9),
    "X Marks the Spot: Any non-pawn, non-capture moves must be to one of the long diagonals": (x_marks_the_spot, 8),
    "Flight over Flight: When your opponent captures, you must move backwards": (flight_over_fight, 9),
    "Helicopter parent: You lose if your opponents capture 3 of your pieces": (helicopter_parent, 8),
    "Deer in the headlights: Your pieces under attack can't move": (deer_in_the_headlights, 8),
    "Impulsive: If you can capture something, you must": (impulsive, 7),
    "Spread Out: You cannot move a pieces next to another one of your pieces": (spread_out, 8),
    "Left to Right: Unless you just moved to the rightmost file, you must move further to the right than where you last moved": (left_to_right, 7),
    "Leaps and Bounds: You cannot move a pieces adjacent to where it was": (leaps_and_bounds, 8),
    "Friendly Fire: You can only move onto squares defended by another one of your pieces": (friendly_fire, 7),
    "Hold them Back: If your opponent moves a pawn onto your side of the board, you lose": (hold_them_back, 8),
    "X-ray defense: If an opposing piece would be attacking your king on an otherwise empty board, you lose": (xray_defense, 7),
    "Outcast: You can't move into the middle two ranks and files": (outcast, 7),
    "Final Countdown: At the start of move 10, you lose the game": (final_countdown, 8),
    "Lead by example: You can't move a non-pawn, non-king piece to a rank ahead of your king": (lead_by_example, 8),
    "Knight errant: You can only move knights and pieces adjacent to knights": (knight_errant, 7),
    "Slippery: You can't move a piece less far than it could move": (slippery, 7),
    "Monkey see: You can't capture with pieces that your opponent hasn't captured with yet": (monkey_see, 7),
    "Rook buddies: You can't move your rooks until you've connected them": (rook_buddies, 4),
    "Stop stalling: Your pieces can't move laterally": (stop_stalling, 3),
    "Remorseful: You can't capture twice in a row": (remorseful, 4),
    "Get down Mr. President: You can't move your king when in check": (get_down_mr_president, 5),
    "Bottled lightning: If you can move your king, you must": (bottled_lightning, 8),
    "Pilgrimage: Until your king reached their home row, you can only capture kings and pawns": (pilgrimage, 8),
    "Leveling up: You can't capture a piece until you've captured its predecessor in the list pawn, knight, bishop, rook, queen, king": (leveling_up, 8),
    "Flatterer: If you can mirror your opponent's move, you must (same piece, same stop square reflected over the midline)": (flatterer, 4),
}

# Stuff in here won't randomly get assigned but you can interact with it by changing get_handicaps
# So you can push new handicaps without worrying about breaking the game

# Also for things that are only for testing, e.g. no handicap
untested_handicaps = {
    'No handicap': (no_handicap, 0),
    "No capturing!": (no_captures, 5),
    "Peasant Rebellion: Can't move pawns": (cant_move_pawns, 7),
    "The Loneliest Number: You can only move a pawn once": (loneliest_number, 6),
}

handicaps = dict(tested_handicaps, **untested_handicaps)

descriptions = {v[0]: k for k, v in handicaps.items()}

# theoretical args for some kind of config, e.g. difficulties, elos, idk


# This just checks that none of them throw errors when called
# Doesn't check logic or anything
# Hopefully just catches stupid things like calling piece.piece.piece.piece
# when you wanted piece.piece.piece or whatever
def test_all_handicaps():
    inputs = HandicapInputs(starting_board(), History())
    for v in handicaps.values():
        s1 = random.choice(Rank.Second.squares() +
                           [Square('B1'), Square('G1')])
        s2 = Square(random.choice(inputs.board.legal_moves(
            s1, inputs.history, Color.WHITE)))
        v[0](s1, s2, inputs)


def get_handicaps(x, y):
    # So I can't forget to undo anything weird
    if not LOCAL:
        return random.sample(tested_handicaps.keys(), 2)
    else:
        # This is Gabe's line. For Gabe's use only. Keep out. No girls allowed.
        handicaps.update(untested_handicaps)
        # return random.sample(handicaps.keys(), 2)
        return descriptions[no_handicap], descriptions[no_handicap]
