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

def is_editor():
    if get_user() is None:
        return False

    user = Author.get(Author.slug == get_user())
    return user.is_editor

def can_edit(article):
    return True

    if get_user() is None:
        return False

    user = Author.get(Author.slug == get_user())
    return article.author == user or user.is_editor

def can_create():
    return get_user() is not None

def can_edit_user(username):
    if len(Author.select()) == 0:  # you need to be able to create a user
        return True
    if get_user() == None:
        return False
    try:
        user = Author.get(Author.slug == username)
    except:
        user = None
    me = Author.get(Author.slug == get_user())
    return (me == user) or me.is_editor

def can_change_editor_status(username):
    if len(Author.select()) == 0:  # you need to be able to create a user
        return True

    if get_user() == None:
        return False
    try:
        user = Author.get(Author.slug == username)
    except:
        user = None
    me = Author.get(Author.slug == get_user())
    return (me != user) and me.is_editor


def logout():
    del session['user']
