from flask import Flask
from database import *
from view_article import article_blueprint
from view_author import author_blueprint
from view_authentication import auth_blueprint


application = Flask(__name__)
app = application

app.register_blueprint(article_blueprint, url_prefix='/article')
app.register_blueprint(author_blueprint, url_prefix='/author')
app.register_blueprint(auth_blueprint, url_prefix='/login')


@app.route('/')
def index():
    return 'Hello Blogging!'

if __name__ == '__main__':
    app.run('0.0.0.0', 5000, debug=True)
