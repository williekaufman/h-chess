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
    def __init__(self, piece, start, stop, capture, check, promotion):
        self.piece = piece
        self.start = Square(start)
        self.stop = Square(stop)
        self.capture = capture.lower() == 't'
        self.check = check.lower() == 't'
        self.promotion = promotion

    def validate(self, board, history):
        if self.piece is None:
            return False
        if board.get(self.stop) and board.get(self.start).color == board.get(self.stop).color:
            return False
       # TODO: Implement this
        return True

    def to_string(self):
        return f'{self.piece}{self.start.value}{self.stop.value}{bool_to_char(self.capture)}{bool_to_char(self.check)}{self.promotion}'

    def of_string(s):
        return Move(s[0], s[1:3], s[3:5], s[5], s[6], s[7])

# All this actual logic is untested. It'll be easier to test once we get a UI set up so I'm just gonna wait on that.


def parse_history(history):
    castlingRights = {'K': True, 'Q': True, 'k': True, 'q': True}
    enPassant = []
    d = {'a1': 'Q', 'h1': 'K', 'a8': 'q', 'h8': 'k'}
    if history:
        for move in history:
            if move.piece.piece == Piece.Rook:
                if move.start.value in d:
                    castlingRights[d[move.start.value]] = False
            elif move.piece.piece == Piece.King:
                if move.piece.color == Color.WHITE:
                    castlingRights['K'] = False
                    castlingRights['Q'] = False
                else:
                    castlingRights['k'] = False
                    castlingRights['q'] = False
        most_recent_move = history[-1]
        if most_recent_move.piece.piece == Piece.PAWN and abs(most_recent_move.start.to_coordinates()[0] - most_recent_move.stop.to_coordinates()[0]) == 2:
            dir = 1 if most_recent_move.piece.color == Color.WHITE else -1
            enPassant.append(most_recent_move.stop.shift(dir, 0))
    return {'castlingRights': castlingRights, 'enPassant': enPassant}

# Ranks and files go from 0 to 7, not 1 to 8. Don't get tricked.

def filter_candidates(candidates, board, color):
    return [c for c in candidates if c and (not board.get(c) or board.get(c).color != color)]

# Pawn logic totally ignores promotion
def pawn_captures(board, square, color):
    dir = 1 if color == Color.WHITE else -1
    candidates = [square.shift(dir, -1), square.shift(dir, 1)]
    return [c for c in candidates if c and board.get(c) and board.get(c).color != color]

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
    print(bishop_moves(board, square, color))
    print(rook_moves(board, square, color))
    return bishop_moves(board, square, color) + rook_moves(board, square, color)

# This ignores castling
def king_moves(board, square, color):
    candidates = []
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

    def move(self, start, stop, history=None, promote_to=Piece.QUEEN):
        piece = self.get(start)
        capture = 't' if self.get(stop) else 'f'
        # TODO: implement these
        check = 'f'
        castle = 'f'  # use k, q, f
        promotion = promote_to.value if piece and piece.piece == Piece.PAWN and stop.to_coordinates()[
            0] in [0, 7] else 'x'
        move = Move(piece, start, stop, capture, check, promotion)
        if not move.validate(self, history):
            return None
        # TODO: Need to handle things like castling, promotion, en passant
        self.set(start, None)
        self.set(stop, piece)
        return move

    def legal_moves(self, start, whose_turn):
        piece = self.get(start)
        moves = []
        if not piece:
            return moves
        color = piece.color
        if color != (Color.WHITE if whose_turn == 'W' else Color.BLACK):
            return moves
        if piece.piece == Piece.PAWN:
            moves += pawn_moves(self, start, color)
            moves += pawn_captures(self, start, color)
        elif piece.piece == Piece.ROOK:
            moves += rook_moves(self, start, color)
        elif piece.piece == Piece.KNIGHT:
            moves += knight_moves(self, start, color)
        elif piece.piece == Piece.BISHOP:
            moves += bishop_moves(self, start, color)
        elif piece.piece == Piece.QUEEN:
            moves += queen_moves(self, start, color)
        elif piece.piece == Piece.KING:
            moves += king_moves(self, start, color)
        return [square.value for square in moves if square]

    def to_string(self):
        ret = ''
        for i in range(8):
            for j in range(8):
                piece = self.board[i][j]
                ret += ' ' if piece is None else piece.to_string()
        return ret

    def of_game_id(game_id):
        return Board(rget('board', game_id=game_id))


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
