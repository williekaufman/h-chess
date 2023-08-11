#!/usr/bin/python3

from flask import Flask, jsonify, request, make_response, render_template
from flask_cors import CORS, cross_origin
from redis_utils import rget, rset, redis
from settings import LOCAL
from secrets import compare_digest, token_hex
from chess import Board, History

from enum import Enum

app = Flask(__name__)
CORS(app)

def new_game_id():
    return token_hex(16)

@app.route("/", methods=['GET'])
def index():
    return render_template('index.html')

@app.route("/new_game", methods=['GET'])
def new_game():
    game_id = new_game_id()
    rset('board', Board.starting_board.to_string(), game_id=game_id)
    return {'success': True, 'game_id': game_id}

@app.route("/board", methods=['GET'])
def get_board(game_id):
    return Board(rget('board', game_id=game_id))

@app.route("/set", methods=['POST'])
def set_board():
    game_id = request.json.get('game_id')
    piece = request.json.get('piece')
    rank = request.json.get('rank')
    file = request.json.get('file')
    board = Board.of_game_id(game_id)
    board = chess.Board(rget('board', game_id=game_id))
    board.set(rank, file, piece)
    rset('board', board.to_string(), game_id=game_id)
    return {'success': True }

@app.route("/move", methods=['POST'])
def move():
    game_id = request.json.get('game_id')
    start = request.json.get('start')
    stop = request.json.get('stop')
    board = Board.of_game_id(game_id)
    board.move(start, stop)
    rset('board', board.to_string(), game_id=game_id)
    return {'success': True }

@app.route("/example", methods=['GET'])
def example():
    return {'success': True, 'message': f'Your game id is {new_game_id()}'} 

@app.route("/rset", methods=['POST'])
def set_redis():
    game_id = request.json.get('game_id')
    key = request.json.get('key')
    value = request.json.get('value')
    rset(key=key, value=value, game_id=game_id)
    return {'success': True }

@app.route("/rget", methods=['GET'])
def get_redis():
    key = request.args.get('key')
    game_id = request.args.get('game_id')
    return {'success': True, 'value': rget(key, game_id=game_id)}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001 if LOCAL else 5002) 