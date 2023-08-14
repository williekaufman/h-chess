#!/usr/bin/python3

from flask import Flask, jsonify, request, make_response, render_template
from flask_cors import CORS, cross_origin
from redis_utils import rget, rset, redis
from settings import LOCAL
from secrets import compare_digest, token_hex
from chess import Board, History, starting_board
from squares import Square
from handicaps import handicaps, get_handicaps

# from enum import Enum

app = Flask(__name__)
CORS(app)

def new_game_id():
    return token_hex(16)

@app.route("/", methods=['GET'])
def index():
    return render_template('index.html')

@app.route("/new_game", methods=['POST'])
def new_game():
    game_id = new_game_id()
    handicaps = get_handicaps(0, 0)
    rset('board', starting_board.to_string(), game_id=game_id)
    rset('history', History().to_string(), game_id=game_id)
    rset('turn', 'W', game_id=game_id)
    rset('w_handicap', handicaps[0], game_id=game_id)
    rset('b_handicap', handicaps[1], game_id=game_id)
    return {'success': True, 'gameId': game_id}

@app.route('/handicap', methods=['GET'])
def get_handicap():
    game_id = request.args.get('gameId')
    color = request.args.get('color')
    color = 'w' if color == 'white' else 'b'
    if (handicap := rget(f'{color}_handicap', game_id=game_id)):
        return {'success': True, 'handicap': handicap}
    else:
        return {'success': False, 'error': 'Invalid game id'}

@app.route("/board", methods=['GET'])
def get_board():
    game_id = request.args.get('gameId')
    board = Board.of_game_id(game_id)
    if not board:
        return {'success': False, 'error': 'Invalid game id'}
    return {'success': True, 'board': board.to_dict(), 'whoseTurn': rget('turn', game_id=game_id)}

@app.route("/move", methods=['POST'])
def move():
    game_id = request.json.get('gameId')
    start = Square(request.json.get('start').upper())
    stop = Square(request.json.get('stop').upper())
    board = Board.of_game_id(game_id)
    history = History.of_game_id(game_id)
    whose_turn = rget('turn', game_id=game_id)
    handicap = handicaps[rget(f'{whose_turn.lower()}_handicap', game_id=game_id)][0]
    move, extra, error = board.move(start, stop, whose_turn, handicap, history)
    if move:
        history.add(move)
        whose_turn = 'W' if whose_turn == 'B' else 'B'
        handicap = handicaps[rget(f'{whose_turn.lower()}_handicap', game_id=game_id)][0]
        rset('history', history.to_string(), game_id=game_id)
        rset('board', board.to_string(), game_id=game_id)
        rset('turn', whose_turn, game_id=game_id)
        return {'success': True , 'extra': extra , 'whoseTurn': whose_turn, 'gameOver': board.game_over(whose_turn, history, handicap)}
    else:
        # It's bad if we end up here since the UI board will be out of sync with the server board
        # That's why we snapback the board on the UI side for moves not in the legal_moves list
        # It's ok for moves that aren't requested via dragging pieces around, e.g. via retry
        return {'success': False, 'error': error , 'whose_turn': whose_turn}
    
@app.route("/legal_moves", methods=['GET'])
def legal_moves():
    game_id = request.args.get('gameId')
    start = Square(request.args.get('start').upper())
    board = Board.of_game_id(game_id)
    history = History.of_game_id(game_id)
    whose_turn = rget('turn', game_id=game_id)
    handicap = handicaps[rget(f'{whose_turn.lower()}_handicap', game_id=game_id)][0]
    return { 'success': True, 'moves': board.legal_moves(start, history, whose_turn, handicap) }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001 if LOCAL else 5002) 