import copy
import random
from redis_utils import rget, rset
from enum import Enum
from color import Color, Result
from squares import Square, Rank, File
from helpers import toast, whiteboard
from collections import Counter
import json
import math

class Piece(Enum):
    PAWN = 'P'
    ROOK = 'R'
    KNIGHT = 'N'
    BISHOP = 'B'
    QUEEN = 'Q'
    KING = 'K'

    def points(self):
        return {
            Piece.PAWN: 1,
            Piece.ROOK: 5,
            Piece.KNIGHT: 3,
            Piece.BISHOP: 3,
            Piece.QUEEN: 9,
            Piece.KING: math.inf
        }[self]

class ColoredPiece():
    def __init__(self, color, piece):
        self.color = color
        self.piece = piece

    def equals(self, other):
        return self.color == other.color and self.piece == other.piece

    def points(self):
        return self.piece.points()

    def to_string(self):
        return self.piece.value if self.color == Color.WHITE else self.piece.value.lower()

    def of_string(s):
        return ColoredPiece(Color.WHITE if s.isupper() else Color.BLACK, Piece(s.upper()))

    def to_string_long(self):
        return f'{self.color.value[0].lower()}{self.piece.value}'

    def __str__(self):
        return self.to_string()


def piece_or_none(s):
    if s == ' ':
        return None
    return ColoredPiece.of_string(s)


def bool_to_char(b):
    return 't' if b else 'f'

class Move():
    def __init__(self, piece, start, stop, capture, check, castle, promotion, capture_type):
        self.piece = piece
        self.start = Square(start)
        self.stop = Square(stop)
        self.capture = capture
        self.check = check.lower() == 't'
        self.castle = castle
        self.promotion = promotion
        self.capture_type = CaptureType(capture_type)

    def validate(self, board, history, whose_turn, handicap):
        assert type(board) == Board
        assert type(history) == History
        assert type(whose_turn) == Color
        if self.piece is None:
            return False
        if board.get(self.stop) and board.get(self.start).color == board.get(self.stop).color:
            return False
        if self.stop.value not in board.legal_moves(self.start, history, whose_turn, handicap):
            return False
        return True

    def to_string(self):
        return f'{self.piece}{self.start.value}{self.stop.value}{self.capture if self.capture else "f"}{bool_to_char(self.check)}{self.castle}{self.promotion}{self.capture_type.value}'

    def of_string(s):
        return Move(ColoredPiece.of_string(s[0]), s[1:3], s[3:5], None if s[5] == 'f' else ColoredPiece.of_string(s[5]), s[6], s[7], s[8], s[9])

# All this actual logic is untested. It'll be easier to test once we get a UI set up so I'm just gonna wait on that.


def get_castling_rights(history):
    ret = {'K': True, 'Q': True, 'k': True, 'q': True}
    d = {'a1': 'Q', 'h1': 'K', 'a8': 'q', 'h8': 'k'}
    for move in history:
        if move.start.value in d:
            ret[d[move.start.value]] = False
        elif move.piece.piece == Piece.KING:
            if move.piece.color == Color.WHITE:
                ret['K'] = False
                ret['Q'] = False
            else:
                ret['k'] = False
                ret['q'] = False
    return ret


def enPassant(history):
    if history:
        most_recent_move = history[-1]
        if most_recent_move.piece.piece == Piece.PAWN and abs(most_recent_move.start.to_coordinates()[0] - most_recent_move.stop.to_coordinates()[0]) == 2:
            dir = -1 if most_recent_move.piece.color == Color.WHITE else 1
            return [most_recent_move.stop.shift(dir, 0)]
    return []


def kingEnPassant(history):
    if history:
        most_recent_move = history[-1]
        if most_recent_move.castle in ['k', 'q']:
            ret = [most_recent_move.stop.shift(
                0, 1 if most_recent_move.stop.to_coordinates()[1] == 2 else -1)]
            return ret
    return []

# Ranks and files go from 0 to 7, not 1 to 8. Don't get tricked.


def filter_candidates(candidates, board, color):
    return [c for c in candidates if c and (not board.get(c) or board.get(c).color != color)]


def pawn_captures(board, square, color, history):
    enPassantSquares = enPassant(history)
    dir = 1 if color == Color.WHITE else -1
    candidates = [square.shift(dir, -1), square.shift(dir, 1)]
    return [c for c in candidates if c and (board.get(c) and board.get(c).color != color) or c in enPassantSquares]


def pawn_moves(board, square, color):
    rank, file = square.to_coordinates()
    dir = 1 if color == Color.WHITE else -1
    one, two = square.shift(dir, 0), square.shift(2*dir, 0)
    if board.get(one):
        return []
    if rank == 1 and color == Color.WHITE or rank == 6 and color == Color.BLACK:
        if board.get(two):
            return [one]
        return [one, two]
    return [one]


def knight_moves(board, square, color):
    candidates = [square.shift(dr, df) for dr, df in [(
        2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (-1, 2), (1, -2), (-1, -2)]]
    return filter_candidates(candidates, board, color)


def bishop_moves(board, square, color):
    candidates = []
    for i in [1, -1]:
        for j in [1, -1]:
            for k in range(1, 8):
                candidate = square.shift(i*k, j*k)
                if not candidate:
                    break
                if board.get(candidate):
                    candidates.append(candidate)
                    break
                candidates.append(candidate)
    return filter_candidates(candidates, board, color)


def rook_moves(board, square, color):
    candidates = []
    for i in [1, -1]:
        for k in range(1, 8):
            candidate = square.shift(i*k, 0)
            if not candidate:
                break
            if board.get(candidate):
                candidates.append(candidate)
                break
            candidates.append(candidate)
    for j in [1, -1]:
        for k in range(1, 8):
            candidate = square.shift(0, j*k)
            if not candidate:
                break
            if board.get(candidate):
                candidates.append(candidate)
                break
            candidates.append(candidate)
    return filter_candidates(candidates, board, color)


def queen_moves(board, square, color):
    return bishop_moves(board, square, color) + rook_moves(board, square, color)


def king_moves(board, square, color, history):
    candidates = []
    if square == Square('E1') or square == Square('E8'):
        castling_rights = get_castling_rights(history)
        if square == Square('E1') and color == Color.WHITE:
            if castling_rights['K'] and not board.get(Square('F1')) and not board.get(Square('G1')):
                candidates.append(Square('G1'))
            if castling_rights['Q'] and not board.get(Square('D1')) and not board.get(Square('C1')) and not board.get(Square('B1')):
                candidates.append(Square('C1'))
        elif square == Square('E8') and color == Color.BLACK:
            if castling_rights['k'] and not board.get(Square('F8')) and not board.get(Square('G8')):
                candidates.append(Square('G8'))
            if castling_rights['q'] and not board.get(Square('D8')) and not board.get(Square('C8')) and not board.get(Square('B8')):
                candidates.append(Square('C8'))
    for i in [1, 0, -1]:
        for j in [1, 0, -1]:
            if i == 0 and j == 0:
                continue
            candidate = square.shift(i, j)
            if not candidate:
                continue
            if board.get(candidate):
                candidates.append(candidate)
                continue
            candidates.append(candidate)
    return filter_candidates(candidates, board, color)


# Only for colorifying and decolorify cache keys
def decolorify_dict(d):
    return {k.value: v for k, v in d.items()}

def colorify_dict(d):
    return {Color(k): v for k, v in d.items()}

# Any values that we want to cache for calculating handicaps
# Values should only change on a move

# If we want to remember something forever, it should be in Move, but if
# we just might use it many times to check handicaps in a single move, it should be here
class Cache():
    def __init__(self, most_recent_move, kings, rand, rooks_have_connected, king_has_reached_last_rank, reached_positions):
        # Could always just use the History.of_game_id(board.game_id) or whatever but we weren't even getting 
        # the history in /board and this felt easier 
        # Not worth rewriting the handicaps that use history[-1] or whatever though
        self.most_recent_move = most_recent_move
        self.kings = kings
        self.rand = rand
        self.rooks_have_connected = rooks_have_connected
        self.king_has_reached_last_rank = king_has_reached_last_rank
        self.reached_positions = reached_positions

    def dict(self):
        return {
            'most_recent_move': self.most_recent_move.to_string() if self.most_recent_move else None,
            'kings': {k.value: v and v.value for k, v in self.kings.items()},
            'rand': self.rand,
            'rooks_have_connected': decolorify_dict(self.rooks_have_connected),
            'king_has_reached_last_rank': decolorify_dict(self.king_has_reached_last_rank),
            'reached_positions': decolorify_dict(self.reached_positions)
        }
    
    def of_string(s):
        try:
            cache = json.loads(s)
            cache['most_recent_move'] = Move.of_string(cache['most_recent_move']) if cache['most_recent_move'] else None
            cache['kings'] = {Color(k): v and Square(v) for k, v in cache['kings'].items()}
            cache['rooks_have_connected'] = colorify_dict(cache['rooks_have_connected']) 
            cache['king_has_reached_last_rank'] = colorify_dict(cache['king_has_reached_last_rank'])
            cache['reached_positions'] = colorify_dict(cache['reached_positions'])
            return Cache(**cache)
        except:
            return None
        
    def copy(self):
        return Cache(
            self.most_recent_move,
            {k: v for k, v in self.kings.items()},
            self.rand,
            {k: v for k, v in self.rooks_have_connected.items()},
            {k: v for k, v in self.king_has_reached_last_rank.items()},
            {k: {kk: vv for kk, vv in v.items()} for k, v in self.reached_positions.items()}
        )
        
class History():
    def __init__(self, s=''):
        if not s:
            self.history = []
        else:
            self.history = [Move.of_string(move) for move in s.split('|')]

    def whose_turn(self):
        return Color.WHITE if len(self.history) % 2 == 0 else Color.BLACK

    def last_move(self, color=None):
        if color and color == self.whose_turn():
            return self.history[-2] if len(self.history) > 1 else None
        return self.history[-1] if self.history else None

    def player_moves(self, color):
        return [move for move in self.history if move.piece.color == color]
    
    def pieces_moved(self, color=None, include_zero=False):
        color = color or self.whose_turn()
        ret = { p : 0 for p in Piece } if include_zero else {}
        ret.update(Counter([move.piece.piece for move in self.history if move.piece.color == color]))
        return ret

    def pieces_captured(self, color=None, include_zero=False):
        color = color or self.whose_turn() 
        ret = { p : 0 for p in Piece } if include_zero else {}
        ret.update(Counter([move.capture.piece for move in self.history if move.capture and move.piece.color == color]))
        return ret

    def pieces_captured_with(self, color=None, include_zero=False):
        color = color or self.whose_turn()
        ret = { p : 0 for p in Piece } if include_zero else {}
        ret.update(Counter([move.piece.piece for move in self.history if move.capture and move.piece.color == color]))
        return ret

    def add(self, move):
        self.history.append(move)

    def to_string(self):
        return '|'.join([move.to_string() for move in self.history])

    def of_game_id(game_id):
        return History(rget('history', game_id=game_id))

    def to_list(self):
        return [move.to_string() for move in self.history]

class HandicapInputs():
    def __init__(self, board, history):
        self.board = board
        self.history = history

class CaptureType(Enum):
    NOT = 'f'
    NORMAL = 't'
    EN_PASSANT = 'e'
    KING_EN_PASSANT = 'k'

class Board():
    def __init__(self, s, game_id, cache):
        self.cache = cache
        # Game_id should be None if this is a temporary board
        self.game_id = game_id
        self.board = [[None] * 8 for _ in range(8)]
        for i in range(8):
            for j in range(8):
                self.board[i][j] = piece_or_none(s[i*8+j])

    def copy(self):
        return Board(self.to_string(), None, self.cache.copy())

    def loc(self, piece):
        return [square for square in Square if self.get(square) and self.get(square).equals(piece)]

    def loc_singleton(self, piece):
        loc = self.loc(piece)
        if len(loc) != 1:
            return None
        return loc[0]

    def make_cache(self, history, move):
        rooks_have_connected = { c : False for c in Color }
        for c in Color:
            rooks_have_connected[c] = self.cache.rooks_have_connected[c] or rooks_are_connected(self, c)
        kings = {c : self.loc_singleton(ColoredPiece(c, Piece.KING)) for c in Color}
        king_has_reached_last_rank = {c : False for c in Color}
        for c in Color:
            king_has_reached_last_rank[c] = king_has_reached_last_rank[c] or (kings[c] and kings[c].rank() == Rank.home(c.other()))
        # Random is a function of the game_id plus number of moves
        # so you get the same number if you call legal_moves again
        # This could theoretically collide but it never will
        random.seed(int(self.game_id or '0', 16) + len(history.history))
        x = self.cache.reached_positions[history.whose_turn().other()].get(self.to_string(), 0)
        if x == 1 and self.game_id:
            whiteboard(f'Position reached before - one more will be threefold repetition', game_id=self.game_id)
        self.cache.reached_positions[history.whose_turn().other()][self.to_string()] = x + 1
        self.cache = Cache(move, kings, random.random(), rooks_have_connected, king_has_reached_last_rank, self.cache.reached_positions)

    def get(self, square):
        rank, file = square.to_coordinates()
        return self.board[rank][file]

    def set(self, square, piece):
        rank, file = square.to_coordinates()
        self.board[rank][file] = piece

    # tells you whether the given square is attacked by the player of the given color
    # creates a phantom piece of the opposite color in the square to make self.legal_moves work right
    def is_attacked(self, target_square, color, history, filter=lambda board, square: True):
        assert type(target_square) == Square
        assert type(color) == Color
        assert type(history) == History
        new_board = self.copy()
        new_board.set(target_square, ColoredPiece(color.other(), Piece.QUEEN))
        for square in Square:
            if not filter(new_board, square):
                continue
            piece = self.get(square)
            if piece and piece.color == color and target_square.value in new_board.legal_moves(square, history, color):
                return True
        return False

    def can_move_to(self, target_square, color, history, filter=lambda board, square: True):
        assert type(target_square) == Square
        assert type(color) == Color
        assert type(history) == History
        for square in Square:
            if not filter(self, square):
                continue
            piece = self.get(square)
            if piece and piece.color == color and target_square.value in self.legal_moves(square, history, color):
                return True
        return False

    def capture_outer(self, start, stop, history):
        piece = self.get(start)
        ret = None, CaptureType.NOT
        if self.get(stop):
            ret = self.get(stop), CaptureType.NORMAL
        enPassantSquares = enPassant(history.history)
        kingEnPassantSquares = kingEnPassant(history.history)
        if piece.piece == Piece.PAWN and stop in enPassantSquares:
            return ColoredPiece(piece.color.other(), Piece.PAWN), CaptureType.EN_PASSANT
        if stop in kingEnPassantSquares:
            # King en passant always captures a rook
            return ColoredPiece(piece.color.other(), Piece.KING), CaptureType.KING_EN_PASSANT
        return ret

    def capture(self, start, stop, history):
        return self.capture_outer(start, stop, history)[0]

    def move(self, start, stop, whose_turn, handicap, history=History(), promote_to=None):
        assert type(start) == Square
        assert type(stop) == Square
        assert type(whose_turn) == Color
        assert type(history) == History
        piece = self.get(start)
        extra = []
        if not piece:
            return None, None, 'no piece'
        if piece.color != whose_turn:
            return None, None, 'wrong color'
        captured_piece, capture_type = self.capture_outer(start, stop, history)
        # TODO: implement check
        check = 'f'
        castle = 'f'
        if piece.piece == Piece.KING and abs(start.to_coordinates()[1] - stop.to_coordinates()[1]) == 2:
            if stop.to_coordinates()[1] == 2:
                castle = 'q'
            else:
                castle = 'k'
        promotion = promote_to.upper() or 'Q' if piece and piece.piece == Piece.PAWN and stop.to_coordinates()[
            0] in [0, 7] else 'x'
        move = Move(piece, start, stop, captured_piece, check, castle, promotion, capture_type)
        # if this validates, then the move will actually happen
        if not move.validate(self, history, whose_turn, handicap):
            return None, None, 'invalid move'
        if castle == 'k':
            self.set(stop.shift(0, 1), None)
            self.set(stop.shift(0, -1), ColoredPiece(
                Color.WHITE if piece.color == Color.WHITE else Color.BLACK, Piece.ROOK))
            if piece.color == Color.WHITE:
                extra.append(('H1', ''))
                extra.append(('F1', 'wR'))
            else:
                extra.append(('H8', ''))
                extra.append(('F8', 'bR'))
        elif castle == 'q':
            self.set(stop.shift(0, -2), None)
            self.set(stop.shift(0, 1), ColoredPiece(
                Color.WHITE if piece.color == Color.WHITE else Color.BLACK, Piece.ROOK))
            if piece.color == Color.WHITE:
                extra.append(('A1', ''))
                extra.append(('D1', 'wR'))
            else:
                extra.append(('A8', ''))
                extra.append(('D8', 'bR'))
        if capture_type == CaptureType.EN_PASSANT:
            self.set(stop.shift(-1 if piece.color ==
                     Color.WHITE else 1, 0), None)
            extra.append(
                (stop.shift(-1 if piece.color == Color.WHITE else 1, 0).value, ''))
        if capture_type == CaptureType.KING_EN_PASSANT:
            self.set(history.history[-1].stop, None)
            extra.append((history.history[-1].stop.value, ''))
        self.set(start, None)
        self.set(stop, piece)
        if promotion != 'x':
            self.set(stop, ColoredPiece(piece.color, Piece(promotion)))
            extra.append(
                (stop.value, f'{piece.color.value.lower()}{promotion}'))
        # TODO -- check = 't' if the king is in check at the end of the move
        # self.in_check[Color.WHITE] = self.calculate_check apking = self.loc(ColoredPiece(whose_turn, Piece.KING))
        # napking = self.loc(ColoredPiece(whose_turn), Piece.KING)
        check = 'f'
        # This sets all the values that only change on a move
        self.make_cache(history, move)
        return move, extra, None

    def legal_moves(self, start, history, whose_turn, handicap=None):
        assert type(start) == Square
        assert type(history) == History
        assert type(whose_turn) == Color
        piece = self.get(start)
        moves = []
        if not piece:
            return moves
        if piece.color != whose_turn:
            return moves
        if piece.piece == Piece.PAWN:
            moves += pawn_moves(self, start, whose_turn)
            moves += pawn_captures(self, start, whose_turn, history.history)
        elif piece.piece == Piece.ROOK:
            moves += rook_moves(self, start, whose_turn)
        elif piece.piece == Piece.KNIGHT:
            moves += knight_moves(self, start, whose_turn)
        elif piece.piece == Piece.BISHOP:
            moves += bishop_moves(self, start, whose_turn)
        elif piece.piece == Piece.QUEEN:
            moves += queen_moves(self, start, whose_turn)
        elif piece.piece == Piece.KING:
            moves += king_moves(self, start, whose_turn, history.history) 
        handicap = handicap or (lambda start, stop, inputs: True)
        handicap_inputs = HandicapInputs(self, history)
        return [square.value for square in moves if square and handicap(start, square, handicap_inputs)]

    def draw(self, whose_turn, history):
        if self.cache.reached_positions[whose_turn][self.to_string()] >= 3:
            return Result.THREEFOLD_REPETION
        if len(history.history) > 100:
            moves = history.history[-100:]
            if not any(move.capture for move in moves) and not any(move.piece.piece == Piece.PAWN for move in moves):
                return Result.FIFTY_MOVE_RULE
        if (winner := rget('winner', game_id=self.game_id)):
            try:
                return Result(winner)
            except:
                return False
        return False    

    def winner(self, whose_turn, history, handicap=None):
        has_king, has_move = False, False
        for square in Square:
            piece = self.get(square)
            if not piece or piece.color != whose_turn:
                continue
            if piece.piece == Piece.KING:
                has_king = True
            if self.legal_moves(square, history, whose_turn, handicap):
                has_move = True
            if has_move and has_king:
                return self.draw(whose_turn, history)
        return whose_turn.other()

    def to_string(self):
        ret = ''
        for i in range(8):
            for j in range(8):
                piece = self.board[i][j]
                ret += ' ' if piece is None else piece.to_string()
        return ret

    def to_dict(self):
        d = {}
        for square in Square:
            piece = self.get(square)
            if piece:
                d[square.value.lower()] = piece.to_string_long()
        return d

    def of_game_id(game_id):
        cache = Cache.of_string(rget('cache', game_id=game_id))
        if (board := rget('board', game_id=game_id)):
            return Board(board, game_id, cache)
        return None

    def write_to_redis(self, game_id=None):
        game_id = game_id or self.game_id
        rset('board', self.to_string(), game_id=game_id)
        rset('cache', json.dumps(self.cache.dict()), game_id=game_id)


empty_rank = ' ' * 8

starting_str = (
    'RNBQKBNR' +
    'PPPPPPPP' +
    empty_rank * 4 +
    'pppppppp' +
    'rnbqkbnr'
)

def starting_cache():
    return Cache(
        None,
        {Color.WHITE: Square('E1'), Color.BLACK: Square('E8')}, 
        random.random(),
        {Color.WHITE: False, Color.BLACK: False},
        {Color.WHITE: False, Color.BLACK: False},
        {Color.WHITE: {starting_str: 1}, Color.BLACK: {}}
        )

def starting_board(game_id=None):
    return Board(
        starting_str, game_id or '0', starting_cache()
    )

def empty_board():
    return Board(
        empty_rank * 8,
        '0', starting_cache()
    )


def rooks_are_connected(board, color):
    rooks = board.loc(ColoredPiece(color, Piece.ROOK))
    for rook1 in rooks:
        for rook2 in rooks:
            if rook1 == rook2:
                continue
            if not [sq for sq in rook1.between(rook2) if board.get(sq)]:
                return True
    return False