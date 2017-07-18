# -*- coding: utf-8 -*-

import os
import logging

import random
import json

# [START imports]
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import MySQLdb

app = Flask(__name__)
app.config.from_pyfile('config.cfg')
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
db = MySQLdb.connect(host=app.config['MYSQL_HOST'],
                     user=app.config['MYSQL_USER'],
                     passwd=app.config['MYSQL_PASSWORD'],
                     db=app.config['MYSQL_DB'])


MAX_QUESTIONS = 2

@app.route('/')
def hello():
    return "Please, don't ruin me!!!"

def read_from_source(source='abai', prefix=''):
    sentences = []
    with open('data/{}{}.txt'.format(prefix, source)) as f:
        sentences = f.readlines()
    return [x.strip() for x in sentences]

def get_all_questions(source='abai'):
    questions = []
    real_ = read_from_source(source)
    fake_ = read_from_source(source, 'fake_')
    n = min(MAX_QUESTIONS / 2, min(len(real_), len(fake_)))
    for i in range(n):
        questions.append({'is_real': 1, 'sentence': real_[i], 'source': source})
        questions.append({'is_real': 0, 'sentence': fake_[i], 'source': source})

    cur = db.cursor()
    for question in questions:
        try:
            cur.execute('''INSERT INTO Question (sentence, is_real, source) VALUES ({}, {}, {})'''.format(question['sentence'], 
                question['is_real'], 
                question['source']))
            cur.commit()
        except:
            print "Yoo..."
            cur.rollback()

@app.route('/copy_questions')
def copy_questions():
    get_all_questions()

@app.route('/api/v1/send_score', methods=['GET'])
def send_score():
    if request.method == 'GET':
        cur = db.cursor()
        try:
            cur.execute('''INSERT INTO Question (sentence, is_real, source) VALUES ('бір өте үлкен сөйлем', 1, 'abai')''')
            db.commit()
        except:
            db.rollback()
        return "Done."
        

if __name__ == "__main__":
    app.run(host='0.0.0.0')

