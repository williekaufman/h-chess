from enum import Enum
from redis_utils import rget

class Color(Enum):
    WHITE = 'White'
    BLACK = 'Black'

    def other(self):
        return Color.WHITE if self == Color.BLACK else Color.BLACK

    def whose_turn(game_id):
        return Color.WHITE if rget('turn', game_id=game_id) == 'White' else Color.BLACK
    
class Result(Enum):
    WHITE_WINS = 'White'
    BLACK_WINS = 'Black'
    THREEFOLD_REPETION = 'Draw by threefold repetition'
    FIFTY_MOVE_RULE = 'Draw by fifty-move rule'
    AGREEMENT = 'Draw by agreement'