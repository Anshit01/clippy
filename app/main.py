from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, send
from pymongo import MongoClient

from app import config


app = Flask(__name__)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 #############WARNING: remove in production
app.secret_key = config.APP_SECRET_KEY

socketio = SocketIO(app)
socketio.init_app(app, cors_allowed_origins="*") ########### WARNING: remove in production

cluster = MongoClient(f'mongodb+srv://{config.DB_USERNAME}:{config.DB_PASSWORD}@cluster0.erdus.mongodb.net/database?retryWrites=true&w=majority')
database = cluster['database']
users_collection = database.users
clips_collection = database.clips


@app.route('/')
def index_route():
    return render_template('index.html')

@socketio.on('message')
def handleMessage(msg):
    print('Message: ' + msg)
    send(msg, broadcast=True)