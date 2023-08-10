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

@app.route("/", methods=['GET'])
def index():
    return render_template('index.html')

@app.route("/example", methods=['GET'])
def example():
    return {'success': True, 'message': 'Hi!'} 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001 if LOCAL else 5002)
