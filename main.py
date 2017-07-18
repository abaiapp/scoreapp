# -*- coding: utf-8 -*-

import os
import logging

import random
import json

# [START imports]
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin


app = Flask(__name__)
app.config.from_pyfile('config.cfg')
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
db = MySQLdb.connect(host=app.config['MYSQL_HOST'],
                     user=app.config['MYSQL_USER'],
                     passwd=app.config['MYSQL_PASSWORD'],
                     db=app.config['MYSQL_DB'])


@app.route("/")
def hello():
    return "Please, don't ruin me!!!"

@app.route('/api/v1/send_score', methods=['GET'])
def send_score():
    if request.method == 'GET':
        cur = db.cursor()
        cur.execute('''INSERT INTO Question (sentence, is_real, source) VALUES ('бір өте үлкен сөйлем', 1, 'abai')''')
        print "Done."
        

if __name__ == "__main__":
    app.run(host='0.0.0.0')

