from sockets import socketio
from redis_utils import rget, rset

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

def toast(message, color=None, game_id=None):
    payload = {'message': message, 'color': 'both'}
    if color:
        payload['color'] = color.value
    if not game_id:
        socketio.emit('message', payload)
    else:
        socketio.emit('message', payload, room=game_id)

def whiteboard(message, color=None, game_id=None):
    payload = {'message': message, 'color': 'both'}
    if color:
        payload['color'] = color.value
    if not game_id:
        socketio.emit('whiteboard', payload)
    else:
        socketio.emit('whiteboard', payload, room=game_id)

def opt_key(color):
    return f'{color.value}_opt'

def try_opt(color, game_id, f):
    if rget(opt_key(color), game_id=game_id):
        f()
        rset(opt_key(color), '', game_id=game_id)


two_letter_words = [
    'aa', 'ab', 'ad', 'ae', 'ag', 'ah', 'ai', 'al', 'am', 'an', 'ar', 'as', 
    'at', 'aw', 'ax', 'ay', 'ba', 'be', 'bi', 'bo', 'by', 'da', 'de', 'do', 
    'ed', 'ef', 'eh', 'el', 'em', 'en', 'er', 'es', 'et', 'ex', 'fa', 'fe', 
    'gi', 'go', 'ha', 'he', 'hi', 'hm', 'ho', 'id', 'if', 'in', 'is', 'it', 
    'jo', 'ka', 'ki', 'la', 'li', 'lo', 'ma', 'me', 'mi', 'mm', 'mo', 'mu', 
    'my', 'na', 'ne', 'no', 'nu', 'od', 'oe', 'of', 'oh', 'oi', 'ok', 'om', 
    'on', 'op', 'or', 'os', 'ow', 'ox', 'oy', 'pa', 'pe', 'pi', 'po', 'qi', 
    're', 'sh', 'si', 'so', 'ta', 'te', 'ti', 'to', 'uh', 'um', 'un', 'up', 
    'us', 'ut', 'we', 'wo', 'xi', 'xu', 'ya', 'ye', 'yo', 'za'
    ]
