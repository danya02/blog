from flask import Blueprint, render_template, abort
import auth

author_blueprint = Blueprint('author', __name__, template_folder='templates/author')

@author_blueprint.route('/<slug>')
def view_author(slug):
    return 'Viewing author ' + slug

@author_blueprint.route('/<slug>/edit', methods=['GET', 'POST'])
def edit_author(slug):
    return 'Editing author ' + slug
