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

def ranking(count):
    db = MySQLdb.connect(host=app.config['MYSQL_HOST'],
                         user=app.config['MYSQL_USER'],
                         passwd=app.config['MYSQL_PASSWORD'],
                         db=app.config['MYSQL_DB'])


    sql = '''
        SELECT name, score, Ranking.device_id FROM Ranking
        LEFT JOIN DeviceName
        ON Ranking.device_id <=> DeviceName.device_id
        ORDER BY score DESC LIMIT %s;
    ''' % str(count)

    cur = db.cursor()
    cur.execute(sql)
    ranking = cur.fetchall()

    data = {'ranking': [] }

    for row in ranking:
        data['ranking'].append({
            'name': row[0],
            'score': row[1],
            'device_id': row[2],
        });

    try:
        db.commit()
    except:
        db.rollback()
    cur.close()
    db.close()

    return data



@app.route('/api/v1/get_top', methods=['GET'])
def get_top():
    if request.method == 'GET':
        count = request.args.get('count', 5)
        return jsonify(ranking(count))

@app.route('/api/v1/get_top_correct', methods=['GET'])
def get_top_correct():
    if request.method == 'GET':
        count = request.args.get('count', 5)
        device_id = request.args.get('device_id', '')
        data = ranking(count)

        res = []
        found_him = 0

        if data['ranking']:
            for i in range(len(data['ranking'])):
                device = data['ranking'][i]
                is_this_one = 0
                if device['device_id'] == device_id:
                    is_this_one = 1
                    found_him = 1
                res.append({
                    'is_this_one': is_this_one,
                    'rank': i + 1,
                    'score': device['score'],
                    'name': device['name'],
                    'device_type': "ios" if device['device_id'].split('-') > 1 else "android",
                })

        if found_him == 0:
            his_rank = rank(device_id)
            res = [{
                'is_this_one': 1,
                'rank': his_rank['rank'],
                'score': his_rank['score'],
                'name': his_rank['name'],
                'device_type': "ios" if device_id.split('-') > 1 else "android"
            }] + res

        return jsonify({
            "ranking": res,
        })

def rank(device_id):
    db = MySQLdb.connect(host=app.config['MYSQL_HOST'],
                         user=app.config['MYSQL_USER'],
                         passwd=app.config['MYSQL_PASSWORD'],
                         db=app.config['MYSQL_DB'])


    sql = '''
        SELECT count(*)+1 FROM Ranking WHERE score > (
            SELECT score FROM Ranking WHERE device_id = '%s');
    ''' % device_id

    rank = 0
    name = ""
    score = 0

    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM Ranking WHERE device_id = '%s'" % device_id)
    row = cur.fetchone()
    if row is not None and row[0]:
        cur.execute(sql)
        row = cur.fetchone()
        if row is not None and row[0]:
            rank = row[0]

        sql = '''
            SELECT name FROM DeviceName WHERE device_id = '%s'
        ''' % device_id

        cur.execute(sql)
        row = cur.fetchone()
        if row is not None and row[0]:
            name = row[0]

        cur.execute("SELECT score FROM Ranking WHERE device_id = '%s'" % device_id)
        row = cur.fetchone()
        if row is not None and row[0]:
            score = row[0]

    try:
        db.commit()
    except:
        db.rollback()
    cur.close()
    db.close()

    return {
        'rank': rank,
        'name': name,
        'score': score,
    }


@app.route('/api/v1/get_rank', methods=['GET'])
def get_rank():
    if request.method == 'GET':
        device_id = request.args.get('device_id', '')
        return jsonify(rank(device_id))


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

@app.route('/api/v1/update_name', methods=['GET'])
def updateName():
    device_id = request.args.get('device_id', '')
    name = request.args.get('name', '')
    if len(device_id) > 0 and len(name) > 0:
        sql = '''
            INSERT INTO DeviceName (device_id, name)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE
            name = VALUES(name)
        '''
        db = MySQLdb.connect(host=app.config['MYSQL_HOST'],
                             user=app.config['MYSQL_USER'],
                             passwd=app.config['MYSQL_PASSWORD'],
                             db=app.config['MYSQL_DB'])

        cur = db.cursor()
        cur.execute(sql, (device_id, name.encode('utf8')))
        try:
            db.commit()
        except:
            db.rollback()
        cur.close()
        db.close()

    return "Done."


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
