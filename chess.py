from enum import Enum
from redis_utils import rget

class Piece(Enum):
    PAWN_W = 'P'
    ROOK_W = 'R'
    KNIGHT_W = 'N'
    BISHOP_W = 'B'
    QUEEN_W = 'Q'
    KING_W = 'K'
    PAWN_B = 'p'
    ROOK_B = 'r'
    KNIGHT_B = 'n'
    BISHOP_B = 'b'
    QUEEN_B = 'q'
    KING_B = 'k'

def piece_or_none(s):
    if s == ' ':
        return None
    return Piece(s)

class Move():
    def __init__(self, piece, start, stop, capture, check, promotion):
        self.piece = piece
        self.start = start
        self.stop = stop
        self.capture = capture
        self.check = check
        self.promotion = promotion

    def validate(self):
        # TODO: Implement this
        return True

    def to_str(self):
        return f'{self.piece}{self.start}{self.stop}{self.capture}{self.check}{self.promotion}'
    
    def of_str(s):
        return Move(s[0], s[1:3], s[3:5], s[5], s[6], s[7])

class Board():
    def __init__(self, s):
        for i in range(8):
            for j in range(8):
                self.board[i][j] = piece_or_none(s[i*8+j])

    def get(self, rank, file):
        return self.board[rank][file]

    def set(self, rank, file, piece):
        self.board[rank][file] = piece

    def move(self, start, stop): 
        piece = self.get(start[0], start[1])
        capture = self.get(stop[0], stop[1])
        # TODO: implement this
        check = False
        promotion = piece in [Piece.PAWN_W, Piece.PAWN_B] and stop[0] in [0, 7]
        self.set(start[0], start[1], ' ')
        self.set(stop[0], stop[1], piece)
        return Move(piece, start, stop, capture, check, promotion) 

    empty_rank = ' ' * 8

    starting_board = ['rnbqkbnr',
                      'pppppppp',
                      empty_rank,
                      empty_rank,
                      empty_rank,
                      empty_rank,
                      'PPPPPPPP',
                      'RNBQKBNR']

    def to_string(self):
        return ''.join([str(piece) for piece in self.board])

    def of_game_id(game_id):
        return Board(rget('board', game_id=game_id))

class History():
    def __init__(self):
        self.history = []

    def add(self, move):
        self.history.append(move)

    def to_string(self):
        return '|'.join([str(move) for move in self.history])

    def of_game_id(game_id):
        return History(rget('history', game_id=game_id))