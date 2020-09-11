from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 #############WARNING: remove in production

@app.route('/')
def index_route():
    return render_template('index.html')
