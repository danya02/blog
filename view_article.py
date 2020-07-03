from flask import Blueprint, render_template, abort, request, redirect, url_for
from database import *
import auth

article_blueprint = Blueprint('article', __name__, template_folder='templates/article')

@article_blueprint.route('/<slug>')
def view_article(slug):
    # TODO: support encryption
    try:
        article = Article.get(Article.slug == slug)
    except Article.DoesNotExist:
        return 'no such article', 404
    tags = [i.tag for i in article.tags.join(Tag)]
    return render_template('view-article.html', article=article, tags=tags, can_edit=auth.can_edit(article), article_body=str(article.content, 'utf-8'))

@article_blueprint.route('/<slug>/edit', methods=['GET', 'POST'])
def edit_article(slug):
    create = False
    try:
        article = Article.get(Article.slug == slug)
    except Article.DoesNotExist:
        article = Article()
        article.slug = slug
        create = True

    if request.method == 'GET':
        time = article.date.time().strftime('%H:%M:%S')
        date = article.date.date().strftime('%Y-%m-%d')
        return render_template('edit-article.html', article=article, authors=Author.select(),
                               article_body=str(article.content or b'', 'utf-8'), time=time, date=date)
    elif request.method == 'POST':
        with db.atomic():
            after_save = []
            article.content = request.form.get('content') or article.content
            article.title = request.form.get('title') or article.title
            article.subtitle = request.form.get('subtitle') or article.subtitle

            try:
                author = Author.get(Author.slug == (request.form.get('author') or ''))
                article.author = author
            except Author.DoesNotExist:
                pass

            if not create:
                after_save.append(
                    lambda: ArticleTag.delete().where(ArticleTag.article == article))

            def add_tags():
                for tag in (request.form.get('tags') or '').split(','):
                    tag = tag.strip()
                    tag_row, _ = Tag.get_or_create(slug=tag)
                    ArticleTag.create(tag=tag_row, article=article)

            after_save.append(add_tags)

            time = request.form.get('time') or article.date.time().strftime('%H:%M:%S')
            date = request.form.get('date') or article.date.date().strftime('%Y-%m-%d')

            article.date = datetime.datetime.fromisoformat(date + 'T' + time)
            article.listed = request.form.get('listed')=='on' or article.listed

            article.encrypted = False
            article.content = request.form.get('content') or article.content

            version = request.form.get('version') or ''
            if (version != article.version) and not create:
                return render_template('edit-article.html', article=article, authors=Author.select())

            article.save(force_insert=create)
            for func in after_save:
                func()
            return redirect(url_for('article.view_article', slug=slug))

@article_blueprint.route('/tag/<tag>')
def articles_by_tag(tag):
    return 'List of articles by tag '+tag
