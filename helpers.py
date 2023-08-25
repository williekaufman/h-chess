from sockets import socketio

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

def broadcast(message, game_id):
    socketio.emit('message', message, room=game_id)

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
