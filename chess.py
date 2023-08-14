from redis_utils import rget
from enum import Enum
from squares import Square

class Piece(Enum):
    PAWN = 'P'
    ROOK = 'R'
    KNIGHT = 'N'
    BISHOP = 'B'
    QUEEN = 'Q'
    KING = 'K'


class Color(Enum):
    WHITE = 'W'
    BLACK = 'B'


class ColoredPiece():
    def __init__(self, color, piece):
        self.color = color
        self.piece = piece

    def to_string(self):
        return self.piece.value if self.color == Color.WHITE else self.piece.value.lower()

    def of_string(s):
        return ColoredPiece(Color.WHITE if s.isupper() else Color.BLACK, Piece(s.upper()))

    def to_string_long(self):
        return f'{self.color.value.lower()}{self.piece.value}'

    def __str__(self):
        return self.to_string()


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
        self.capture = capture.lower() == 't'
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
            ret = [most_recent_move.stop.shift(0, 1 if most_recent_move.stop.to_coordinates()[1] == 2 else -1)]
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


class Board():
    def __init__(self, s):
        self.board = [[None] * 8 for _ in range(8)]
        for i in range(8):
            for j in range(8):
                self.board[i][j] = piece_or_none(s[i*8+j])

    def get(self, square):
        rank, file = square.to_coordinates()
        return self.board[rank][file]

    def set(self, square, piece):
        rank, file = square.to_coordinates()
        self.board[rank][file] = piece

    def move(self, start, stop, whose_turn, handicap, history=None, promote_to=Piece.QUEEN):
        piece = self.get(start)
        extra = []
        if not piece:
            return None, None, 'no piece'
        if piece.color.value != whose_turn:
            return None, None, 'wrong color'
        capture = 't' if self.get(stop) else 'f'
        enPassantSquares = enPassant(history.history)
        kingEnPassantSquares = kingEnPassant(history.history)
        if piece.piece == Piece.PAWN and stop in enPassantSquares:
            capture = 'e'
        if stop in kingEnPassantSquares:
            capture = 'k'
        # TODO check
        check = 'f'
        castle = 'f'
        if piece.piece == Piece.KING and abs(start.to_coordinates()[1] - stop.to_coordinates()[1]) == 2:
            if stop.to_coordinates()[1] == 2:
                castle = 'q'
            else:
                castle = 'k'
        promotion = promote_to.value if piece and piece.piece == Piece.PAWN and stop.to_coordinates()[
            0] in [0, 7] else 'x'
        move = Move(piece, start, stop, capture, check, castle, promotion)
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
            self.set(stop.shift(-1 if piece.color == Color.WHITE else 1, 0), None)
            print(capture)
            extra.append((stop.shift(-1 if piece.color == Color.WHITE else 1, 0).value, ''))
        if capture == 'k':
            self.set(history.history[-1].stop, None)
            extra.append((history.history[-1].stop.value, ''))
        self.set(start, None)
        self.set(stop, piece)
        if promotion != 'x':
            self.set(stop, ColoredPiece(piece.color, Piece(promotion)))
            extra.append((stop.value, f'{piece.color.value.lower()}{promotion}'))
        return move, extra, None

    def legal_moves(self, start, history, whose_turn, handicap=None):
        piece = self.get(start)
        moves = []
        if not piece:
            return moves
        color = piece.color
        if color != (Color.WHITE if whose_turn == 'W' else Color.BLACK):
            return moves
        if piece.piece == Piece.PAWN:
            moves += pawn_moves(self, start, color)
            moves += pawn_captures(self, start, color, history.history)
        elif piece.piece == Piece.ROOK:
            moves += rook_moves(self, start, color)
        elif piece.piece == Piece.KNIGHT:
            moves += knight_moves(self, start, color)
        elif piece.piece == Piece.BISHOP:
            moves += bishop_moves(self, start, color)
        elif piece.piece == Piece.QUEEN:
            moves += queen_moves(self, start, color)
        elif piece.piece == Piece.KING:
            moves += king_moves(self, start, color, history.history)
        handicap = handicap or (lambda board, start, stop, history: True)
        return [square.value for square in moves if square and handicap(self, start, square, history.history)]

    def game_over(self, whose_turn, history, handicap=None):
        color = Color.WHITE if whose_turn == 'W' else Color.BLACK
        has_king, has_move = False, False
        for square in Square:
            piece = self.get(square)
            if not piece:
                continue
            if piece.color == color and piece.piece == Piece.KING:
                has_king = True
            if piece.color == color and self.legal_moves(square, history, whose_turn, handicap):
                has_move = True
            if has_move and has_king:
                return False
        return True

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
        if (board := rget('board', game_id=game_id)):
            return Board(board)
        return None


empty_rank = ' ' * 8

starting_board = Board(
    'RNBQKBNR' +
    'PPPPPPPP' +
    empty_rank * 4 +
    'pppppppp' +
    'rnbqkbnr'
)


class History():
    def __init__(self, s=''):
        if not s:
            self.history = []
        else:
            self.history = [Move.of_string(move) for move in s.split('|')]

    def add(self, move):
        self.history.append(move)

    def to_string(self):
        return '|'.join([move.to_string() for move in self.history])

    def of_game_id(game_id):
        return History(rget('history', game_id=game_id))