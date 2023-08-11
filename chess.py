import enum
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

class Board():
    def __init__(self, s):
        for i in range(8):
            for j in range(8):
                self.board[i][j] = Piece(s[i*8+j])

    def get(self, rank, file):
        return self.board[rank][file]

    def set(self, rank, file, piece):
        self.board[rank][file] = piece
    
    def to_string(self):
        return ''.join([str(piece) for piece in self.board])

    starting_board = 'rnbqkbnrpppppppp                                PPPPPPPPRNBQKBNR'

    def of_game_id(game_id):
        return Board(rget('board', game_id=game_id))