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

MAX_QUESTIONS = 2 * 700

@app.route('/')
def hello():
    return "Please, don't ruin me!!!"

@app.route('/api/v1/get_top_5', methods=['GET'])
def get_top():
    if request.method == 'GET':
        db = MySQLdb.connect(host=app.config['MYSQL_HOST'],
                             user=app.config['MYSQL_USER'],
                             passwd=app.config['MYSQL_PASSWORD'],
                             db=app.config['MYSQL_DB'])

        
        sql = '''
            SELECT * FROM Ranking ORDER BY score DESC LIMIT 5;
        '''

        cur = db.cursor()
        cur.execute(sql)
        ranking = cur.fetchall()
        try:
            db.commit()
        except:
            db.rollback()
        cur.close()
        db.close()

        data = {
            'ranking': ranking
        }
        
        return jsonify(data)


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

        db = MySQLdb.connect(host=app.config['MYSQL_HOST'],
                             user=app.config['MYSQL_USER'],
                             passwd=app.config['MYSQL_PASSWORD'],
                             db=app.config['MYSQL_DB'])


        cur = db.cursor()
        cur.executemany(sql, items)
        try:
            db.commit()
        except:
            db.rollback()


        cur.close()
        db.close()

        updateRanking(device_id = data['device_id'], score = data['score'])

        return "Done." + str(random.random())

def updateRanking(device_id, score):
    sql = '''
        INSERT INTO Ranking (device_id, score)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
        score = GREATEST(COALESCE(VALUES(score), score), score);
    '''
    db = MySQLdb.connect(host=app.config['MYSQL_HOST'],
                         user=app.config['MYSQL_USER'],
                         passwd=app.config['MYSQL_PASSWORD'],
                         db=app.config['MYSQL_DB'])


    cur = db.cursor()
    cur.execute(sql, (device_id, score))
    try:
        db.commit()
    except:
        db.rollback()
    cur.close()
    db.close()


if __name__ == "__main__":
    app.run(host='0.0.0.0')



'''
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

    for question in questions:
        try:
            cur.execute('INSERT INTO Question (sentence, is_real, source) VALUES ('{}', '{}', '{}')'.format(question['sentence'],
                question['is_real'],
                question['source']))
            db.commit()
        except:
            print "Yoo..."
            db.rollback()

    cur.close()
    db.close()

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
    cur.close()
    db.close()
    return jsonify(json_data)


def copy_questions():
    copy_all_questions()
    return "Done."
'''
