# -*- coding: utf-8 -*-

# TODO capacity tests...

import os
import sys
import logging

import random
import json
from datetime import datetime

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


cur = db.cursor()
MAX_QUESTIONS = 2 * 700

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

    db.close()

@app.route('/get_questions')
def get_questions():
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

    db.close()
    return jsonify(json_data)


@app.route('/copy_questions')
def copy_questions():
    copy_all_questions()
    return "Done."


@app.route('/api/v1/send_score', methods=['POST'])
def send_score():
    if request.method == 'POST':
        try:
            data = request.get_json()
        except:
            return "Incorrect json"
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

#        f = open('output.json', 'w');
#        f.write(json.dumps(data));
#        f.close();

        cur = db.cursor()

        cur.execute('''INSERT INTO ScoreJSON (end_time, data) VALUES ('{}', '{}')'''
            .format(end_time, json.dumps(data)))
        try:
            cur.commit()
        except:
            print "something wrong with MySQL!!!"
            pass

        items = []
        for score in data['scores']:
            items.append((
                score['question_id'],
                score['is_correct'],
                score['date_ans'],
                data['device_id'],
                data['device_type'],
                data['lat'],
                data['lon'],
                data['lives'],
                data['score'],
                end_time
            ));

        sql = '''
            INSERT IGNORE INTO Score (question_id,
                is_correct,
                submitted,
                device_id,
                device_type,
                lat,
                lon,
                lives,
                score,
                end_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)

        '''

        cur.executemany(sql, items)

        try:
            db.commit()
        except:
            db.rollback()

        db.close()

        return "Done." + str(random.random())

if __name__ == "__main__":
    app.run(host='0.0.0.0')

