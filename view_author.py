from flask import Blueprint, render_template, abort, request, redirect, url_for
from database import *
import auth

author_blueprint = Blueprint('author', __name__, template_folder='templates/author')

@author_blueprint.route('/<slug>')
def view_author(slug):
    try:
        author = Author.get(Author.slug == slug)
    except Author.DoesNotExist:
        if auth.can_edit_user(slug):
            return redirect(url_for('author.edit_author', slug=slug))
        return abort(404)
    return render_template('view-author.html', author=author, can_edit=auth.can_edit_user(slug))

@author_blueprint.route('/<slug>/edit', methods=['GET', 'POST'])
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
        return redirect(url_for('author.view_author', slug=slug))
