from app.main import app
from app import config

if __name__ == '__main__':
    debug = False
    if hasattr(config, 'debug'):
        if config.debug == True:
            debug = True
    app.run(debug=debug)