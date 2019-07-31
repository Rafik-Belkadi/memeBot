#
# The following module contains the code for the Actual Fact Bot 5338
# Facebook Page.
#
# This software is provided under the GNU General Public License v3,
# as available at:
# https://www.gnu.org/licenses/gpl-3.0.en.html
# [Accessed 20/04/2019]
#
import urllib3
import facebook
from bs4 import BeautifulSoup
from PIL import Image
import binascii
from pathlib import Path
import pymysql.cursors
import os
import random
import time
from datetime import datetime, timedelta, date
from meme import Meme
from sys import argv
from io import BytesIO


def get_abs_file(filename):
    filepath = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(filepath, filename)


def upload_post(message, access_token, img):
    # access token is generated via the facebook developer tool.
    graph = facebook.GraphAPI(access_token)
    post = graph.put_photo(image=img,
                           message=message)
    return graph, post['post_id']


def load_image(filename):
    filename = get_abs_file(filename)
    byteio = BytesIO()
    img = Image.open(filename)
    img.save(byteio, format='PNG')
    return byteio.getvalue()


def get_access_token(filename='token.txt'):
    return Path(get_abs_file(filename)).read_text().strip()


def get_titles(soup, element="h3", html_class='_eYtD2XCVieq6emjKBH3m'):
    html_elements = soup.find_all(element, {'class': html_class})
    return [i.text for i in html_elements]


def get_img_urls(soup):
    myImages =  [x['src'] for x in soup.findAll('img', '_2_tDEnGMLxpM6uOa2kaDB3 ImageBox-image media-element')]
    print(myImages)
    return myImages

def get_soup(url):
    http = urllib3.PoolManager()
    response = http.request('GET', url)
    return BeautifulSoup(response.data, 'html.parser')






def get_memes(soup):
    titles = get_titles(soup)
    img_urls = get_img_urls(soup)
    memes = list()
    # return a list of fact objects
    return [Meme(titles[i],
                 img_urls[i]) for i in range(len(img_urls))]

def main():
    soup = get_soup('https://www.reddit.com/r/dankmemes/')
    # Generate a list of 10 fact objects from the generator
    memes = get_memes(soup)
    # upload post and comment
    graph, post_id = upload_post(memes[0].title, get_access_token(), memes[0].img_url)


if __name__ == '__main__':
    main()
