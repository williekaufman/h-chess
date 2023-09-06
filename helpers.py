from sockets import socketio
from redis_utils import rget, rset
import datetime



def try_move(board, start, stop, history, promote_to=None, return_move=False):
    new_board = board.copy()
    args = {
        'start': start,
        'stop': stop,
        'whose_turn': history.whose_turn(),
        'handicap': None,
        'history': history,
    }
    if promote_to:
        args['promote_to'] = promote_to
    move , _ , _ = new_board.move(**args)
    return (new_board, move) if return_move else new_board


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


def toast(message, color=None, game_id=None, really_broadcast_to_all=False):
    payload = {'message': message, 'color': 'both'}
    if color:
        payload['color'] = color.value
    if not game_id:
        if really_broadcast_to_all:
            socketio.emit('message', payload)
        else:
            print(f'toast called without game_id: {message}')
    else:
        socketio.emit('message', payload, room=game_id)

def whiteboard(message, color=None, game_id=None, really_broadcast_to_all=False):
    payload = {'message': message, 'color': 'both'}
    if color:
        payload['color'] = color.value
    if not game_id:
        # Now that board.game_id is sometimes None, 
        # wants to make sure this is not accidentally called w/o a game id
        if really_broadcast_to_all:
            socketio.emit('whiteboard', payload)
        else:
            print(f'whiteboard called without game_id: {message}')
    else:
        socketio.emit('whiteboard', payload, room=game_id)


def whiteboardify_pieces(pieces):
    return str([p.value for p in set(pieces)]).replace("'", "")

def opt_key(color):
    return f'{color.value}_opt'


def try_opt(color, game_id, f):
    if not game_id:
        return 
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