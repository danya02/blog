from flask import Blueprint, render_template, abort, request, redirect, url_for, Response
from database import *
import uuid
import auth
import pypandoc

article_blueprint = Blueprint('article', __name__, template_folder='templates/article')

def pandoc_article(article):
    return pypandoc.convert_text(article.content, 'html', article.format)


@article_blueprint.route('/<slug>/', methods=['GET', 'POST'])
def view_article(slug):
    try:
        article = Article.get(Article.slug == slug)
    except Article.DoesNotExist:
        return abort(404)
    tags = [i.tag for i in article.tags.join(Tag)]
    if not article.encrypted:
        return render_template('view-article.html', article=article, tags=tags, can_edit=auth.can_edit(article), article_body=pandoc_article(article))
    else:
        if request.method == 'GET':
            return render_template('view-article.html', article=article, tags=tags, can_edit=auth.can_edit(article), encrypted=True, protected=True)
        elif request.method == 'POST':
            try:
                content = article.decrypt(request.form['password'])
            except ValueError:
                return render_template('view-article.html', article=article, tags=tags, can_edit=auth.can_edit(article), encrypted=True, protected=True, error=True)
            article.content = content  # because pandoc_article takes an Article. we don't save this, so it's fine.
            return render_template('view-article.html', article=article, tags=tags, can_edit=auth.can_edit(article), article_body=pandoc_article(article), protected=True)

@article_blueprint.route('/<slug>/source/', methods=['GET', 'POST'])
def view_article_source(slug):
    try:
        article = Article.get(Article.slug == slug)
    except Article.DoesNotExist:
        return abort(404)
    tags = [i.tag for i in article.tags.join(Tag)]
    if not article.encrypted:
        return Response(article.content, mimetype='text/plain')
    else:
        if request.method == 'GET':
            return render_template('view-article.html', article=article, tags=tags, can_edit=auth.can_edit(article), encrypted=True, protected=True)
        elif request.method == 'POST':
            try:
                content = article.decrypt(request.form['password'])
            except ValueError:
                return render_template('view-article.html', article=article, tags=tags, can_edit=auth.can_edit(article), encrypted=True, protected=True, error=True)
            return Response(content, mimetype='text/plain')

@article_blueprint.route('/create/')
def create_article():
    return redirect(url_for('article.edit_article', slug=str(uuid.uuid4())))

@article_blueprint.route('/<slug>/edit/', methods=['GET', 'POST'])
def edit_article(slug):
    create = False
    try:
        article = Article.get(Article.slug == slug)
    except Article.DoesNotExist:
        article = Article()
        article.slug = slug
        create = True
    if create and not auth.can_create():
        return abort(403)
    if not create and not auth.can_edit(article):
        return abort(403)

    if request.method == 'GET':
        if not article.encrypted:
            time = article.date.time().strftime('%H:%M:%S')
            date = article.date.date().strftime('%Y-%m-%d')
            tags = [i.tag for i in article.tags.join(Tag)]

            return render_template('edit-article.html', article=article, authors=Author.select(),
                                    article_body=str(article.content or b'', 'utf-8'), time=time, date=date,
                                    tags=tags)
        else:
            return render_template('unlock-article.html', article=article)
    elif request.method == 'POST':
        if request.form['action'] == 'edit':
            with db.atomic():
                after_save = []
                article.content = request.form.get('content') or article.content
                article.title = request.form.get('title') or article.title
                article.subtitle = request.form.get('subtitle') or article.subtitle
                article.slug = request.form.get('slug') or article.slug

                try:
                    author = Author.get(Author.slug == (request.form.get('author') or ''))
                    article.author = author
                except Author.DoesNotExist:
                    pass

                def add_tags():
                    for tag in (request.form.get('tags') or '').split(','):
                        if tag:
                            tag = tag.strip()
                            tag_row, _ = Tag.get_or_create(slug=tag)
                            ArticleTag.get_or_create(tag=tag_row, article=article)

                after_save.append(add_tags)

                time = request.form.get('time') or article.date.time().strftime('%H:%M:%S')
                date = request.form.get('date') or article.date.date().strftime('%Y-%m-%d')

                article.date = datetime.datetime.fromisoformat(date + 'T' + time)
                article.listed = request.form.get('listed')=='on' or article.listed

                article.content = bytes(request.form.get('content'), 'utf-8') or article.content
                article.format = request.form.get('format') or article.format

                article.encrypted = False
                password = request.form.get('password') or ''
                if password != '':
                    after_save.append(lambda: article.encrypt_in_place(password))

                version = request.form.get('version') or ''
                if (version != str(article.version)) and not create:
                    tags = []
                    class Null:
                        pass
                    for tag in (request.form.get('tags') or '').split(','):
                        obj = Null()
                        obj.slug = tag
                        tags.append(obj)
                    return render_template('edit-article.html', article=article, authors=Author.select(), wrong_version=True,
                                            time=time, date=date, article_body=str(article.content, 'utf-8'), tags=tags)

                article.version = uuid.uuid4()
                article.save(force_insert=create)
                for func in after_save:
                    func()
                return redirect(url_for('article.view_article', slug=article.slug))
        elif request.form['action'] == 'unlock':
            try:
                content = article.decrypt(request.form['password'])
            except ValueError:
                return render_template('unlock-article.html', article=article, error=True)
            time = article.date.time().strftime('%H:%M:%S')
            date = article.date.date().strftime('%Y-%m-%d')
            tags = [i.tag for i in article.tags.join(Tag)]

            return render_template('edit-article.html', article=article, authors=Author.select(),
                                    article_body=str(content or b'', 'utf-8'), time=time, date=date,
                                    password=request.form['password'], tags=tags)

@article_blueprint.route('/<slug>/delete', methods=['POST'])
def delete_article(slug):
    try:
        article = Article.get(Article.slug == slug)
    except Article.DoesNotExist:
        return redirect(url_for('article.edit_article', slug=slug))

    if request.form['confirm'] == 'on':
        article.delete_instance()
        return redirect(url_for('index'))
    return redirect(url_for('article.edit_article', slug=slug))


@article_blueprint.route('/tag/<tag>')
def articles_by_tag(tag):
    return 'List of articles by tag '+tag
