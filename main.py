# -*- coding: utf-8 -*-

# TODO capacity tests...

import os
import sys
import logging

import random
import json
import datetime

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


MAX_QUESTIONS = 700

@app.route('/')
def hello():
    return "Please, don't ruin me!!!"

def read_from_source(source='abai', prefix=''):
    sentences = []
    with open('data/{}{}.txt'.format(prefix, source)) as f:
        sentences = f.readlines()
    return [x.strip() for x in sentences]

def copy_all_questions(source='abai'):

    cur = db.cursor()
    cur.execute('SELECT id FROM Question')
    data = cur.fetchall()

    if len(data) > 0:
        print len(data)
        return

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
            cur.execute('''INSERT INTO Question (sentence, is_real, source) VALUES ('{}', '{}', '{}')'''.format(question['sentence'],
                question['is_real'],
                question['source']))
            db.commit()
        except:
            print "Yoo..."
            db.rollback()

#@app.route('/get_questions')
def get_questions():
    cur = db.cursor()
    cur.execute('SELECT id, sentence, is_real, source from Question')
    data = cur.fetchall()

    json_data = []
    for row in data:
        json_data.append({
            'id': row[0],
            'sentence': row[1],
            'is_real': row[2],
            'source': row[3],
        })

    return jsonify(json_data)


#@app.route('/copy_questions')
def copy_questions():
    copy_all_questions()
    return "Done."


@app.route('/api/v1/send_score', methods=['POST'])
def send_score():
    if request.method == 'POST':
        try:
            scores = request.get_json()
        except:
            return "Incorrect json"

        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur = db.cursor()
        for score in scores:
            try:
                cur.execute('''INSERT INTO Score (question_id,
                    is_correct,
                    submitted,
                    device_id,
                    lat,
                    lon,
                    lives,
                    score,
                    end_time) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}')'''
                    .format(score[u'question_id'],
                        score[u'is_correct'],
                        score[u'submitted'],
                        score[u'device_id'],
                        score[u'lat'],
                        score[u'lon'],
                        score[u'lives'],
                        score[u'score'],
                        end_time))
                db.commit()
            except:
                db.rollback()
        return "Done."

if __name__ == "__main__":
    app.run(host='0.0.0.0')

