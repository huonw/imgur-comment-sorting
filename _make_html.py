#!/usr/bin/env python3

from json import load
import sys
import argparse

parser = argparse.ArgumentParser(description='Convert a json representation of the Imgur gallery to a html tree.')
parser.add_argument('input', type=argparse.FileType('r'),
                    nargs='?', default=sys.stdin,
                    help='The json file to read from. Defaults to stdin.')
parser.add_argument('-I', '--no-images', action='store_true',
                    help='Disable image file generation. (Much faster!)')
parser.add_argument('-G', '--no-gallery', action='store_true',
                    help='Disable gallery page generation.')


args = parser.parse_args()

# generic tag open, close, attributes and content.
def tag(tag, attr, *contents):
    return '<{tag} {attrs}>{cont}</{tag}>'.format(
        tag=tag,
        attrs=' '.join('%s="%s"' % (k,v) for k,v in attr.items()),
        cont=''.join(str(x) for x in contents))

# common tags
def div(attr, *contents):
    return tag('div', attr, *contents)
def span(attr, *contents):
    return tag('span', attr, *contents)
def a(url, attr, *contents):
    d = {}
    d.update(attr)
    d['href'] = url
    return tag('a', d, *contents)

# the main section of a caption
def caption_body(cap):
    cap_id = 'cap_%d' % cap['id']

    expander = ''
    if cap['children']:
        expander = span({'class': 'cap-expander'}, '[+]')

    # a comment looks like:
    #
    # [+]? <author> <points> (<up> <down>) <score>
    # <caption text>
    return div({'class': 'cap-body', 'id': cap_id,
                'data-points': cap['points'], 'data-score': cap['score']},
               div({'class': 'cap-head'},
                   expander,
                   span({'class': 'cap-author'},
                        a('http://imgur.com/user/%s' % cap['author'], {},
                             cap['author'])),
                   span({'class': 'cap-points', 'title':'Points'},
                        cap['points'],
                        span({'class': 'cap-points-breakdown'},
                             span({'class':'cap-points-ups',
                                   'title':'Upvotes'},
                                  cap['ups']),
                             span({'class':'cap-points-downs',
                                   'title':'Downvotes'},
                                  -cap['downs']))),
                   span({'class': 'cap-score', 'title':'Score'},
                        '%.3f' % cap['score']),
                   span({'class': 'cap-link'},
                        a('#%s' % cap_id, {}, 'link'))),
               div({'class': 'cap-body'},
                   cap['caption']))

# caption with comments
def caption(cap):
    html = div({'class': 'cap-wrapper'},
               caption_body(cap),
               div({'class': 'cap-children'},
                   *caption_list(cap['children'])))
    return html

# a helper to do a list of captions in one go, with sorting
def caption_list(captions, sort_by='score'):
    return [caption(c) for c in sorted(captions,
                                       key=lambda x: x[sort_by],
                                       reverse=True)]

# format an image
def image(img, prev=None, next=None):
    next_link = ''
    prev_link = ''
    if prev:
        prev_link = a('%s.html' % prev,
                      {'id':'image-prev', 'class':'image-arrow'},
                      '&larr; Back')
    if next:
        next_link = a('%s.html' % next,
                      {'id':'image-next', 'class':'image-arrow'},
                      'Next &rarr;')

    return div({'id': 'image-wrapper'},
               prev_link, next_link,
               tag('img', {'id': 'image',
                           'src': 'http://i.imgur.com/%s.jpg' % img['hash']}),
               div({'id': 'image-info'},
                   a('http://imgur.com/gallery/%s' % img['hash'], {},
                     'View original image on imgur')))

# create a page, with the give title, and whether it is in a subfolder
# of the toplevel folder.
def page(title, is_in_folder, *text):
    # used for adding stuff to the end of each page, in an easily
    # adjustable way.
    page_suffix = ''
    try:
        with open('_page_suffix.html') as f:
            page_suffix = f.read()
    except:
        pass

    prefix = ''
    if is_in_folder:
        prefix = '../'

    x = tag('html', {},
            tag('head', {},
                tag('title', {}, title + ' - Imgur comment sorting'),
                tag('link', {'rel':'stylesheet',
                             'href':prefix + 'style.css'}),
                tag('script', {'type':'text/javascript',
                               'src':'https://ajax.googleapis.com/ajax/libs/jquery/1.8.2/jquery.min.js'}),
                tag('script', {'type':'text/javascript',
                               'src': prefix + 'script.js'})),
            tag('body', {},
                div({'id':'wrapper'},
                    div({'id': 'header'},
                        div({'id': 'gallery-link'},
                            a(prefix + 'gallery', {}, 'Gallery')),
                        div({'id': 'about-link'},
                            a(prefix + 'index.html', {}, 'About'))),
                    *text),
                page_suffix))

    return '<!DOCTYPE html>' + x

# page with an image and comments
def image_page(img, prev=None, next=None):
    return page(img['title'], True,
                tag('h1', {'id': 'image-title'},
                    img['title']),
                image(img, prev, next),
                div({'id': 'captions'},
                    *caption_list(img['children'])))

# page with a large number of thumbnails
def gallery_page(imgs):
    return page('Gallery', True,
                tag('h1', {'id': 'gallery-title'}, 'Gallery'),
                div({'id': 'gallery-list'},
                    *[a('%s.html' % img['hash'], {},
                        tag('img',
                            {'class':'gallery-image',
                             'src': 'http://i.imgur.com/%sb.jpg' % img['hash']}))
                      for img in imgs]))

def render_file(title, is_in_folder, fname):
    with open(fname) as f:
        return page(title, is_in_folder, f.read())




if not args.no_images or not args.no_gallery:
    try:
        imgs = load(args.input)
    except Exception as e:
        print('Error loading the image data: %s' % e, file=sys.stderr)
        sys.exit(1)

if not args.no_images:
    prev = None
    for img,next in zip(imgs, imgs[1:] + [None]):
        with open('gallery/%s.html' % img['hash'],'w') as f:
            next_hash = next['hash'] if next else None
            f.write(image_page(img, prev, next_hash))
            prev = img['hash']

if not args.no_gallery:
    with open('gallery/index.htm','w') as f:
        f.write(gallery_page(imgs))

with open('index.html', 'w') as f:
    f.write(render_file('About', False, '_index.html'))
