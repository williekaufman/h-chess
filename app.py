#!/usr/bin/python3

from flask import Flask, jsonify, request, make_response, render_template
from flask_socketio import SocketIO, send, emit, join_room, leave_room
from flask_cors import CORS, cross_origin
from threading import Thread
from redis_utils import rget, rset, redis
from settings import LOCAL
from secrets import compare_digest, token_hex
from chess import Color, Piece, Result, Board, History, starting_board
from squares import Square
from handicaps import handicaps, lookup_handicap, get_handicaps, tested_handicaps, test_all_handicaps, Difficulty, get_handicap_elo, set_handicap_elo, instantiate_handicap_elos
import time
import random
import json
from sockets import app, socketio
from helpers import toast, whiteboard, opt_key
import signal
import sys


CORS(app)

def new_game_id():
    return token_hex(16)

def get_increment(game_id):
    try:
        return float(rget('increment', game_id=game_id))
    except:
        return 0

def update_time(whose_turn, game_id):
    now = time.time()
    key = f'{whose_turn.value}_time'
    current_time = rget(key, game_id=game_id)
    increment = get_increment(game_id)
    if not current_time:
        return
    current_time = float(current_time)
    last_move = rget('last_move', game_id=game_id)
    if last_move:
        time_since_last_move = now - float(last_move)
        rset(key, current_time - time_since_last_move + increment, game_id=game_id)
        rset('last_move', now, game_id=game_id)
        if time_since_last_move > current_time:
            return whose_turn.other()
    elif whose_turn == Color.BLACK:
        rset('last_move', now, game_id=game_id)

def times(game_id, whose_turn):
    last_move = rget('last_move', game_id=game_id)
    whiteTime = rget(f'{Color.WHITE.value}_time', game_id=game_id)
    blackTime = rget(f'{Color.BLACK.value}_time', game_id=game_id)
    # TODO handle case where one player has no time control
    if not whiteTime or not blackTime:
        return {
            'whiteTime': 'White',
            'blackTime': 'Black',
            'ticking': False,
        }
    whiteTime = float(whiteTime)
    blackTime = float(blackTime)
    if last_move:
        last_move = float(last_move)
        now = time.time()
        time_since_last_move = now - last_move
        if whose_turn == Color.WHITE:
            whiteTime -= time_since_last_move
            if whiteTime < 0:
                rget('winner', game_id=game_id) or rset(
                    'winner', 'Black', game_id=game_id)
        else:
            blackTime -= time_since_last_move
            if blackTime < 0:
                rget('winner', game_id=game_id) or rset(
                    'winner', 'White', game_id=game_id)
    return {
        'whiteTime': whiteTime,
        'blackTime': blackTime,
        'ticking': bool(last_move),
    }

def update_elos(handicaps, players, result):
    if result == Result.WHITE_WINS:
        result = 1
    elif result == Result.BLACK_WINS:
        result = 0
    else:
        result = 0.5
    white_player_elo = get_player_elo(players[Color.WHITE])
    black_player_elo = get_player_elo(players[Color.BLACK])
    white_handicap_elo = get_handicap_elo(handicaps[Color.WHITE])
    black_handicap_elo = get_handicap_elo(handicaps[Color.BLACK])
    white_elo = white_player_elo + white_handicap_elo
    black_elo = black_player_elo + black_handicap_elo
    expected = 1 / (1 + 10 ** ((black_elo - white_elo) / 400))
    adjustment = 32 * (result - expected)
    set_handicap_elo(handicaps[Color.WHITE], white_handicap_elo + adjustment)
    set_handicap_elo(handicaps[Color.BLACK], black_handicap_elo - adjustment)
    set_player_elo(players[Color.WHITE], white_player_elo + adjustment)
    set_player_elo(players[Color.BLACK], black_player_elo - adjustment)

def get_player_elo(username):
    try:
        return float(rget(username, game_id='player_elos'))
    except:
        return 1200

def set_player_elo(username, elo):
    rset(username, elo, game_id='player_elos')

def set_winner(game_id, result):
    handicaps = {color: rget(f'{color.value}_handicap', game_id=game_id) for color in Color}
    players = {color: rget(f'{color.value}_username', game_id=game_id) for color in Color}
    if players[Color.WHITE] and players[Color.BLACK]:
        update_elos(handicaps, players, result)
    rset('winner', result.value, game_id=game_id)

def get_winner(game_id):
    try:
        return Result(rget('winner', game_id=game_id))
    except:
        return None

def make_promotion_arg(promotion):
    try:
        promotion = Piece(promotion.upper())
    except:
        promotion = Piece.QUEEN
    return promotion

@app.route("/", methods=['GET'])
def index():
    return render_template('index.html')

def last_game_key(username):
    return 'last_game:' + username

def last_color_key(username):
    return 'last_color:' + username

def friends_key(username):
    return 'friends:' + username

def get_friends(username):
    return json.loads(rget(friends_key(username), game_id=None) or '[]')

def is_online(username):
    return redis.sismember('online_players', username)

def online_players():
    return [p.decode('utf-8') for p in redis.smembers('online_players')]

# We're going to call this a lot unnecessarily but that's fine
# Just make sure it's idempotent
def logon(username):
    rset(f'{username}:last_seen', time.time(), game_id=None)
    redis.sadd('online_players', username)

# Called whenever you change your username or close a window
# with a username. If you had multiple open, we'll log you back on
# as soon as you do anything that requires a username, like reloading
# the friends list
def logoff(username):
    redis.srem('online_players', username)

def last_seen(username):
    try:
        return float(rget(f'{username}:last_seen', game_id=None))
    except:
        return 0

# I think this shouldn't really be necessary since we have the socket.on disconnect logic 
# but better safe than sorry, don't want weird ghost users piling up
def sweep():
    now = time.time()
    for username in online_players():
        if now - last_seen(username) > 3600:
            print(f'Logging off {username} due to inactivity')
            logoff(username)

def get_public_games():
    for player in online_players():
        game_id = rget(last_game_key(player), game_id=None)
        if game_id and rget('public', game_id=game_id) and (color := rget('other_player', game_id=game_id)):
            difficulty = Difficulty.of_number(handicaps[rget(
                f'{color}_handicap', game_id=game_id)][1])
            yield {'username': player, 'gameId': game_id, 'color': color, 'difficulty': difficulty.value}

def add_friend(username, friend):
    friends = get_friends(username)
    if friend in friends:
        return False
    friends.append(friend)
    rset(friends_key(username), json.dumps(friends), game_id=None, ex=None)


def remove_friend(username, friend):
    friends = get_friends(username)
    if friend not in friends:
        return False
    friends.remove(friend)
    rset(friends_key(username), json.dumps(friends), game_id=None, ex=None)

@app.route("/rejoin", methods=['GET'])
def rejoin():
    username = request.args.get('username')
    if not username:
        return {'success': False, 'error': 'No username provided'}
    logon(username)
    game_id = rget(last_game_key(username), game_id=None)
    color = rget(last_color_key(username), game_id=None)
    if not game_id or not color:
        return {'success': False, 'error': 'No game to rejoin'}
    if get_winner(game_id):
        return {'success': False, 'error': 'Game is over'}
    return {'success': True, 'gameId': game_id, 'color': color}

def float_arg(arg, default=0):
    try:
        return float(arg)
    except:
        return default

@app.route("/new_game", methods=['POST'])
def new_game():
    game_id = request.json.get('gameId') or new_game_id()
    try:
        playerColor = Color(request.json.get('color'))
    except:
        playerColor = Color.WHITE if random.random() > 0.5 else Color.BLACK
    if rget('board', game_id=game_id):
        return {'success': False, 'error': 'Game already exists'}
    username = request.json.get('username')
    if username:
        logon(username)
        rset(last_game_key(username), game_id, game_id=None)
        rset(last_color_key(username), playerColor.value, game_id=None)
        rset(f'{playerColor.value}_username', username, game_id=game_id)
        if request.json.get('public'):
            rset('public', 'True', game_id=game_id)
    if (timeControl := float_arg(request.json.get('timeControl'))):
        for color in Color:
            rset(f'{color.value}_time', timeControl, game_id=game_id)
    if (increment := float_arg(request.json.get('increment'))):
        rset('increment', increment, game_id=game_id) 
    if request.json.get('aiOpp'):
        rset('ai', playerColor.other().value, game_id=game_id)
    handicap_config = {Color.WHITE: None, Color.BLACK: None}
    if (yourHandicap := request.json.get('yourHandicap')):
        try:
            yourHandicap = Difficulty(yourHandicap)
        except:
            return {'success': False, 'error': 'Invalid handicap difficulty'}
        handicap_config[playerColor] = yourHandicap
    if (theirHandicap := request.json.get('theirHandicap')):
        try:
            theirHandicap = Difficulty(theirHandicap)
        except:
            return {'success': False, 'error': 'Invalid handicap difficulty'}
        handicap_config[playerColor.other()] = theirHandicap
    handicaps = get_handicaps(handicap_config)
    starting_board().write_to_redis(game_id)
    rset('history', History().to_string(), game_id=game_id)
    rset('turn', f'{Color.WHITE.value}', game_id=game_id)
    for color, handicap in zip(Color, handicaps):
        rset(f'{color.value}_handicap', handicap, game_id=game_id)
    for color in Color:
        rset(opt_key(color), 'True', game_id=game_id)
    rset('other_player', playerColor.other().value, game_id=game_id)
    if rget('ai', game_id=game_id) == 'White':
        board = Board.of_game_id(game_id)
        history = History.of_game_id(game_id)
        if (ret := board.ai_move(history, lookup_handicap(game_id, Color.WHITE))):
                make_move(game_id, ret[0], board, history, ret[1])
    return {'success': True, 'gameId': game_id, 'color': playerColor.value}

@app.route("/public_games", methods=['GET'])
def public_games():
    return {'success': True, 'games': list(get_public_games())}

@app.route("/friends", methods=['GET'])
def get_friends_list():
    username = request.args.get('username')
    if not username:
        return {'success': False, 'error': 'No username provided'}
    friends = sorted([str(f) for f in get_friends(username)])
    online_friends, offline_friends = [
        [f for f in friends if is_online(f) == online] for online in [True, False]
    ]
    return {'success': True, 'online': online_friends, 'offline': offline_friends}

@app.route("/join_game", methods=['GET'])
def join_game():
    game_id = request.args.get('gameId')
    board = Board.of_game_id(game_id)
    winner = rget('winner', game_id=game_id)
    set_other_player = False
    color = request.args.get('color') 
    if not color:
        color = rget('other_player', game_id=game_id)
        set_other_player = True
    last_move = rget('last_move', game_id=game_id)
    if not board:
        return {'success': False, 'error': 'Invalid game id'}
    if not color:
        return {'success': False, 'error': 'Game already has two players'}
    username = request.args.get('username')
    if username:
        logon(username)
        rset(last_game_key(username), game_id, game_id=None)
        rset(last_color_key(username), color, game_id=None)
        rset(f'{color}_username', username, game_id=game_id)
    set_other_player and toast(f"{username or 'anonymous player'} joined!", game_id=game_id)
    if winner:
        return {'success': True, 'board': board.to_dict(), 'winner': winner, 'color': color}
    set_other_player and rset('other_player', '', game_id=game_id)
    return {
        'success': True, 
        'color': color, 
        'board': board.to_dict(), 
        'whoseTurn': rget('turn', game_id=game_id), 
        'mostRecentMove': 
        {
            'from': board.cache.most_recent_move.start.value,
            'to': board.cache.most_recent_move.stop.value
        } if board.cache.most_recent_move else None, 
         **times(game_id, Color.whose_turn(game_id))}

@app.route("/watch_game", methods=['GET'])
def watch_game():
    game_id = request.args.get('gameId')
    board = Board.of_game_id(game_id)
    winner = rget('winner', game_id=game_id)
    last_move = rget('last_move', game_id=game_id)
    if not board:
        return {'success': False, 'error': 'Invalid game id'}
    if winner:
        return {'success': True, 'board': board.to_dict(), 'winner': winner}
    return {
        'success': True,
        'board': board.to_dict(),
        'whoseTurn': rget('turn', game_id=game_id),
        'mostRecentMove': 
        {
            'from': board.cache.most_recent_move.start.value,
            'to': board.cache.most_recent_move.stop.value
        } if board.cache.most_recent_move else None,
        **times(game_id, Color.whose_turn(game_id))}

@app.route('/handicap', methods=['GET'])
def get_handicap():
    game_id = request.args.get('gameId')
    try:
        color = Color(request.args.get('color'))
    except:
        return {'success': False, 'error': 'Invalid color'}
    if (handicap := rget(f'{color.value}_handicap', game_id=game_id)):
        return {'success': True, 'handicap': handicap}
    else:
        return {'success': False, 'error': 'Invalid game id'}

@app.route('/both_handicaps', methods=['GET'])
def get_both_handicaps():
    game_id = request.args.get('gameId')
    if (white_handicap := rget(f'{Color.WHITE.value}_handicap', game_id=game_id)) and (black_handicap := rget(f'{Color.BLACK.value}_handicap', game_id=game_id)):
        return {'success': True, 'White': white_handicap, 'Black': black_handicap}

@app.route("/all_handicaps", methods=['GET'])
def get_all_handicaps():
    ret = [k for k in tested_handicaps.keys()]
    if request.args.get('includeElos'):
        ret = {k: get_handicap_elo(k) for k in ret}
    return {'success': True, 'handicaps': ret}

@app.route("/elo", methods=['GET'])
def get_elo():
    username = request.args.get('username')
    if not username:
        return {'success': False, 'error': 'No username provided'}
    return {'success': True, 'elo': get_player_elo(username)}

@app.route("/elo/all", methods=['GET'])
def get_all_elos():
    keys = [k.decode('utf-8').split(':')[1] for k in redis.keys('*player_elos')]
    elos = {k: get_player_elo(k) for k in keys}
    return {'success': True, 'elos': elos}

@app.route("/board", methods=['GET'])
def get_board():
    game_id = request.args.get('gameId')
    board = Board.of_game_id(game_id)
    winner = rget('winner', game_id=game_id)
    whose_turn = Color.whose_turn(game_id)
    if not board:
        return {'success': False, 'error': 'Invalid game id'}
    if winner:
        return {'success': True, 'board': board.to_dict(), 'winner': winner}
    return {
        'success': True, 
        'board': board.to_dict(), 
        'whoseTurn': whose_turn.value, 
        'mostRecentMove': 
        {
            'from': board.cache.most_recent_move.start.value,
            'to': board.cache.most_recent_move.stop.value
        } if board.cache.most_recent_move else None,
        **times(game_id, whose_turn), 
    }

@app.route("/history", methods=['GET'])
def get_history():
    game_id = request.args.get('gameId')
    history = History.of_game_id(game_id)
    if not history:
        return {'success': False, 'error': 'Invalid game id'}
    return {'success': True, 'history': history.to_list()}

# Only call this if you've validated the move already
def make_move(game_id, move, board, history, extra):
    rset('draw', '', game_id=game_id)
    whose_turn = history.whose_turn()
    winner_on_time = update_time(whose_turn, game_id)
    history.add(move)
    rset(opt_key(whose_turn), 'True', game_id=game_id)
    whose_turn = whose_turn.other()
    handicap = lookup_handicap(game_id, whose_turn)
    rset('history', history.to_string(), game_id=game_id)
    board.write_to_redis()
    rset('turn', whose_turn.value, game_id=game_id)
    winner = winner_on_time or board.winner(whose_turn, history, handicap)
    ret = {'success': True, 'extra': extra, 'whoseTurn': whose_turn.value}
    if winner:
        set_winner(game_id, Result(winner.value))
        ret['winner'] = winner.value
    # This tells the frontend to pull down the new state
    socketio.emit('update', { 'color': whose_turn.value }, room=game_id)
    return ret

def move_inner():
    game_id = request.json.get('gameId')
    ignore_other_player_check = request.json.get('ignoreOtherPlayerCheck')
    promotion = make_promotion_arg(request.json.get('promotion'))
    if rget('other_player', game_id=game_id) and not ignore_other_player_check and not rget('ai', game_id=game_id):
        return {'success': False, 'error': 'Other player has not joined'}
    start = Square(request.json.get('start').upper())
    stop = Square(request.json.get('stop').upper())
    board = Board.of_game_id(game_id)
    history = History.of_game_id(game_id)
    whose_turn = Color.whose_turn(game_id)
    handicap = lookup_handicap(game_id, whose_turn)
    move, extra, error = board.move(
        start, stop, whose_turn, handicap, history, promotion)
    if move:
        ret = make_move(game_id, move, board, history, extra)
        whose_turn = whose_turn.other()
        if ('winner' not in ret) and rget('ai', game_id=game_id) == whose_turn.value:
            if (move, extra, error := board.ai_move(history, lookup_handicap(game_id, whose_turn))):
                make_move(game_id, move, board, history, extra)
        return {**ret, **times(game_id, whose_turn)}
    else:
        return {'success': False, 'error': error }

def error_handler(e):
    print(f'Exception on /move: {e}')
    return {
        'success': False, 
        'error': 'Invalid request, probably due to a bug. If convenient, please report it. The console should have a log of the actual error. Sorry!', 
        'exception': str(e)}

@app.route("/move", methods=['POST'])
def move():
    if not LOCAL:
        try:
            return move_inner()
        except Exception as e:
            return error_handler(e)
    else:
        return move_inner()

    
def legal_moves_inner():
    game_id = request.args.get('gameId')
    ignore_other_player_check = request.args.get('ignoreOtherPlayerCheck')
    ignore_other_player_check = ignore_other_player_check and ignore_other_player_check.lower() == 'true'
    if rget('other_player', game_id=game_id) and not ignore_other_player_check and not rget('ai', game_id=game_id):
        return {'success': False, 'error': 'Other player has not joined'}
    start = Square(request.args.get('start').upper())
    board = Board.of_game_id(game_id)
    history = History.of_game_id(game_id)
    whose_turn = Color.whose_turn(game_id)
    promotion = make_promotion_arg(request.args.get('promotion'))
    handicap = lookup_handicap(game_id, whose_turn)
    return {'success': True, 'moves': board.legal_moves(start, history, whose_turn, handicap, promotion)}


@app.route("/legal_moves", methods=['GET'])
def legal_moves():
    try:
        return legal_moves_inner()
    except Exception as e:
        return error_handler(e)


@app.route("/add_friend", methods=['POST'])
def befriend():
    username = request.json.get('username')
    friend = request.json.get('friend')
    if not username or not friend:
        return {'success': False, 'error': 'No username or friend provided'}
    if username == friend:
        return {'success': False, 'error': 'Befriending yourself is just sad'} 
    socketio.emit('message', {'message': f'{username} added you as a friend'}, room=friend)
    add_friend(username, friend)
    return {'success': True}

# Ya this should probably be DELETE type but whatever
@app.route("/remove_friend", methods=['POST'])
def unfriend():
    username = request.json.get('username')
    friend = request.json.get('friend')
    if not username or not friend:
        return {'success': False, 'error': 'No username or friend provided'}
    remove_friend(username, friend)
    return {'success': True}


@app.route("/offer_draw", methods=['POST'])
def offer_draw():
    game_id = request.json.get('gameId')
    color = request.json.get('color')
    try:
        color = Color(color)
    except:
        return {'success': False, 'error': 'Invalid color'}
    if not game_id or not color:
        return {'success': False, 'error': 'No game id or color provided'}
    if rget('other_player', game_id=game_id):
        return {'success': False, 'error': 'Other player has not yet joined'}
    socketio.emit('draw_offer', {'color': color.other().value}, room=game_id)
    rset('draw', color.value, game_id=game_id)
    return {'success': True} 

@app.route("/accept_draw", methods=['POST'])
def accept_draw():
    game_id = request.json.get('gameId')
    color = request.json.get('color')
    try:
        color = Color(color)
    except:
        return {'success': False, 'error': 'Invalid color'}
    if not game_id or not color:
        return {'success': False, 'error': 'No game id or color provided'}
    if rget('draw', game_id=game_id) != color.other().value:
        return {'success': False, 'error': 'Draw offer not live - expires when either player makes a move'}
    if rget('winner', game_id=game_id):
        return {'success': False, 'error': 'Game already over'}
    set_winner(game_id, Result.AGREEMENT)
    socketio.emit('update', {'color': 'both'}, room=game_id)
    return {'success': True}

@app.route("/resign", methods=['POST'])
def resign():
    game_id = request.json.get('gameId')
    color = request.json.get('color')
    try:
        color = Color(color)
    except:
        return {'success': False, 'error': 'Invalid color'}
    if not game_id or not color:
        return {'success': False, 'error': 'No game id or color provided'}
    if rget('winner', game_id=game_id):
        return {'success': False, 'error': 'Game already over'}
    set_winner(game_id, Result(color.other().value))
    whiteboard(f'{color.value} resigned', color.other(), game_id=game_id)
    socketio.emit('update', {'color': 'both'}, room=game_id)
    return { 'success': True }

@app.route("/invite", methods=['POST'])
def invite():
    friend = request.json.get('friend')
    username = request.json.get('username') or 'anonymous'
    game_id = request.json.get('gameId')
    if not friend or not game_id:
        return {'success': False, 'error': 'No friend or game id provided'}
    if not rget('other_player', game_id=game_id):
        return {'success': False, 'error': 'Game already has two players'}
    socketio.emit('invite', {'gameId': game_id, 'username': username }, room=friend)
    return {'success': True}

@socketio.on('connect')
def on_connect():
    pass

@socketio.on('disconnect')
def on_disconnect():
    username = rget(request.sid, game_id=None)
    if username:
        logoff(username)

@socketio.on('logon')
def on_logon(data):
    username = data['username']
    if not username:
        return
    logon(username)
    rset(request.sid, username, game_id=None)

@socketio.on('logoff')
def on_logoff(data):
    username = data['username']
    if not username:
        return
    logoff(username)

@socketio.on('join')
def on_join(data):
    game_id = data['room']
    join_room(game_id)
    board = Board.of_game_id(game_id)
    if not board:
        # Joining a username room, not a game room
        return 
    history = History.of_game_id(game_id)
    whose_turn = Color.whose_turn(game_id)
    handicap = lookup_handicap(game_id, whose_turn)
    # so we try once-per-turn events when the frontend 
    # joins the room in the call to /new_game

    # Might not always work if there isn't a knight at home but 
    # whatever, just pick up a piece or something. Shouldn't have a lot
    # of cases of people joining games that are already in progress

    # TODO
    # This comment is somewhat out of date, since when you refresh you join
    # whatever game you used to be in. Could come up with something better.
    square = Square('B1') if whose_turn == Color.WHITE else Square('B8')
    board.legal_moves(square, history, whose_turn, handicap)


@socketio.on('leave')
def on_leave(data):
    leave_room(data['room'])

def run_sweep():
    while True:
        sweep()
        time.sleep(1800)

if __name__ == '__main__':
    instantiate_handicap_elos()
    try:
        test_all_handicaps()
    except Exception as e:
        print(e)
        print('Handicap tests failed')
    Thread(target=run_sweep).start()
    socketio.run(app, host='0.0.0.0', port=5001 if LOCAL else 5003)
