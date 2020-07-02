from flask import Flask
from database import *

application = Flask(__name__)
app = application

@app.route('/')
def index():
    return 'Hello Blogging!'

if __name__ == '__main__':
    app.run('0.0.0.0', 5000, debug=True)
    
