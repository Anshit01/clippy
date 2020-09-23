from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, send, emit, join_room, leave_room, rooms
from flask_session import Session
from pymongo import MongoClient
import uuid
import random
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
    if is_loggedin():
        return render_template('index.html', loggedin=True)
    else:
        return render_template('index.html', loggedin=False)

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
        join_room(id)
        name = ''
        email = ''
        recent_clip_id = ''
        clip_list = {}
        user_data = users_collection.find_one({'_id': id})
        if user_data:
            name = user_data['name']
            email = user_data['email']
            recent_clip_id = user_data['recent_clip_id']
            clip_list = clip_list_collection.find_one({'_id': id})
            if clip_list:
                clip_list.pop('_id')
        else:
            err = 'Invalid Credentials'
        photo_URL = session['photo_URL']
        e, clip_name, clip_data = get_clip(recent_clip_id)
        emit('login_response', (err, id, name, email, clip_list, photo_URL, recent_clip_id, clip_name, clip_data))

@socketio.on('login')
def handle_login(name, email, uid, photo_URL):
    print('Login: ' + name + ' ' + email + ' ' + uid)
    user = users_collection.find_one({'email': email})
    err = None
    recent_clip_id = ''
    clip_name = ''
    clip_data = ''
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
    if err is None:
        e, clip_name, clip_data = get_clip(recent_clip_id)
    emit('login_response', (err, id, name, email, clip_list,photo_URL, recent_clip_id, clip_name, clip_data))

@socketio.on('logout')
def handle_logout():
    err = ''
    res = ''
    if is_loggedin():
        logout()
        res = 'Logged out successfully'
    else:
        err = 'Already logged out'
    emit('logout_response', (err, res))

@socketio.on('new_clip')
def handle_new_clip(user_id, clip_name, clip_data, old_clip_id):
    user_doc = users_collection.find_one({'_id': user_id}, {'recent_clip_id': 1})
    err = ''
    if(user_doc):
        new_clip_id = 'clip_' + uuid.uuid4().hex
        clip_list_collection.update_one(
            {'_id': user_id},
            {'$set': {new_clip_id: clip_name}}
        )
        clips_collection.insert_one({
            '_id': new_clip_id,
            'clip_name': clip_name,
            'data': clip_data
        })
        users_collection.update_one(
            {'_id': user_id},
            {'$set': {'recent_clip_id': new_clip_id}}
        )
        emit('new_clip_response', (err, new_clip_id, clip_name, clip_data, old_clip_id), room=user_id)
    else:
        err = 'Unauthorized access'
        emit('new_clip_response', (err, '', clip_name, clip_data, old_clip_id))


@socketio.on('get_clip')
def handle_get_clip(user_id, clip_id):
    user_doc = users_collection.find_one({'_id': user_id})
    err = ''
    clip_name = ''
    clip_data = ''
    if user_doc:
        err, clip_name, clip_data = get_clip(clip_id)
        users_collection.update_one(
            {'_id': user_id},
            {'$set': {'recent_clip_id': clip_id}}
        )
    else:
        err = 'Invalid User ID'
    emit('clip_response', (err, clip_id, clip_name, clip_data))


@socketio.on('delete_clip')
def handle_delete_clip(connection_id, clip_id):
    print('delete: '+ clip_id)
    if is_loggedin():
        user_id = session['user_id']
        clip_list_collection.update_one(
            {'_id': user_id},
            {'$unset': {clip_id: ''}}
        )
        clips_collection.delete_one({'_id': clip_id})
        clips_list = clip_list_collection.find_one({'_id': user_id}, {'_id': 0})
        new_clip_id = ''
        if len(clips_list):
            new_clip_id = next(iter(clips_list))
        emit('delete_clip_response', (connection_id, clip_id, new_clip_id), room=user_id)


@socketio.on('update_text')
def handle_text(connection_id, user_id, clip_id, clip_name, text, timestamp):
    # print('User_id: ' + user_id)
    # print('Room:' + str(rooms()))
    # print('Text: ' + text)
    if is_loggedin():
        if clip_name == '':
            clip_name = 'clip-' + str(random.randint(11, 99))
        clips_collection.update_one(
            {'_id': clip_id},
            {'$set': {'clip_name': clip_name, 'data': text}}
        )
        clip_list_collection.update_one(
            {'_id': user_id},
            {'$set': {clip_id: clip_name}}
        )
        emit('text_response', (connection_id, text, clip_id, clip_name, timestamp), room=user_id)



def get_clip(clip_id):
    clip_doc = clips_collection.find_one({'_id': clip_id})
    err = ''
    clip_name = ''
    clip_data = ''
    if clip_doc:
        clip_name = clip_doc['clip_name']
        clip_data = clip_doc['data']
    else:
        err = 'Invalid clip ID'
    return (err, clip_name, clip_data)

def login(user_id, name, email, photo_URL):
    session['user_id'] = user_id
    session['name'] = name
    session['email'] = email
    session['photo_URL'] = photo_URL
    join_room(user_id)
    print(rooms())

def logout():
    leave_room(session['user_id'])
    session.pop('user_id', None)
    session.pop('name', None)
    session.pop('email', None)
    session.pop('photo_URL', None)

def is_loggedin():
    if 'user_id' in session:
        return True
    print('not logged in')
    return False