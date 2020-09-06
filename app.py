from flask import Flask, send_file, request, render_template, redirect, url_for
from database import *
from view_article import article_blueprint
from view_author import author_blueprint
from view_authentication import auth_blueprint
from view_file import file_blueprint

import os
import traceback
import pypandoc
from article_list_utils import *


import auth

application = Flask(__name__)
app = application

app.secret_key = b'super secret super spoopy'
app.register_blueprint(article_blueprint, url_prefix='/article')
app.register_blueprint(author_blueprint, url_prefix='/author')
app.register_blueprint(auth_blueprint, url_prefix='/login')
app.register_blueprint(file_blueprint, url_prefix='/file')



@app.route('/')
def index():
    query = Article.select().where(Article.listed).order_by(-Article.date)
    cur_page = int(request.args.get('page') or 1)

    def goto_page(num):
        return url_for('index', page=num)

    last_page = ceil(len(query)/ELEMENTS_PER_PAGE)
    if cur_page > last_page:
        return redirect(goto_page(last_page))
    return render_template('article/list-article.html', articles=query.paginate(cur_page, ELEMENTS_PER_PAGE),
                                                        get_preview=get_preview, cur_page=cur_page,
                                                        last_page=last_page, goto_page=goto_page)

@app.route('/database-backup.sqlite')
def fetch_database():
    file = DB_PATH+'.backup'
    try:
        os.unlink(file)
    except FileNotFoundError:
        pass
    db.execute_sql('vacuum into ?;', (file, ))
    return send_file(file)

@app.route('/pandoc/', methods=['GET', 'POST'])
def pandoc_debug():
    if request.method == 'GET':
        return render_template('pandoc-debug.html', format='md', source='Write your markup here...')
    elif request.method == 'POST':
        try:
            result = pypandoc.convert_text(request.form['source'], 'html', request.form['format'])
            return render_template('pandoc-debug.html', format=request.form['format'], source=request.form['source'], result=result)
        except:
            return render_template('pandoc-debug.html', format=request.form['format'], source=request.form['source'], error=traceback.format_exc())

@app.route('/creation-tools/')
def creation_tools():
    if auth.can_create():
        return render_template('creation-tools.html', is_editor=auth.is_editor(), db_size=os.path.getsize(DB_PATH))
    return abort(403)

@app.route('/vacuum/', methods=['POST'])
def vacuum_db():
    if not auth.can_create():
        return abort(403)
    db.execute_sql('vacuum;')
    return redirect(url_for('creation_tools'))

if __name__ == '__main__':
    app.run('0.0.0.0', 5000, debug=True)
