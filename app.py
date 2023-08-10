#!/usr/bin/python3

from flask import Flask, jsonify, request, make_response, render_template
from flask_cors import CORS, cross_origin
from redis_utils import rget, rset, redis
from settings import LOCAL
from secrets import compare_digest, token_hex
import random
import json

from enum import Enum

app = Flask(__name__)
CORS(app)

def new_game_id():
    return token_hex(16)

@app.route("/", methods=['GET'])
def index():
    return render_template('index.html')

@app.route("/example", methods=['GET'])
def example():
    return {'success': True, 'message': 'Hi!'} 

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
