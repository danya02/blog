from flask import Flask, send_file, request, render_template
from database import *
from view_article import article_blueprint
from view_author import author_blueprint
from view_authentication import auth_blueprint
import traceback
import pypandoc


application = Flask(__name__)
app = application

app.secret_key = b'super secret super spoopy'
app.register_blueprint(article_blueprint, url_prefix='/article')
app.register_blueprint(author_blueprint, url_prefix='/author')
app.register_blueprint(auth_blueprint, url_prefix='/login')


@app.route('/')
def index():
    return 'Hello Blogging!'

@app.route('/database-backup.sqlite')
def fetch_database():
    return send_file(DB_PATH)

@app.route('/pandoc', methods=['GET', 'POST'])
def pandoc_debug():
    if request.method == 'GET':
        return render_template('pandoc-debug.html', format='md', source='Write your markup here...')
    elif request.method == 'POST':
        try:
            result = pypandoc.convert_text(request.form['source'], 'html', request.form['format'])
            return render_template('pandoc-debug.html', format=request.form['format'], source=request.form['source'], result=result)
        except:
            return render_template('pandoc-debug.html', format=request.form['format'], source=request.form['source'], error=traceback.format_exc())





if __name__ == '__main__':
    app.run('0.0.0.0', 5000, debug=True)
