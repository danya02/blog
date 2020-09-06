from math import ceil
import pypandoc

ELEMENTS_PER_PAGE = 1

def do_fadeout(article):
    if article.encrypted:
        return False
    return article.crop_with_fade

def get_preview(article):
    if article.encrypted:
        return '<b>Content encrypted. Also there was a problem with this template, this is a bug!</b>'

    source = b'\r\n\r\n'.join(article.content.split(b'\r\n\r\n')[0:article.crop_at_paragraph])

    return pypandoc.convert_text(source, 'html', article.format)

def get_content(article):
    if article.encrypted:
        return '<b>Content encrypted. Visit web page and enter password to decrypt.</b>'

    return pypandoc.convert_text(article.content, 'html', article.format)
