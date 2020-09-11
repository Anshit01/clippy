from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index_route():
    return render_template('index.html')
