from app.main import app, socketio
from app import config

if __name__ == '__main__':
    debug = False
    if hasattr(config, 'debug'):
        if config.debug == True:
            debug = True
    socketio.run(app, debug=debug)