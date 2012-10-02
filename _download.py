#!/usr/bin/env python3

from urllib.request import urlopen, URLError
from json import loads, dump
import sys
from math import sqrt
import argparse

parser = argparse.ArgumentParser(description='Download a certain number of the most recent images and their captions from the imgur gallery.')
parser.add_argument('count', nargs='?', type=int, default=100,
                    help='The number of images to download.')
parser.add_argument('-o', '--output', type=argparse.FileType('w'),
                    default=sys.stdout,
                    help='The file to output to, default is stdout.')
args = parser.parse_args()

def get_json(url):
    data = urlopen(url).read().decode('utf-8')
    return loads(data)

z_quant = 1.96 # alpha = 0.05
def score(ups, downs, z=z_quant):
    n = max(ups, 0) + max(0, downs)
    if n <= 0:
        return 0

    p = ups / n
    z2_n = z**2 / n
    return (p + z2_n / 2 - z * sqrt((p*(1-p) + z2_n / 4) / n)) / (1 + z2_n)

GALLERY_URL = 'http://imgur.com/gallery/page/{page_no:d}.json'
IMAGE_URL = 'http://imgur.com/gallery/{hash:s}.json'

page = 0
# list of all the images, in reverse chronological order.
images = []

count = args.count

while count > 0:
    try:
        # download my current page.
        gallery = get_json(GALLERY_URL.format(page_no = page))
        page += 1 # next page
    except Exception as e: # failed!
        print('Error opening gallery page %d: %s' % (page, e),
              file=sys.stderr)
        sys.exit(1)

    for img in gallery['data']: # go through the images on this page.
        if count == 0: # seen enough pictures
            break

        try: # download more info about the current image.
            print('[%d] Downloading %s' % (count, img['hash']), file=sys.stderr)
            image = get_json(IMAGE_URL.format(hash = img['hash']))
        except Exception as e:
            print('Error opening image %s: %s' % (img['hash'], e),
                  file=sys.stderr)
            continue # something failed, skip to the next one.

        caps = image['data']['captions']

        # nested comments, starting at the image.
        img['children'] = []
        # top level comments have parent_id = 0
        caps_dict = {0: img}

        # go through and set up the nested structure (as well as the
        # comment scores.)
        #
        # order by date, so that comments that are later come after so
        # in theory the parent_id is already in the dictionary,
        # because it'd be weird if a reply happened before the parent.
        for c in sorted(caps, key=lambda c: c['datetime']):
            c['score'] = score(c['ups'],c['downs'])
            c['children'] = []

            try:
                caps_dict[c['parent_id']]['children'].append(c)
            except KeyError: # weird...
                print('No parent for a comment',file=sys.stderr)
            caps_dict[c['id']] = c

        images.append(img)

        count -= 1 # done one more image.


dump(images, args.output)


