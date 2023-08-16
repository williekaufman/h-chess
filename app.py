#!/usr/bin/python3

from flask import Flask, jsonify, request, make_response, render_template
from flask_cors import CORS, cross_origin
from redis_utils import rget, rset, redis
from settings import LOCAL
from secrets import compare_digest, token_hex
from chess import Color, Board, History, starting_board
from squares import Square
from handicaps import handicaps, get_handicaps
import time
import random
import json

app = Flask(__name__)
CORS(app)

def new_game_id():
    return token_hex(16)

def update_time(whose_turn, game_id):
    now = time.time()
    key = f'{whose_turn.value}_time'
    current_time = rget(key, game_id=game_id)
    if not current_time:
        return
    current_time = float(current_time)
    last_move = rget('last_move', game_id=game_id)
    if last_move:
        time_since_last_move = now - float(last_move)
        if time_since_last_move > current_time:
            return whose_turn.other()
        rset(key, current_time - time_since_last_move, game_id=game_id)
    rset('last_move', now, game_id=game_id)
    

def times(game_id, whose_turn):
    last_move = rget('last_move', game_id=game_id)
    whiteTime = rget(f'{Color.WHITE.value}_time', game_id=game_id)
    blackTime = rget(f'{Color.BLACK.value}_time', game_id=game_id) 
    # This is kinda hacky but it's just so the frontend always displays something
    # for games that don't have time controls
    if not whiteTime or not blackTime:
        return {
            'whiteTime': 'White',
            'blackTime': 'Black',
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
                rget('winner', game_id=game_id) or rset('winner', 'Black', game_id=game_id)
        else:
            blackTime -= time_since_last_move
            if blackTime < 0:
                rget('winner', game_id=game_id) or rset('winner', 'White', game_id=game_id)
    return {
        'whiteTime': whiteTime,
        'blackTime': blackTime,
    }

@app.route("/", methods=['GET'])
def index():
    return render_template('index.html')

def live_game_key(username):
    return 'live_game:' + username

def friends_key(username):
    return 'friends:' + username

def get_friends(username):
    return json.loads(rget(friends_key(username), game_id=None) or '[]')

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

@app.route("/new_game", methods=['POST'])
def new_game():
    game_id = request.json.get('gameId') or new_game_id()
    try:
        playerColor = Color(request.json.get('color'))
    except:
        playerColor = Color.WHITE if random.random() > 0.5 else Color.BLACK
    username = request.json.get('username')
    if username:
        rset(live_game_key(username), game_id, game_id=None)
        rset('username', username, game_id=game_id)
    if (timeControl := request.json.get('timeControl')):
        for color in Color:
            rset(f'{color.value}_time', timeControl, game_id=game_id)
    if rget('board', game_id=game_id):
        return {'success': False, 'error': 'Game already exists'}
    handicaps = get_handicaps(0, 0)
    rset('board', starting_board.to_string(), game_id=game_id)
    rset('history', History().to_string(), game_id=game_id)
    rset('turn', f'{Color.WHITE.value}', game_id=game_id)
    for color, handicap in zip(Color, handicaps):
        rset(f'{color.value}_handicap', handicap, game_id=game_id)
    rset('other_player', color.other().value, game_id=game_id)
    return {'success': True, 'gameId': game_id, 'color': playerColor.value }

@app.route("/active_games", methods=['GET'])
def active_games():
    username = request.args.get('username')
    if not username:
        return {'success': False, 'error': 'No username provided'}
    friends = [str(f) for f in get_friends(username)]
    games = []
    for friend in friends:
        game_id = rget(live_game_key(friend), game_id=None)
        games.append({
            'username': friend,
            'gameId': game_id,
        })
    return {'success': True, 'games': games}

@app.route("/join_game", methods=['GET'])
def join_game():
    game_id = request.args.get('gameId')
    board = Board.of_game_id(game_id)
    winner = rget('winner', game_id=game_id)
    color = rget('other_player', game_id=game_id)
    if not board:
        return {'success': False, 'error': 'Invalid game id'}
    if not color:
        return {'success': False, 'error': 'Game already has two players'}
    username = rget('username', game_id=game_id)
    username and rset(live_game_key(username), '', game_id=None)
    if winner:
        return {'success': True, 'board': board.to_dict(), 'winner': winner}
    rset('other_player', '', game_id=game_id)
    return {'success': True, 'color': color, 'board': board.to_dict(), 'whoseTurn': rget('turn', game_id=game_id)}

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

@app.route("/all_handicaps", methods=['GET'])
def get_all_handicaps():
    return {'success': True, 'handicaps': [k for k in handicaps.keys()]}

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
    return {'success': True, 'board': board.to_dict(), 'whoseTurn': whose_turn.value, **times(game_id, whose_turn)}

@app.route("/history", methods=['GET'])
def get_history():
    game_id = request.args.get('gameId')
    history = History.of_game_id(game_id)
    if not history:
        return {'success': False, 'error': 'Invalid game id'}
    return {'success': True, 'history': history.to_list()}

@app.route("/move", methods=['POST'])
def move():
    game_id = request.json.get('gameId')
    ignore_other_player_check = request.json.get('ignoreOtherPlayerCheck')
    promotion = request.json.get('promotion')
    if rget('other_player', game_id=game_id) and not ignore_other_player_check:
        return {'success': False, 'error': 'Other player has not joined'}
    start = Square(request.json.get('start').upper())
    stop = Square(request.json.get('stop').upper())
    board = Board.of_game_id(game_id)
    history = History.of_game_id(game_id)
    whose_turn = Color.whose_turn(game_id) 
    handicap = handicaps[rget(f'{whose_turn.value}_handicap', game_id=game_id)][0]
    move, extra, error = board.move(start, stop, whose_turn, handicap, history, promotion)
    if move:
        winner_on_time = update_time(whose_turn, game_id)
        history.add(move)
        whose_turn = whose_turn.other()
        handicap = handicaps[rget(f'{whose_turn.value}_handicap', game_id=game_id)][0]
        rset('history', history.to_string(), game_id=game_id)
        rset('board', board.to_string(), game_id=game_id)
        rset('turn', whose_turn.value, game_id=game_id)
        winner = winner_on_time or board.winner(whose_turn, history, handicap)
        ret = {'success': True , 'extra': extra , 'whoseTurn': whose_turn.value}
        if winner:
            rset('winner', winner, game_id=game_id)
            ret['winner'] = winner
        return {**ret, **times(game_id, whose_turn)}
    else:
        # It's bad if we end up here since the UI board will be out of sync with the server board
        # That's why we snapback the board on the UI side for moves not in the legal_moves list
        # It's ok for moves that aren't requested via dragging pieces around, e.g. via retry
        return {'success': False, 'error': error , 'whose_turn': whose_turn.value}
    
@app.route("/legal_moves", methods=['GET'])
def legal_moves():
    game_id = request.args.get('gameId')
    ignore_other_player_check = request.args.get('ignoreOtherPlayerCheck')
    ignore_other_player_check = ignore_other_player_check and ignore_other_player_check.lower() == 'true'
    if rget('other_player', game_id=game_id) and not ignore_other_player_check:
        return {'success': False, 'error': 'Other player has not joined'}
    start = Square(request.args.get('start').upper())
    board = Board.of_game_id(game_id)
    history = History.of_game_id(game_id)
    whose_turn = Color.whose_turn(game_id)
    handicap = handicaps[rget(f'{whose_turn.value}_handicap', game_id=game_id)][0]
    return { 'success': True, 'moves': board.legal_moves(start, history, whose_turn, handicap) }

@app.route("/add_friend", methods=['POST'])
def befriend():
    username = request.json.get('username')
    friend = request.json.get('friend')
    if not username or not friend:
        return {'success': False, 'error': 'No username or friend provided'}
    if username == friend:
        return {'success': False, 'error': 'Befriending yourself is just sad'}
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001 if LOCAL else 5003)