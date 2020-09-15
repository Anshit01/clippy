from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, send, emit
from pymongo import MongoClient
import uuid
import time

from app import config


app = Flask(__name__)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 #############WARNING: remove in production
app.secret_key = config.APP_SECRET_KEY

socketio = SocketIO(app)
socketio.init_app(app, cors_allowed_origins="*") ########### WARNING: remove in production

cluster = MongoClient(f'mongodb+srv://{config.DB_USERNAME}:{config.DB_PASSWORD}@cluster0.erdus.mongodb.net/database?retryWrites=true&w=majority')
database = cluster['database']
users_collection = database.users
clip_list_collection = database.clip_list
clips_collection = database.clips


@app.route('/')
def index_route():
    return render_template('index.html')

@socketio.on('message')
def handle_message(msg):
    print('Message: ' + msg)

@socketio.on('connect')
def handle_connect():
    connection_id = uuid.uuid4().hex
    emit('connect_response', connection_id)

@socketio.on('login')
def handle_login(name, email, uid):
    print('Login: ' + name + ' ' + email + ' ' + uid)
    user = users_collection.find_one({'email': email})
    err = None
    recent_clip_id = ''
    clip_list = {}
    if user:
        if uid == user['uid']:
            print(str(user))
            id = user['_id']
            recent_clip_id = user['recent_clip_id']
            clip_list = clip_list_collection.find_one({'_id': id})
            clip_list.pop('_id')
        else:
            print('attempt to login with wrong credentials')
            err = 'Invalid Credentials'
    else:
        id = 'id_' + uuid.uuid4().hex
        recent_clip_id = 'clip_' + uuid.uuid4().hex
        users_collection.insert_one({
            '_id': id,
            'name': name,
            'email': email,
            'uid': uid,
            'recent_clip_id': recent_clip_id
        })
        clip_list_collection.insert_one({
            '_id': id,
            recent_clip_id: 'Untitled'
        })
        clips_collection.insert_one({
            '_id': recent_clip_id,
            'clip_name': 'Untitled',
            'data': ''
        })
        print('user added')
    emit('login_response', (err, id, name, email, clip_list, recent_clip_id))
    
@socketio.on('get_clip')
def handle_get_clip(clip_id):
    clip_doc = clips_collection.find_one({'_id': clip_id})
    err = ''
    clip_name = ''
    clip_data = ''
    if clip_doc:
        clip_name = clip_doc['clip_name']
        clip_data = clip_doc['data']
    else:
        err = 'Invalid clip ID'
    emit('clip_response', (err, clip_id, clip_name, clip_data))

@socketio.on('update_text')
def handle_text(connection_id, user_id, clip_id, clip_name, text, timestamp):
    print('User_id: ' + user_id)
    print('Text: ' + text)
    clips_collection.update_one(
        {'_id': clip_id},
        {'$set': {'clip_name': clip_name, 'data': text}}
    )
    emit('text_response', (connection_id, text, timestamp), broadcast=True)
