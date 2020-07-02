from flask import Blueprint, render_template, abort
import auth

auth_blueprint = Blueprint('auth', __name__, template_folder='templates/auth')

@auth_blueprint.route('/', methods=['GET', 'POST'])
def authenticate():
    return 'Auth page'
