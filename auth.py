from flask import session
from database import *

def get_user(db_row=False):
    user = session.get('user', None)
    try:
        user_row = Author.select().where(Author.slug == user).get()
    except Author.DoesNotExist:
        del session['user']
        return None
    if db_row:
        return user_row
    else:
        return user

def authenticate(username, password):
    try:
        user = Author.get(Author.slug == username)
    except:
        raise ValueError('username invalid')
    if not user.check_password(password):
        raise ValueError('password invalid')
    session['user'] = username

def is_editor():
    if (user:=get_user(True)) is not None:
        return user.is_editor
    return False

def can_edit(article):
    if (user:=get_user(True)) is not None:
        return article.author==user or user.is_editor
    return False

def can_create():
    return get_user() is not None

def can_edit_user(username):
    if len(Author.select()) == 0:  # you need to be able to create a user
        return True
    if (me:=get_user(True)) is not None:
        try:
            user = Author.get(Author.slug == username)
        except:
            user = None
        return (me == user) or me.is_editor
    return False

def can_change_editor_status(username):
    if len(Author.select()) == 0:  # you need to be able to create a user
        return True
    if (me:=get_user(True)) is not None:
        try:
            user = Author.get(Author.slug == username)
        except:
            user = None
        return (me != user) and me.is_editor
    return False


def logout():
    del session['user']
