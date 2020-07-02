from flask import Blueprint, render_template, abort
import auth

article_blueprint = Blueprint('article', __name__, template_folder='templates/article')

@article_blueprint.route('/<slug>')
def view_article(slug):
    return 'Viewing article '+slug

@article_blueprint.route('/<slug>/edit', methods=['GET', 'POST'])
def edit_article(slug):
    return 'Editing article '+slug
