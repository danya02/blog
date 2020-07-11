from flask import Blueprint, render_template, abort, request, redirect, url_for
import auth

auth_blueprint = Blueprint('auth', __name__, template_folder='templates/auth')

@auth_blueprint.route('/', methods=['GET', 'POST'])
def authenticate():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        try:
            auth.authenticate(request.form['username'], request.form['password'])
        except ValueError as e:
            return render_template('login.html', error=e.args[0])
        return redirect(url_for('index'))

@auth_blueprint.route('/logout/')
def logout():
    auth.logout()
    return redirect(url_for('index'))
