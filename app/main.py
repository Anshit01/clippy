from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, send, emit
from flask_session import Session
from pymongo import MongoClient
import uuid
import time

from app import config

cluster = MongoClient(f'mongodb+srv://{config.DB_USERNAME}:{config.DB_PASSWORD}@cluster0.erdus.mongodb.net/database?retryWrites=true&w=majority')
database = cluster['database']
users_collection = database.users
clip_list_collection = database.clip_list
clips_collection = database.clips

app = Flask(__name__)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 ############# WARNING: remove in production
app.secret_key = config.APP_SECRET_KEY

app.config['SESSION_TYPE'] = 'mongodb'
app.config['SESSION_MONGODB'] = cluster
Session(app)

socketio = SocketIO(app, manage_session=False)
socketio.init_app(app, cors_allowed_origins="*") ########### WARNING: remove in production



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
    print(is_loggedin())
    if is_loggedin():
        err = ''
        id = session['user_id']
        name = ''
        email = ''
        recent_clip_id = ''
        clip_list = {}
        user_data = users_collection.find_one({'_id': id})
        if user_data:
            name = user_data['name']
            email = user_data['email']
            recent_clip_id = user_data['recent_clip_id']
            clip_list = dict(clip_list_collection.find({'_id': id}))
            if clip_list:
                clip_list.pop('_id')
        else:
            err = 'Invalid Credentials'
        photo_URL = session['photo_URL']
        emit('login_response', (err, id, name, email, clip_list, recent_clip_id, photo_URL))

@socketio.on('login')
def handle_login(name, email, uid, photo_URL):
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
            login(id, name, email, photo_URL)
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
        login(id, name, email, photo_URL)
    emit('login_response', (err, id, name, email, clip_list, recent_clip_id, photo_URL))
    
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

def login(user_id, name, email, photo_URL):
    session['user_id'] = user_id
    session['name'] = name
    session['email'] = email
    session['photo_URL'] = photo_URL

def logout():
    session.pop('user_id', None)
    session.pop('name', None)
    session.pop('email', None)
    session.pop('photo_URL', None)

def is_loggedin():
    if 'user_id' in session:
        return True
    print('not logged in')
    return False