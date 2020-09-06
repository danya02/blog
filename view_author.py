from flask import Blueprint, render_template, abort, request, redirect, url_for
from database import *
import auth
from math import ceil
from article_list_utils import *


author_blueprint = Blueprint('author', __name__, template_folder='templates/author')

@author_blueprint.route('/list/')
def list_authors():
    return render_template('list-authors.html', authors=Author.select())

@author_blueprint.route('/list/admin/')
def admin_author_list():
    if not auth.is_editor():
        return abort(403)
    return render_template('list-authors-admin.html', authors=Author.select())


@author_blueprint.route('/<slug>/')
def view_author(slug):
    try:
        author = Author.get(Author.slug == slug)
    except Author.DoesNotExist:
        if auth.can_edit_user(slug):
            return redirect(url_for('author.edit_author', slug=slug))
        return abort(404)
    query = Article.select().where(Article.author == author).order_by(-Article.date)
    cur_page = int(request.args.get('page') or 1)

    def goto_page(num):
        return url_for('author.view_author', slug=slug, page=num)

    last_page = ceil(len(query) / ELEMENTS_PER_PAGE)
    if cur_page > last_page:
        return redirect(goto_page(last_page))

    return render_template('view-author.html', author=author, can_edit=auth.can_edit_user(slug),
                                               articles=query.paginate(cur_page, ELEMENTS_PER_PAGE),
                                               get_preview=get_preview, cur_page=cur_page,
                                               last_page=last_page, goto_page=goto_page)

@author_blueprint.route('/create/')
def create_author():
    return redirect(url_for('author.edit_author', slug=str(uuid.uuid4())))


@author_blueprint.route('/<slug>/edit/', methods=['GET', 'POST'])
def edit_author(slug):
    if not auth.can_edit_user(slug):
        return abort(403)
    no_change = 'D0N-tChangeTh3Curr3ntPassw0rd'
    create = False
    try:
        author = Author.get(Author.slug == slug)
    except Author.DoesNotExist:
        author = Author()
        create = True
        author.slug = slug

    if request.method == 'GET':
        return render_template('edit-author.html', author=author, no_change=no_change, can_change_editor=auth.can_change_editor_status(slug))

    elif request.method == 'POST':
        after_save = []
        author.name = request.form['name']
        author.slug = request.form['slug']
        if request.form['password'] != no_change:
            after_save.append(lambda:
                author.set_password(request.form['password']))
        author.description = request.form['description']
        if auth.can_change_editor_status(slug):
            author.is_editor = request.form.get('editor') == 'on'

        with db.atomic():
            author.password = b''
            author.salt = b''
            author.save(force_insert=create)
            for func in after_save:
                func()
        return redirect(url_for('author.view_author', slug=author.slug))
