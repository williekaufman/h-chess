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

    def validate(self):
        # TODO: Implement this
        return True

    def to_string(self):
        return f'{self.piece}{self.start.value}{self.stop.value}{bool_to_char(self.capture)}{bool_to_char(self.check)}{self.promotion}'
    
    def of_string(s):
        return Move(s[0], s[1:3], s[3:5], s[5], s[6], s[7])

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

    def move(self, start, stop, promote_to=Piece.QUEEN):
        piece = self.get(start)
        capture = 't' if self.get(stop) else 'f'
        # TODO: implement this
        check = 'f'
        promotion = promote_to.value if piece and piece.piece == Piece.PAWN and stop.to_coordinates()[0] in [0, 7] else 'x'
        move = Move(piece, start, stop, capture, check, promotion)
        if not move.validate():
            return None
        self.set(start, None)
        self.set(stop, piece)
        return move 

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