from flask import Blueprint, render_template, abort, request, redirect, url_for, Response
from database import *
import uuid
import auth
import pypandoc
from article_list_utils import *

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

    next_article = None
    prev_article = None
    try:
        prev_article = Article.select(Article.slug).where(Article.listed).order_by(Article.date).where(Article.date > article.date).get()
    except Article.DoesNotExist:
        pass
    try:
        next_article = Article.select(Article.slug).where(Article.listed).order_by(-Article.date).where(Article.date < article.date).get()
    except Article.DoesNotExist:
        pass

    if not article.encrypted:
        return render_template('view-article.html', article=article, tags=tags, can_edit=auth.can_edit(article), article_body=pandoc_article(article), next_article=next_article, prev_article=prev_article)
    else:
        if request.method == 'GET':
            return render_template('view-article.html', article=article, tags=tags, can_edit=auth.can_edit(article), encrypted=True, protected=True, next_article=next_article, prev_article=prev_article)
        elif request.method == 'POST':
            try:
                content = article.decrypt(request.form['password'])
            except ValueError:
                return render_template('view-article.html', article=article, tags=tags, can_edit=auth.can_edit(article), encrypted=True, protected=True, error=True, next_article=next_article, prev_article=prev_article)
            article.content = content  # because pandoc_article takes an Article. we don't save this, so it's fine.
            return render_template('view-article.html', article=article, tags=tags, can_edit=auth.can_edit(article), article_body=pandoc_article(article), protected=True, next_article=next_article, prev_article=prev_article)

@article_blueprint.route('/<slug>/source/', methods=['GET', 'POST'])
def view_article_source(slug):
    try:
        article = Article.get(Article.slug == slug)
    except Article.DoesNotExist:
        return abort(404)
    tags = [i.tag for i in article.tags.join(Tag)]
    if not article.encrypted:
        return Response(article.content, mimetype='text/plain')
    prev_article = None
    next_article = None

    try:
        prev_article = Article.select(Article.slug).where(Article.listed).order_by(Article.date).where(Article.date > article.date).get()
    except Article.DoesNotExist:
        pass
    try:
        next_article = Article.select(Article.slug).where(Article.listed).order_by(-Article.date).where(Article.date < article.date).get()
    except Article.DoesNotExist:
        pass

    else:
        if request.method == 'GET':
            return render_template('view-article.html', unlock_source=True, article=article, tags=tags, can_edit=auth.can_edit(article), encrypted=True, protected=True, next_article=next_article, prev_article=prev_article)
        elif request.method == 'POST':
            try:
                content = article.decrypt(request.form['password'])
            except ValueError:
                return render_template('view-article.html', unlock_source=True, article=article, tags=tags, can_edit=auth.can_edit(article), encrypted=True, protected=True, error=True, next_article=next_article, prev_article=prev_article)
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
                                    tags=tags, this_user=auth.get_user(True))
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

                this_user = auth.get_user(True)
                try:
                    author = Author.get(Author.slug == (request.form.get('author') or ''))
                    if this_user.is_editor:
                        article.author = author
                    else:
                        article.author = this_user
                except Author.DoesNotExist:
                    article.author = this_user

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
                article.listed = request.form.get('listed')=='on'

                article.content = bytes(request.form.get('content'), 'utf-8') or article.content
                article.format = request.form.get('format') or article.format
                try:
                    crop = int(request.form.get('crop_at_paragraph'))
                except:
                    crop = article.crop_at_paragraph
                article.crop_at_paragraph = crop

                article.crop_with_fade = request.form.get('crop_with_fade')=='on'

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
                                            time=time, date=date, article_body=str(article.content, 'utf-8'), tags=tags,
                                            this_user=auth.get_user(True))

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
                                    password=request.form['password'], tags=tags, this_user=auth.get_user(True))

@article_blueprint.route('/<slug>/delete', methods=['POST'])
def delete_article(slug):
    try:
        article = Article.get(Article.slug == slug)
    except Article.DoesNotExist:
        return redirect(url_for('article.edit_article', slug=slug))

    if not auth.can_edit(article):
        return abort(403)

    if request.form['confirm'] == 'on':
        article.delete_instance()
        return redirect(url_for('index'))
    return redirect(url_for('article.edit_article', slug=slug))


@article_blueprint.route('/tag/<tag>')
def articles_by_tag(tag):
    try:
        tag = Tag.get(Tag.slug==tag)
    except Tag.DoesNotExist:
        return abort(404)
    query = Article.select().join(ArticleTag).where(ArticleTag.tag == tag).where(Article.listed).order_by(-Article.date)
    cur_page = int(request.args.get('page') or 1)

    def goto_page(num):
        return url_for('article.articles_by_tag', page=num)

    last_page = ceil(len(query) / ELEMENTS_PER_PAGE)
    if cur_page > last_page:
        return redirect(goto_page(last_page))
    return render_template('list-article.html', articles=query.paginate(cur_page, ELEMENTS_PER_PAGE),
                                                get_preview=get_preview, cur_page=cur_page,
                                                last_page=last_page, goto_page=goto_page,
                                                tag=tag.slug)

@article_blueprint.route('/tag/<tag>/atom.xml')
@article_blueprint.route('/tag/<tag>/atom/')
@article_blueprint.route('/tag/<tag>/feed.xml')
@article_blueprint.route('/tag/<tag>/feed/')
def articles_by_tag_feed(tag):
    try:
        tag = Tag.get(Tag.slug==tag)
    except Tag.DoesNotExist:
        return abort(404)
    query = Article.select().join(ArticleTag).join(Tag).where(ArticleTag.tag == tag).where(Article.listed).order_by(-Article.date).limit(5)
    return Response(render_template('atom-syndication.xml', what_here=f'posts with tag "{tag.slug}"', url_here=url_for('article.articles_by_tag', tag=tag.slug,  _external=True), articles=list(query), get_content=get_content), mimetype='application/atom+xml')


@article_blueprint.route('/admin_list/')
def admin_article_list():
    if not auth.can_create():
        return abort(403)
    return render_template('admin-list-article.html', articles=Article.select(Article.slug, Article.title, Article.subtitle, Article.author, Article.listed, Article.encrypted, Article.date).order_by(-Article.date))
