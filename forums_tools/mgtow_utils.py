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

    subforum = subforum.replace(" ", "_")

    df = pd.DataFrame(df_list)
    df.to_csv(dst.replace(".csv", "")+"_"+subforum+".csv")


def build_topics_index(src, dst, nump):

    session = get_html_session()

    # Gets the first page
    r = session.get(INCELS_URL)

    df_list = []

    for thread in r.html.find("#grid .element-item "):

        thread_dict = {
            "link": list(thread.find("a")[0].links)[0],
            "subforum": thread.find('h4')[0].text,
        }

        df_list.append(thread_dict)

    df = pd.DataFrame(df_list)
    df.to_csv(dst)


def get_thread(link, session=None):

    session = get_html_session(session)
    number_of_pages_post = get_num_pages_post(link, session)
    df_list = []
    
    for thread_page in range(1, number_of_pages_post + 1, 1):

        post_elemenets = get_posts_page(link, thread_page, session)
        N = len(post_elemenets[0])

        for i in range(N):
            try:
                element = []
                element.append(post_elemenets[0][i])
                element.append(post_elemenets[1][i])

                post_dict = get_post(element, link, session)
                df_list.append(post_dict)
            except Exception as ex:
                traceback.print_exc()
                print("problem with post", i, ":", link)

    df = pd.DataFrame(df_list)
    df.to_csv("./data/forums/mgtow/posts/" +
              re.sub("/", "", link[9:].replace(" ", "_")) + ".csv", index=False)


def get_num_pages_post(link, session=None):
    session = get_html_session(session)
    r_post = session.get(INCELS_THREAD_BASE + link)
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
    print(INCELS_THREAD_BASE + link + "page/" + str(thread_page))

    post_elemenet = []
    post_elemenet.append(r_post.html.find('.hentry'))
    post_elemenet.append(r_post.html.find('.bbp-reply-header'))

    return post_elemenet


def get_post(post, link, session=None):
    # number_blockquotes = post.find(
    #    '.message-content')[0].html.count("</blockquote>")
    # bs_text = BeautifulSoup(post.find('.message-content')[0].html, "lxml")
    #
    # for i in range(number_blockquotes):
    #    try:
    #        bs_text.blockquote.decompose()
    #    except AttributeError:
    #        pass

    if post[1].find(".bbp-reply-post-date"):
        date_post = post[1].find(
            ".bbp-reply-post-date")[0].text.replace("\n", "")
    else:
        date_post = None

    if post[0].find(".bbp-reply-author a"):
        author = post[0].find(".bbp-reply-author a")[0].text.replace("\n", "")
    else:
        author = None

    if post[0].find(".bbp-reply-content"):
        content_text = post[0].find(
            ".bbp-reply-content")[0].text.replace("\n", ""),
        content_html = post[0].find(
            ".bbp-reply-content")[0].html.replace("\n", ""),
    else:
        content_text = None
        content_html = None

    post_dict = {
        "author": author,
        "resume_author": None,
        "joined_author": None,
        "messages_author": None,
        "text_post": content_text,
        "html_post": content_html,
        "number_post": None,
        # "id_post": post.find(""),
        # "id_post_interaction": post.find(""),
        "date_post": date_post,
        "links": re.findall(LINKS_REGEX, str(content_html)),
        "thread": link,
    }

    return post_dict


def handle_date(date_post):
    date_post = date_post.replace(",", "")
    week_day = date_post.split()
    current_date = datetime.today().replace(
        hour=0, minute=0, second=0, microsecond=0)
    real_date = datetime.today()

    if week_day[0] in week_day_list:

        # handles date: case (1) day of this week / last week
        if week_day_list[week_day[0]] != -1:

            if week_day_list[week_day[0]] > current_date.today().weekday():
                number_day = (
                    7 - week_day_list[week_day[0]]) + current_date.today().weekday()
            elif week_day_list[week_day[0]] < current_date.today().weekday():
                number_day = current_date.today().weekday() - \
                    week_day_list[week_day[0]]

            real_date = current_date - relativedelta(days=number_day)

        # handles date: case (2) yesterday  /today
        else:
            if "Yesterday" in week_day[0]:
                real_date = current_date - relativedelta(days=1)

            elif "Today" in week_day[0]:
                real_date = current_date - relativedelta(days=0)

        if 'am' in date_post or "12:" in date_post:
            week_day_hour = week_day[2].split(':')
            real_date = real_date.replace(
                hour=int(week_day_hour[0]), minute=int(week_day_hour[1]))
        else:
            week_day_hour = week_day[2].split(':')
            real_date = real_date.replace(
                hour=int(week_day_hour[0]) + 12, minute=int(week_day_hour[1]))

    # handles date: case (3) older post
    else:
        real_date = real_date.replace(day=int(week_day[1]), month=int(month_list[week_day[0]]),
                                      year=int(week_day[2]), hour=0, minute=0, second=0, microsecond=0)

    return real_date
