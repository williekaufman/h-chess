from redis_utils import rget, rset
import random
from enum import Enum
from color import Color
from squares import Square
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
        pt_dict = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': math.inf}
        return pt_dict[self.value]


class ColoredPiece():
    def __init__(self, color, piece):
        self.color = color
        self.piece = piece

    def equals(self, other):
        return self.color == other.color and self.piece == other.piece

    def to_string(self):
        return self.piece.value if self.color == Color.WHITE else self.piece.value.lower()

    def of_string(s):
        return ColoredPiece(Color.WHITE if s.isupper() else Color.BLACK, Piece(s.upper()))

    def to_string_long(self):
        return f'{self.color.value[0].lower()}{self.piece.value}'

    def __str__(self):
        return self.to_string()
    
    def points(self):
        return self.piece.points()


def piece_or_none(s):
    if s == ' ':
        return None
    return ColoredPiece.of_string(s)


def bool_to_char(b):
    return 't' if b else 'f'


def char_to_bool(c):
    return c.lower() == 't'


class Move():
    def __init__(self, piece, start, stop, capture, check, castle, promotion):
        self.piece = piece
        self.start = Square(start)
        self.stop = Square(stop)
        self.capture = capture.lower() in ['t', 'k', 'e']
        self.check = check.lower() == 't'
        self.castle = castle
        self.promotion = promotion

    def validate(self, board, history, whose_turn, handicap):
        if self.piece is None:
            return False
        if board.get(self.stop) and board.get(self.start).color == board.get(self.stop).color:
            return False
        if self.stop.value not in board.legal_moves(self.start, history, whose_turn, handicap):
            return False
        return True

    def to_string(self):
        return f'{self.piece}{self.start.value}{self.stop.value}{bool_to_char(self.capture)}{bool_to_char(self.check)}{self.castle}{self.promotion}'

    def of_string(s):
        return Move(ColoredPiece.of_string(s[0]), s[1:3], s[3:5], s[5], s[6], s[7], s[8])

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

# Any values that we want to cache for calculating handicaps
# Values should only change on a move

# It's probably not actually worth caching the king positions
# but just doing it as a test

# If we want to remember something forever, it should be in Move, but if
# we just might use it many times to check handicaps in a single move, it should be here
class Cache():
    def __init__(self, kings, rand):
        self.kings = kings
        self.rand = rand

    def dict(self):
        return {
            'kings': {k.value: v and v.value for k, v in self.kings.items()},
            'rand': self.rand
        }
    
    def of_string(s):
        try:
            cache = json.loads(s)
            cache['kings'] = {Color(k): v and Square(v) for k, v in cache['kings'].items()}
            return Cache(**cache)
        except:
            return None
        
class History():
    def __init__(self, s=''):
        if not s:
            self.history = []
        else:
            self.history = [Move.of_string(move) for move in s.split('|')]

    def whose_turn(self):
        return Color.WHITE if len(self.history) % 2 == 0 else Color.BLACK

    def add(self, move):
        self.history.append(move)

    def to_string(self):
        return '|'.join([move.to_string() for move in self.history])

    def of_game_id(game_id):
        return History(rget('history', game_id=game_id))

    def to_list(self):
        return [move.to_string() for move in self.history]

class HandicapInputs:
    def __init__(self, board, history):
        self.board = board
        self.history = history

class Board():
    def __init__(self, s, game_id, cache):
        self.cache = cache
        self.game_id = game_id
        self.board = [[None] * 8 for _ in range(8)]
        for i in range(8):
            for j in range(8):
                self.board[i][j] = piece_or_none(s[i*8+j])

    def copy(self):
        return Board(self.to_string(), self.game_id, self.cache)

    def loc(self, piece):
        return [square for square in Square if self.get(square) and self.get(square).equals(piece)]

    def loc_singleton(self, piece):
        loc = self.loc(piece)
        if len(loc) != 1:
            return None
        return loc[0]

    def make_cache(self, history):
        kings = {c : self.loc_singleton(ColoredPiece(c, Piece.KING)) for c in Color}
        # Random is a function of the game_id plus number of moves
        # so you get the same number if you call legal_moves again
        # This could theoretically collide but it never will
        random.seed(int(self.game_id, 16) + len(history.history))
        self.cache = Cache(kings, random.random())

    def get(self, square):
        rank, file = square.to_coordinates()
        return self.board[rank][file]

    def set(self, square, piece):
        rank, file = square.to_coordinates()
        self.board[rank][file] = piece

    # tells you whether the given square is attacked by the player of the given color
    # creates a phantom piece of the opposite color in the square to make self.legal_moves work right
    def is_attacked(self, given_square, given_color, history):
        new_board = self.copy()
        new_board.set(given_square, ColoredPiece(given_color.other(), Piece.QUEEN))
        for square in Square:
            piece = self.get(square)
            if piece and piece.color == given_color and given_square.value in new_board.legal_moves(square, history, given_color):
                return True
        return False

    def move(self, start, stop, whose_turn, handicap, history=History(), promote_to=None):
        piece = self.get(start)
        extra = []
        if not piece:
            return None, None, 'no piece'
        if piece.color != whose_turn:
            return None, None, 'wrong color'
        capture = 't' if self.get(stop) else 'f'
        enPassantSquares = enPassant(history.history)
        kingEnPassantSquares = kingEnPassant(history.history)
        if piece.piece == Piece.PAWN and stop in enPassantSquares:
            capture = 'e'
        if stop in kingEnPassantSquares:
            capture = 'k'
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
        move = Move(piece, start, stop, capture, check, castle, promotion)
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
        if capture == 'e':
            self.set(stop.shift(-1 if piece.color ==
                     Color.WHITE else 1, 0), None)
            extra.append(
                (stop.shift(-1 if piece.color == Color.WHITE else 1, 0).value, ''))
        if capture == 'k':
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
        self.make_cache(history)
        return move, extra, None

    def legal_moves(self, start, history, whose_turn, handicap=None):
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
                return False
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

def starting_cache():
    return Cache({Color.WHITE: Square('E1'), Color.BLACK: Square('E8')}, random.random())

def starting_board():
    return Board(
        'RNBQKBNR' +
        'PPPPPPPP' +
        empty_rank * 4 +
        'pppppppp' +
        'rnbqkbnr',
        '0', starting_cache()
    )

