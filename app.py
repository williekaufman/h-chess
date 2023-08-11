#!/usr/bin/python3

from flask import Flask, jsonify, request, make_response, render_template
from flask_cors import CORS, cross_origin
from redis_utils import rget, rset, redis
from settings import LOCAL
from secrets import compare_digest, token_hex
from chess import Board, History, starting_board
from squares import Square

from enum import Enum

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
    rset('board', starting_board.to_string(), game_id=game_id)
    rset('history', History().to_string(), game_id=game_id)
    return {'success': True, 'gameId': game_id}

@app.route("/board", methods=['GET'])
def get_board():
    game_id = request.args.get('gameId')
    print(rget('board', game_id=game_id))
    print(game_id)
    return {'success': True, 'board': Board(rget('board', game_id=game_id)).to_string()}

@app.route("/move", methods=['POST'])
def move():
    game_id = request.json.get('gameId')
    start = Square(request.json.get('start'))
    stop = Square(request.json.get('stop'))
    board = Board.of_game_id(game_id)
    history = History.of_game_id(game_id)
    if (move := board.move(start, stop, history)):
        history.add(move)
        rset('history', history.to_string(), game_id=game_id)
        rset('board', board.to_string(), game_id=game_id)
        return {'success': True}
    else:
        # TODO: return error message
        return {'success': False}

@app.route("/example", methods=['GET'])
def example():
    return {'success': True, 'message': f'Your game id is {new_game_id()}'} 

@app.route("/rset", methods=['POST'])
def set_redis():
    game_id = request.json.get('gameId')
    key = request.json.get('key')
    value = request.json.get('value')
    rset(key=key, value=value, game_id=game_id)
    return {'success': True }

@app.route("/rget", methods=['GET'])
def get_redis():
    key = request.args.get('key')
    game_id = request.args.get('gameId')
    return {'success': True, 'value': rget(key, game_id=game_id)}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001 if LOCAL else 5002) 