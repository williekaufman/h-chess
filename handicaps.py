from redis_utils import rset, rget
from squares import Square, Rank, File
from chess import Color, Piece, ColoredPiece, HandicapInputs, starting_board, empty_board, History, CaptureType, queen_moved_like
from settings import LOCAL
from helpers import toast, whiteboard, try_move, get_adjacent_squares, get_orthogonally_adjacent_squares, get_diagonally_adjacent_squares, two_letter_words, try_opt, whiteboardify_pieces 
from enum import Enum
from collections import defaultdict, Counter
import random

def lookup_handicap(game_id, color):
    assert color in Color
    return handicaps[rget(f'{color.value}_handicap', game_id=game_id)][0]

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

def number_of_the_beast(start, stop, inputs):
    return stop.rank != Rank.Sixth

def checkers(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if board.capture(start, stop, history):
        return stop.rank().more_adv_than(start.rank(), history.whose_turn())
    return True

def queen_disguise(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if board.get(start).piece != Piece.QUEEN:
        return True
    if (disguise := board.cache.queen_disguise[history.whose_turn()]):
        return queen_moved_like(start, stop) == disguise
    return True

def blood_scent(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if board.capture(start, stop, history):
        return True
    for square in board.legal_moves(start, history, history.whose_turn()):
        if board.capture(start, Square(square), history):
            return False
    return True

def nurturer(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if (captured_piece := board.capture(start, stop, history)):
        return captured_piece.piece != Piece.KING or board.cache.has_promoted[history.whose_turn()]
    return True 

def lose_if_no_queen(start, stop, inputs):
    board, history = inputs.board, inputs.history
    return board.loc(ColoredPiece(history.whose_turn(), Piece.QUEEN))

def h_file_phobe(start, stop, inputs):
    return stop.file() != File.H

def respectful(start, stop, inputs):
    board, history, promote_to = inputs.board, inputs.history, inputs.promote_to
    if board.is_attacked(board.cache.kings[history.whose_turn().other()], history.whose_turn(), history):
        return True
    new_board = try_move(board, start, stop, history, promote_to)
    return not new_board.is_attacked(board.cache.kings[history.whose_turn().other()], history.whose_turn(), history)

def skittish(start, stop, inputs):
    board, history = inputs.board, inputs.history
    king_sq = board.cache.kings[history.whose_turn()]
    return king_sq and not board.is_attacked(king_sq, history.whose_turn().other(), history) or board.get(start).piece == Piece.KING 


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
    board, history = inputs.board, inputs.history
    color = Color.WHITE if board.cache.rand > 0.5 else Color.BLACK
    try_opt(
        history.whose_turn(),
        board.game_id,
        lambda : whiteboard(f'Must move to a {color.value.lower()} square', history.whose_turn(), inputs.board.game_id),
    )
    return stop.color() == color

def cant_move_specific_piece_type_at_random(start, stop, inputs):
    board, history = inputs.board, inputs.history
    random.seed(board.cache.rand)
    has_legal_moves = {p: False for p in Piece}
    for square in Square:
        if board.get(square) and board.get(square).color == inputs.history.whose_turn():
            if board.legal_moves(square, inputs.history, inputs.history.whose_turn()):
                has_legal_moves[board.get(square).piece] = True
    pieces = [p for p in has_legal_moves.keys() if has_legal_moves[p]]
    if not pieces:
        return False
    if len(pieces) == 1:
        return True
    piece = random.choice(pieces)
    try_opt(
        history.whose_turn(),
        board.game_id,
        lambda : whiteboard(f'Can\'t move a {piece.name.lower()}', history.whose_turn(), board.game_id),
        )
    return board.get(start).piece != piece

def must_move_specific_piece_type_at_random(start, stop, inputs):
    board, history = inputs.board, inputs.history
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
    try_opt(
        history.whose_turn(),
        board.game_id,
        lambda : whiteboard(f'Must move a {piece.name.lower()}', history.whose_turn(), board.game_id),
        )
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
    return not (board.get(start).piece == Piece.PAWN and board.capture(start, stop, history))


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
    board, history, promote_to = inputs.board, inputs.history, inputs.promote_to
    if board.get(start).piece != Piece.PAWN:
        return True
    new_board = try_move(board, start, stop, history, promote_to)
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
        try_opt(
            history.whose_turn(),
            board.game_id,
            lambda : whiteboard(f"Can't move a {last_move.piece.piece.name.lower()}", history.whose_turn(), board.game_id),
            )
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
        try_opt(
            history.whose_turn(),
            inputs.board.game_id,
            lambda : whiteboard(f"Must move to a {last_move.stop.color().other().value.lower()} square", history.whose_turn(), inputs.board.game_id),
        )
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
    piece_counter = {p: piece_counter[p] for p in piece_counter if inputs.board.loc(ColoredPiece(inputs.history.whose_turn(), p))}
    can_move = str([p.value for p in piece_counter.keys() if piece_counter[p] == min(piece_counter.values())]).replace("'", "")
    try_opt(
        inputs.history.whose_turn(),
        inputs.board.game_id,
        lambda : whiteboard(f'Can move: {can_move}', inputs.history.whose_turn(), inputs.board.game_id),
    )
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
    board, history = inputs.board, inputs.history
    pieces_captured = history.pieces_captured()
    whiteboard_str = whiteboardify_pieces(pieces_captured.keys())
    pieces_captured and try_opt(
        history.whose_turn(),
        board.game_id,
        lambda : whiteboard(f'Captured: {whiteboard_str}', history.whose_turn(), board.game_id),
    )
    return inputs.board.get(start).piece not in inputs.history.pieces_captured()


def cowering_in_fear(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if (pieces_captured := history.pieces_captured(history.whose_turn().other())):
        min_points_to_move = max([piece.points() for piece in pieces_captured.keys()])
        whiteboard_str = whiteboardify_pieces([p for p in Piece if p.points() >= min_points_to_move])
        pieces_captured and try_opt(
            history.whose_turn(),
            board.game_id,
            lambda : whiteboard(f'Can move: {whiteboard_str}', history.whose_turn(), board.game_id),
        )
        return board.get(start).piece.points() >= min_points_to_move
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
    if (last_move := history.last_move(history.whose_turn())):
        last_piece = last_move.piece.piece
        try_opt(
            history.whose_turn(),
            board.game_id,
            lambda : whiteboard(f'Last piece was {last_piece.name.lower()}', history.whose_turn(), board.game_id),
        )
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

def octomom(start, stop, inputs):
    return sum(inputs.history.pieces_captured(inputs.history.whose_turn().other()).values()) < 8

def deer_in_the_headlights(start, stop, inputs):
    return not inputs.board.is_attacked(start, inputs.history.whose_turn().other(), inputs.history)


def impulsive(start, stop, inputs):
    board, history = inputs.board, inputs.history
    c = history.whose_turn()
    for s in Square:
        if board.get(s) and board.get(s).color == c:
            mvs = [Square(x) for x in board.legal_moves(s, history, c)]
            if [m for m in mvs if board.capture(s, m, history)]:
                try_opt(
                    c,
                    board.game_id,
                    lambda : whiteboard(f'Must capture', c, board.game_id),
                )
                return board.capture(start, stop, history)
    return True


def spread_out(start, stop, inputs):
    board, history = inputs.board, inputs.history
    return not [sq for sq in get_adjacent_squares(stop) if board.get(sq) and board.get(sq).color == history.whose_turn() and sq != start]


def left_to_right(start, stop, inputs):
    board, history = inputs.board, inputs.history
    c = history.whose_turn()
    if (last_move := history.last_move(history.whose_turn())):
        last_file = last_move.stop.file()
        try_opt(
            c,
            board.game_id,
            lambda: whiteboard(
                f'Last file: {last_file.name}', c, board.game_id),
        )
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
    history = inputs.history
    moves = len(history.player_moves(history.whose_turn()))
    try_opt(
        history.whose_turn(),
        inputs.board.game_id,
        lambda : whiteboard(f'{10 - moves}', history.whose_turn(), inputs.board.game_id),
    )
    return moves < 10


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
    pieces_captured = history.pieces_captured_with(history.whose_turn().other())
    whiteboard_str = whiteboardify_pieces(pieces_captured.keys())
    try_opt(
        history.whose_turn(),
        board.game_id,
        lambda: whiteboard(
            f'Can capture with {whiteboard_str}' if pieces_captured else "Can't capture yet!", history.whose_turn(), board.game_id),
    )
    if board.capture(start, stop, history):
        return board.get(start).piece in pieces_captured
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
    pieces_captured = history.pieces_captured()
    d = {
        Piece.KNIGHT: Piece.PAWN,
        Piece.BISHOP: Piece.KNIGHT,
        Piece.ROOK: Piece.BISHOP,
        Piece.QUEEN: Piece.ROOK,
        Piece.KING: Piece.QUEEN}
    can_capture = [p for p in Piece if p == Piece.PAWN or d[p] in pieces_captured]
    whiteboard_str = whiteboardify_pieces(can_capture) 
    try_opt(
        history.whose_turn(),
        board.game_id,
        lambda: whiteboard(
            f'Can capture {whiteboard_str}', history.whose_turn(), board.game_id),
    ) 
    if (captured_piece := board.capture(start, stop, history)):
        if captured_piece.piece not in pieces_captured and captured_piece.piece not in [Piece.PAWN]:
            return d[captured_piece.piece] in pieces_captured
    return True


def flatterer(start, stop, inputs):
    board, history = inputs.board, inputs.history
    last_move = history.last_move()
    if not last_move:
        return True
    target_square = Square.of_rank_and_file(
        last_move.stop.rank().flip(), last_move.stop.file())
    piece = last_move.piece.piece
    f = lambda board, square: board.get(square) and board.get(square).piece == piece
    if board.can_move_to(target_square, history.whose_turn(), history, f):
        try_opt(
            history.whose_turn(),
            board.game_id,
            lambda: whiteboard(
                f'Must mirror!', history.whose_turn(), board.game_id),
        )
        return stop == target_square and board.get(start).piece == piece
    return True

def covering_fire(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if board.capture(start, stop, history):
        f = lambda board, square: square != start
        return board.is_attacked(stop, history.whose_turn(), history, f)
    return True

def reflective(start, stop, inputs):
    board, history = inputs.board, inputs.history
    if board.get(start).piece == Piece.PAWN:
        return True
    return board.get(stop.flip()) 

def tower_defense(start, stop, inputs):
    board, history = inputs.board, inputs.history
    return board.get(start).piece != Piece.ROOK and board.loc(ColoredPiece(history.whose_turn(), Piece.ROOK))

def bloodthirsty(start, stop, inputs):
    board, history = inputs.board, inputs.history
    player_moves = history.player_moves(inputs.history.whose_turn())
    if len(player_moves) < 5:
        return True
    if not player_moves[-1].capture and not player_moves[-2].capture:
        try_opt(
            history.whose_turn(),
            board.game_id,
            lambda: whiteboard(
                f'Must capture!', history.whose_turn(), board.game_id),
        )
        return board.capture(start, stop, history)
    return True

def scrabble(start, stop, inputs):
    history = inputs.history
    moves = history.player_moves(history.whose_turn())
    if len(moves) == 0:
        try_opt(
            history.whose_turn(),
            inputs.board.game_id,
            lambda: whiteboard(
                "Hint: Don't move to the c or g file on odd-numbered turns"
            )
        )
    if len(moves) % 2 == 0:
        return True
    last_move = history.last_move(history.whose_turn())
    valid_files = [file for file in File if f'{last_move.stop.file().value}{file.value}'.lower() in two_letter_words]
    valid_files_str = str([file.value for file in valid_files]).replace("'", "")
    try_opt(
        history.whose_turn(),
        inputs.board.game_id,
        lambda: whiteboard(
            f'Valid files: {valid_files_str}', history.whose_turn(), inputs.board.game_id),
    )
    return stop.file() in valid_files

def fearless_leader(start, stop, inputs):
    board, history = inputs.board, inputs.history
    c = history.whose_turn()
    k = board.loc_singleton(ColoredPiece(c, Piece.KING))
    pawns_below = [p for p in k.sqs_below(c) if board.get(p) and board.get(p).piece == Piece.PAWN]
    return pawns_below or not board.capture(start, stop, history)

def protect_the_peons(start, stop, inputs):
    board, history = inputs.board, inputs.history
    c = history.whose_turn()
    return not [s for s in board.loc(ColoredPiece(c, Piece.PAWN)) if not board.is_attacked(s, c, history)]

def mind_the_middle(start, stop, inputs):
    board, history, promote_to = inputs.board, inputs.history, inputs.promote_to
    center = [Square('E4'), Square('E5'), Square('D4'), Square('D5')]
    new_board = try_move(board, start, stop, history, promote_to)
    return not [s for s in center if new_board.is_attacked(s, history.whose_turn(), history)]

def monkey_dont(start, stop, inputs):
    h = inputs.history
    c = h.whose_turn()
    ap_moves = h.player_moves(c)
    nap_moves = h.player_moves(c.other())
    if c == Color.BLACK:
        nap_moves = nap_moves[1:]
    n = len([1 for x,y in zip(ap_moves, nap_moves) if x.piece.piece == y.piece.piece])
    most_recent_copy = ap_moves and nap_moves and (ap_moves[-1].piece.piece == nap_moves[-1].piece.piece)
    plural = '' if n == 1 else 's'
    if most_recent_copy:
        try_opt(
            h.whose_turn(),
            inputs.board.game_id,
            lambda: whiteboard(
                f'Your opponent has copied you {n} time{plural}', h.whose_turn(), inputs.board.game_id),
        )
    return n < 3

def femme_fatale(start, stop, inputs):
    board, history = inputs.board, inputs.history
    cap_pc, cap_type = board.capture_outer(start, stop, history)
    return (not cap_pc) or cap_pc.piece != Piece.KING or board.get(start).piece == Piece.QUEEN

def noble_steed(start, stop, inputs):
    board, history = inputs.board, inputs.history
    for knight in board.loc(ColoredPiece(history.whose_turn(), Piece.KNIGHT)):
        if start in get_adjacent_squares(knight) or start == knight:
            return True
    return False

def velociraptor(start, stop, inputs):
    board, history = inputs.board, inputs.history
    opponent_moves = history.player_moves(history.whose_turn().other())
    can_capture = [move.piece.piece for move in opponent_moves[-3:]]
    whiteboard_str = whiteboardify_pieces(can_capture)
    try_opt(
        history.whose_turn(),
        board.game_id,
        lambda: whiteboard(
            f'Can capture: {whiteboard_str}', history.whose_turn(), board.game_id),
    )
    if (captured_piece := board.capture(start, stop, history)):
        return captured_piece.piece in [move.piece.piece for move in opponent_moves[-3:]]
    return True

# Comment so I can search for the bottom of the handicaps


# number is how bad the handicap is, 1-10
tested_handicaps = {
    "Simp: Lose if you have no queen": (lose_if_no_queen, 4),
    "Skittish: While in check, you must move your king": (skittish, 2),
    "Bongcloud: When your king is on the back rank, you can only move pawns and kings": (bongcloud, 2),
    "Home Base: Can't move to opponent's side of board": (cant_move_to_opponents_side_of_board, 5),
    "Unlucky: Can't move to half of squares, re-randomized every move": (cant_move_to_half_of_squares_at_random, 5),
    "Colorblind: Can't move to squares of one color, re-randomized every move": (cant_move_to_one_color_at_random, 5),
    "Gambler: Can't move a specific piece type, re-randomized every move": (cant_move_specific_piece_type_at_random, 3),
    "Flavor of the month: Must move a specific piece type, re-randomized every move": (must_move_specific_piece_type_at_random, 7),
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
    "Flight over fight: When your opponent captures, you must move backwards": (flight_over_fight, 8),
    "Helicopter parent: You lose if your opponent captures 3 of your pieces": (helicopter_parent, 8),
    "Octomom: You lose if your opponent captures 8 of your pieces": (octomom, 3),
    "Deer in the headlights: Your pieces under attack can't move": (deer_in_the_headlights, 8),
    "Impulsive: If you can capture something, you must": (impulsive, 7),
    "Spread Out: You cannot move a pieces next to another one of your pieces": (spread_out, 8),
    "Left to Right: Unless you just moved to the rightmost file, you must move further to the right than where you last moved": (left_to_right, 7),
    "Leaps and Bounds: You cannot move a pieces adjacent to where it was": (leaps_and_bounds, 8),
    "Friendly Fire: You can only move onto squares defended by another one of your pieces": (friendly_fire, 7),
    "Hold them Back: If your opponent moves a pawn onto your side of the board, you lose": (hold_them_back, 8),
    "X-ray defense: If an opposing piece would be attacking your king on an otherwise empty board, you lose": (xray_defense, 7),
    "Outcast: You can't move into the middle two ranks and files": (outcast, 7),
    "Final Countdown: At the end of move 10, you lose the game": (final_countdown, 8),
    "Lead by example: You can't move a non-pawn, non-king piece to a rank ahead of your king": (lead_by_example, 8),
    "Knight errant: You can only move knights and pieces adjacent to knights": (knight_errant, 7),
    "Slippery: You can't move a piece less far than it could move": (slippery, 6),
    "Monkey see: You can't capture with pieces that your opponent hasn't captured with yet": (monkey_see, 7),
    "Rook buddies: You can't move your rooks until you've connected them": (rook_buddies, 3),
    "Stop stalling: Your pieces can't move laterally": (stop_stalling, 3),
    "Remorseful: You can't capture twice in a row": (remorseful, 4),
    "Get down Mr. President: You can't move your king when in check": (get_down_mr_president, 5),
    "Bottled lightning: If you can move your king, you must": (bottled_lightning, 8),
    "Pilgrimage: Until your king reaches their home row, you can only capture kings and pawns": (pilgrimage, 8),
    "Leveling up: You can't capture a piece until you've captured its predecessor in the list [pawn, knight, bishop, rook, queen, king]": (leveling_up, 6),
    "Covering fire: You can only capture a piece if you could capture it two different ways": (covering_fire, 6),
    "Reflective: You can only move non-pawns to squares whose opposite square reflected across the center line is occupied": (reflective, 6),
    "Tower Defense: You can't move your rooks. If you lose all your rooks, you lose": (tower_defense, 7),
    "Bloodthirsty: After the first 3 turns, if you go 2 turns without capturing, you must capture on the third (or lose)": (bloodthirsty, 5),
    "The scent of blood: You can't make non-capturing moves with pieces that could capture": (blood_scent, 3),
    "Nurturer: You can't capture their king until you've promoted a pawn": (nurturer, 3), 
    "Fearless Leader: You can only capture when your king is in front of one of your pawns": (fearless_leader, 8),
    "Protect the Peons: You lose if you have an undefended pawn": (protect_the_peons, 8), 
    "Mind the Middle: You can't attack the central four squares": (mind_the_middle, 9),
    "Femme Fatale: Only your queen can take their king": (femme_fatale, 3),
    "H-phile: You can't move to the h file": (h_file_phobe, 3),
    "The number of the beast: You can't move onto the sixth rank": (number_of_the_beast, 3),
    "Respectful: Can't give check": (respectful, 4),
    "Checkers: You can only capture forward": (checkers, 4),
    "Disguised queen: Your queen is secretly either a bishop or a rook. Once you move it like one, you can't move it like the other": (queen_disguise, 2),
    "Noble steed: Your non-Knight pieces can only move if they're next to one of your knights": (noble_steed, 8),
    "Velociraptor: You can only capture a piece if your opponent has moved a piece of that type in the last 3 moves": (velociraptor, 4),
}

white_only_handicaps = {}
    
black_only_handicaps = {}

# Stuff in here won't randomly get assigned but you can interact with it by changing get_handicaps
# So you can push new handicaps without worrying about breaking the game

# Also for things that are only for testing, e.g. no handicap
untested_handicaps = {
    'No handicap': (no_handicap, 0),
    "No capturing!": (no_captures, 5),
    "Peasant Rebellion: Can't move pawns": (cant_move_pawns, 7),
    "The Loneliest Number: You can only move a pawn once": (loneliest_number, 6),
    # It turns out this is quite close to "you have to move to the a or e file on even numbered turns". Kinda lame
    "Scrabble: For each pair of moves, the files that your piece stops on must spell a 2-letter word. E.g. you could do H file, A file (ha) and then B file, E file (be) for your first 4 moves.": (scrabble, 7),
    "Monkey Don't: If your opponent moves the same piece as you just moved 3 times over the course of the game, you lose": (monkey_dont, 9),
    # We played a playtest game and it was stupid
    "Flatterer: If you can mirror your opponent's move, you must (same piece, same stop square reflected over the midline)": (flatterer, 4),
}

handicaps = dict(tested_handicaps, **untested_handicaps)

descriptions = {v[0]: k for k, v in handicaps.items()}

class Difficulty(Enum):
    NONE = 'none'
    EASY = 'easy'
    MEDIUM = 'medium'
    HARD = 'hard'

    def offset(self):
        if self == Difficulty.NONE:
            return 0
        if self == Difficulty.EASY:
            return 1
        elif self == Difficulty.MEDIUM:
            return 4
        else:
            return 7
    
    def of_number(n):
        if n == 0:
            return Difficulty.NONE
        if n < 4:
            return Difficulty.EASY
        elif n < 7:
            return Difficulty.MEDIUM
        else:
            return Difficulty.HARD

def pick_handicap(difficulty, color):
    relevant_handicaps = tested_handicaps
    relevant_handicaps.update(white_only_handicaps if color == Color.WHITE else black_only_handicaps)
    if not difficulty:
        return "No handicap"
    n = random.choice([0, 0, 1, 1, 1, 1, 2, 2]) + difficulty.offset()
    if (handicaps := [k for k, v in relevant_handicaps.items() if v[1] == n]):
        return random.choice(handicaps)
    # This shouldn't really be happening
    print('No handicap found for difficulty', difficulty)
    return "No handicap"

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


def get_handicaps(config):
    # So I can't forget to undo anything weird
    if not LOCAL:
        return [pick_handicap(config[color], color) for color in Color]
    else:
        return [pick_handicap(config[color], color) for color in Color]
        # return descriptions[queen_disguise], descriptions[no_handicap]

