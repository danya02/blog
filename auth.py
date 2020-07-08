from flask import session
from database import *

def get_user():
    return session.get('user', None)

def authenticate(username, password):
    try:
        user = Author.get(Author.slug == username)
    except:
        raise ValueError('username invalid')
    if not user.check_password(password):
        raise ValueError('password invalid')
    session['user'] = username

def can_edit(article):
    return True
    if get_user() is None:
        return False

    user = Author.get(Author.slug == get_user())
    return article.author == user or author.is_editor

def logout():
    del session['user']
