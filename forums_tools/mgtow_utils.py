# from forums_tools.utils import get_html_session
# from forums_tools.dateutil.relativedelta import relativedelta
from utils import get_html_session
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import traceback
import re

week_day_list = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6,
                 "Yesterday": -1, "Today": -1}

month_list = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10,
              "Nov": 11, "Dec": 12, }

LINKS_REGEX = r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?'

INCELS_URL = "https://www.mgtow.com/forums"
INCELS_THREAD_BASE = "https://www.mgtow.com/"


def build_index(link, dst, nump):
    session = get_html_session()

    # Gets the first page
    r = session.get(INCELS_THREAD_BASE + link+"page/" + str(1))

    # Find number of pages
    number_of_pages = int(r.html.find(".bbp-pagination a")
                          [1].text.replace(",", ""))

    # Get a name of subforum
    subforum = r.html.find(".bbp-breadcrumb-current")[0].text

    df_list = []

    # Get data index
    for page_num in range(1, number_of_pages + 1, 1):
        print("Forum: {0} - Page {1}/{2}".format(subforum,
                                                 page_num, number_of_pages))
        r = session.get(INCELS_THREAD_BASE + link+"page/" + str(page_num))

        for thread in r.html.find(".status-publish"):

            if thread.find('.bbp-author-name'):
                author_topic = thread.find(' .bbp-author-name')[0].text,
            else:
                author_topic = None

            thread_dict = {
                "type": None,
                "title": thread.find('.bbp-topic-permalink')[0].text,
                "link": list(thread.find('.bbp-topic-permalink')[0].links)[0],
                "author_topic": author_topic,
                "replies": thread.find(' .bbp-topic-reply-count')[0].text,
                "views":  thread.find(' .bbp-topic-voice-count')[0].text,
                "subforum": subforum
            }

            df_list.append(thread_dict)

    # Export data index
    subforum = subforum.replace(" ", "_")
    df = pd.DataFrame(df_list)
    df.to_csv(dst.replace(".csv", "")+"_"+subforum+".csv")


def build_topics_index(src, dst, nump):

    session = get_html_session()

    # Gets the first page
    r = session.get(INCELS_URL)

    df_list = []

    # Processing data topics index
    for thread in r.html.find("#grid .element-item "):

        thread_dict = {
            "link": list(thread.find("a")[0].links)[0],
            "subforum": thread.find('h4')[0].text,
        }

        df_list.append(thread_dict)

    # Export data topics index
    df = pd.DataFrame(df_list)
    df.to_csv(dst)


def get_thread(link, session=None):

    session = get_html_session(session)
    number_of_pages_post = get_num_pages_post(link, session)
    df_list = []

    # Processing post pages
    for thread_page in range(1, number_of_pages_post + 1, 1):

        post_elemenets = get_posts_page(link, thread_page, session)
        N = len(post_elemenets[0])

        for i in range(N):
            try:
                element = []
                element.append(post_elemenets[0][i])
                element.append(post_elemenets[1][i])

                post_dict = get_post(element, link, session)
                post_dict['number_post'] = i + 1

                df_list.append(post_dict)
            except Exception:
                traceback.print_exc()
                print("problem with post", i, ":", link)

    # Export data posts
    df = pd.DataFrame(df_list)
    df.to_csv("./data/forums/mgtow/posts/" +
              re.sub("/", "", link[9:].replace(" ", "_")) + ".csv", index=False)


def get_num_pages_post(link, session=None):
    session = get_html_session(session)
    r_post = session.get(INCELS_THREAD_BASE + link)

    # Get number pages for post
    try:
        number_of_pages_post = int(r_post.html.find(
            ".bbp-pagination-links a")[-2].text)
    except IndexError:
        number_of_pages_post = 1
    return number_of_pages_post


def get_posts_page(link, thread_page, session=None):
    session = get_html_session(session)
    r_post = session.get(INCELS_THREAD_BASE + link +
                         "page/" + str(thread_page))

    # Get list elements post
    post_elemenet = []
    post_elemenet.append(r_post.html.find('.hentry'))
    post_elemenet.append(r_post.html.find('.bbp-reply-header'))

    return post_elemenet


def get_post(post, link, session=None):

    # Verify existence of sub-elements
    if post[1].find(".bbp-reply-post-date"):
        date_post = post[1].find(
            ".bbp-reply-post-date")[0].text.replace("\n", "")
    else:
        date_post = None

    if post[0].find(".bbp-reply-author"):
        author = str(post[0].find(".bbp-reply-author")[0].text.replace("\n", ""))
    else:
        author = None

    if post[1].attrs["id"]:
        aux_str = str(post[1].attrs["id"])
        aux_str = aux_str.split("-")
        id_post = int(aux_str[-1])
    else:
        id_post = None

    if post[0].find(".bbp-reply-content blockquote"):
        blockquoteList = post[0].find(".bbp-reply-content blockquote")
        id_post_interaction = []

        # Processing id interactions of post
        for blockquot in blockquoteList:
            if blockquot.find(".d4p-bbt-quote-title a"):
                str_aux = str(blockquot.find(
                    ".d4p-bbt-quote-title a")[0].links)
                str_aux = str_aux.split("-")
                id_post_aux = str_aux[-1].split("'")
                id_post_interaction.append(id_post_aux[0])

        number_blockquotes = post[0].find(
            '.bbp-reply-content')[0].html.count("</blockquote>")
        bs_text = BeautifulSoup(
            post[0].find('.bbp-reply-content')[0].html, "lxml")

        for i in range(number_blockquotes):
            try:
                bs_text.blockquote.decompose()
            except AttributeError:
                pass

    else:
        id_post_interaction = None

    if post[0].find(".bbp-reply-content"):
        content_text = str(post[0].find(
            ".bbp-reply-content")[0].text.replace("\n", "")),
        content_html = str(post[0].find(
            ".bbp-reply-content")[0].html.replace("\n", "")),
    else:
        content_text = None
        content_html = None

    # Data of post
    post_dict = {
        "author": author,
        "resume_author": None,
        "joined_author": None,
        "messages_author": None,
        "text_post": content_text,
        "html_post": content_html,
        "number_post": None,
        "id_post": id_post,
        "id_post_interaction": id_post_interaction,
        "date_post": handle_date(date_post),
        "links": re.findall(LINKS_REGEX, str(content_html)),
        "thread": link,
    }

    return post_dict


def handle_date(date_post):
    date_post = date_post.replace(" at ", "-")
    date_post = date_post.replace(":", "-")
    date_post = date_post.replace("AM", "")
    date_post = date_post.replace("PM", "")
    week_day = date_post.split("-")
    real_date = datetime.today()

    # Converter date-time
    if week_day[0]:

        if int(week_day[3]) > 12:
            real_date.replace(year=int(week_day[0]), month=int(week_day[1]), day=int(week_day[2]),
                              hour=int(week_day[3]+12), minute=int(week_day[4]), second=0, microsecond=0)
        else:
            real_date.replace(year=int(week_day[0]), month=int(week_day[1]), day=int(week_day[2]),
                              hour=int(week_day[3]), minute=int(week_day[4]), second=0, microsecond=0)

    return real_date
