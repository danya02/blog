from flask import Blueprint, render_template, abort, request, redirect, url_for, Response
from database import *
import uuid
import auth

file_blueprint = Blueprint('file', __name__, template_folder='templates/file')

@file_blueprint.route('/<uuid:uuid>/', methods=['GET', 'POST'])
def view_file(uuid):
    try:
        file = File.get(File.uuid == uuid)
    except File.DoesNotExist:
        return abort(404)
    if not file.encrypted:
        print(request.headers.get('if-none-match'), file.hash, request.headers.get('if-none-match') == file.hash)
        if request.headers.get('if-none-match') == f'"{file.hash}"':
            resp = Response('')
            resp.status_code = 304
            resp.set_etag(file.hash, False)
            resp.cache_control.max_age = 5
            resp.cache_control.public = True
            return resp
        resp = Response(file.content)
        resp.content_type = file.mimetype
        resp.headers.set('Content-Disposition', 'attachment', filename=file.filename)
        resp.cache_control.max_age = 5
        resp.cache_control.public = True
        resp.set_etag(file.hash, False)
        return resp
    else:
        if request.method == 'GET':
            return render_template('unlock-file.html', file=file), 401
        elif request.method == 'POST':
            try:
                content = file.decrypt(request.form['password'])
            except ValueError:
                return render_template('unlock-file.html', file=file, error=True)
            resp = Response(content)
            resp.headers.content_type = file.mimetype
            resp.headers.set('Content-Disposition', 'attachment', filename=file.filename)
            # not setting cache-control or etag because this is in response to a POST
            return resp

@file_blueprint.route('/create/')
def create_file():
    return redirect(url_for('file.edit_file', uuid=str(uuid.uuid4())))

@file_blueprint.route('/<uuid:uuid>/edit/', methods=['GET', 'POST'])
def edit_file(uuid):
    if not auth.can_create():
        return abort(403)
    create = False
    try:
        file = File.get(File.uuid == uuid)
    except File.DoesNotExist:
        file = File()
        file.uuid = uuid
        create = True

    if request.method == 'GET':
        if not file.encrypted:
            return render_template('edit-file.html', file=file, password='')
        else:
            return render_template('unlock-file.html', file=file), 401
    elif request.method == 'POST':
        if request.form['action'] == 'unlock':
            try:
                file.decrypt_in_place(request.form['password'])
            except ValueError:
                return render_template('unlock-file.html', file=file, error=True)
            return render_template('edit-file.html', file=file, password=request.form['password'])
        elif request.form['action'] == 'edit':
            file_sent = request.files.get('content') is not None
            if file_sent:
                file.set_content(request.files['content'].stream.read())
            file.mimetype = request.form['mimetype'] or (request.files['content'].mimetype if file_sent else None) or file.mimetype or 'application/octet-stream'

            try:
                file.decrypt_in_place(request.form.get('old_password'))
            except ValueError:
                return render_template('unlock-file.html', file=file, error=True), 401

            if request.form.get('password'):
                file.encrypt_in_place(request.form['password'])
            file.filename = request.form['filename'] or (request.files['content'].filename if file_sent else None) or file.filename or 'untitled.bin'
            file.save(force_insert=create)
            return redirect(url_for('file.edit_file', uuid=uuid))
