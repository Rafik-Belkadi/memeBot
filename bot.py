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
from Meme import Meme
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


def get_access_token(filename='access token.txt'):
    return Path(get_abs_file(filename)).read_text().strip()


def get_titles(soup, element="span", html_class='td-sml-current-item-title'):
    html_elements = soup.find_all(element, {'class': html_class})
    return [i.text for i in html_elements]


def get_img_urls(soup):
    return [x['src'] for x in soup.findAll('img')][3:-1]


def get_soup(url):
    http = urllib3.PoolManager()
    response = http.request('GET', url)
    return BeautifulSoup(response.data, 'html.parser')


def get_connection():
    connection = pymysql.connect(host="localhost",
                                 user="root",
                                 password="toor",
                                 db="Memes",
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection


def handle_code(fact, connection, code):
    try:
        with connection.cursor() as c:

            query = "INSERT INTO POSTS (source, lastpost) VALUES (%s, %s)"
            c.execute(
                query, (datetime.now().date().isoformat()))

            connection.commit()
    finally:
        connection.close()


def get_facts(soup):
    titles = get_titles(soup)
    statuses = get_statuses(soup)
    sources = get_sources(soup)
    categories = get_categories(soup)
    img_urls = get_img_urls(soup)
    facts = list()
    # return a list of fact objects
    return [Fact(titles[i],
                 statuses[i],
                 sources[i],
                 categories[i],
                 img_urls[i],
                 i) for i in range(len(titles))]


def get_additional_text(skip_counts):
    i, n = skip_counts
    add_text = ""
    if i > 0:
        if i == 1:
            add_text += "\n\nI skipped over 1 fictional fact"
        else:
            add_text += "\n\nI skipped over " + \
                str(i) + " fictional facts"
    if n == 1:
        add_text += " and 1 repost" if i > 0 else "\n\n1 repost"
    elif n > 0:
        add_text += " and " + \
            str(n) + "reposts" if i > 0 else "\n\n" + str(n) + "reposts"
    if (i > 0 or n > 0):
        add_text += " to get here."
    return add_text


def check_facts(facts):
    # Returns the first 'good' fact in a list of fact objects
    fictionals = 0
    reposts = 0
    for fact in facts:
        if fact.is_fictional():
            fictionals += 1
            continue
        repost, code = fact.is_repost(get_connection())
        if not repost:
            handle_code(fact, get_connection(), code)
        if repost:
            reposts += 1
            continue
        else:
            return fact, (fictionals, reposts)


def gen_full_text(fact, add_text):
    # Extra message to precede fact, additional text to follow fact
    extra_message = "Botmin message: " + \
        ' '.join(argv[1::]) + "\n\n" if len(argv) > 1 else ""
    return extra_message + str(fact) + add_text


def get_post_image(fact):
    # Contains the code to randomly (0.1% chance) use the
    # Fact Republic logo meme as the fact photo.
    img = fact.get_image()
    if random.random() > 0.999:
        byteio = BytesIO()
        img = Image.open(get_abs_file("FactRepublic.jpg")).convert('RGB')
        img.save(byteio, format="PNG")
        img = byteio.getvalue()
    return img


def main():
    soup = get_soup('http://factrepublic.com/random-facts-generator/')
    # Generate a list of 10 fact objects from the generator
    facts = get_facts(soup)
    # select a fact by checking their validity (reposts, fictional, etc.)
    fact, skip_counts = check_facts(facts)
    # Add a kill count to the post for skipped facts if necessary
    add_text = get_additional_text(skip_counts)

    # upload post and comment
    graph, post_id = upload_post(gen_full_text(
        fact, add_text), get_access_token(), get_post_image(fact))
    comment_id = upload_comment(graph, post_id, fact.comment_text)['id']
    upload_reply(graph, comment_id)

    # 2% chance to add a bonus fact
    if random.random() > 0.98:
        fact = check_facts(facts[fact.id+1::])[0]
        comment_id = upload_comment(
            graph, post_id, str(fact), fact.get_image(), bonus=True)['id']
        upload_comment(graph, comment_id, fact.comment_text)

    # If facts are skipped, upload them to comments
    if fact.id != 0:
        for fact in facts[0:fact.id]:
            comment_id = upload_comment(graph, post_id, "Skipped fact %s:\n" %
                                        (fact.id+1) + str(fact), fact.get_image())['id']
            upload_comment(graph, comment_id, fact.comment_text)


if __name__ == '__main__':
    main()
