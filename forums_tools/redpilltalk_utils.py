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

INCELS_URL = "https://redpilltalk.com"

INCELS_THREAD_BASE = "https://redpilltalk.com"


def build_index(link, dst, nump):
    session = get_html_session()

    # Gets the first page
    r = session.get(INCELS_URL+link+"page/" + str(1))

    # Find number of pages
    number_of_pages = int(r.html.find(".pagination span a")[-1].text)

    # Get a name of subforum
    subforum = r.html.find("#page-body h2")[0].text

    df_list = []

    for page_num in range(1, number_of_pages + 1, 1):
        print("Forum: {0} - Page {1}/{2}".format(subforum,
                                                 page_num, number_of_pages))

        r = session.get(INCELS_THREAD_BASE + link+"page/" + str(page_num))

        for thread in r.html.find("dl"):

            author = ''
            if len(thread.find('dt a')) >= 2:
                author = thread.find('dt a')[1].text
            
            if thread.find(".topictitle"):

                thread_dict = {
                    "type": None,
                    "title": thread.find(".topictitle")[0].text,
                    "link": str(list(thread.find(".topictitle")[0].links)[0]).replace("./", "/"),
                    "author_topic": author,
                    "replies": int(str(thread.find(".posts")[0].text).replace("Replies", "")),
                    "views": int(str(thread.find(".views")[0].text).replace("Views", "")),
                    "subforum": subforum
                }

                df_list.append(thread_dict)

    subforum = subforum.replace(" ","_")

    df = pd.DataFrame(df_list)
    df.to_csv(dst.replace(".csv", "")+"_"+subforum+".csv")


def build_topics_index(src, dst, nump):

    session = get_html_session()

    # Gets the first page
    r = session.get(INCELS_URL)

    df_list = []

    for thread in r.html.find(".topiclist dl"):

        if thread.find(".feed-icon-forum"):

            thread_dict = {
                "link": str(list(thread.find(".forumtitle")[0].links)[0]).replace("./", "/"),
                "subforum": thread.find(".forumtitle")[0].text,
            }

            df_list.append(thread_dict)

    df = pd.DataFrame(df_list)
    df.to_csv(dst)


def get_thread(link, session=None):

    session = get_html_session(session)
    link = INCELS_URL+link

    number_of_pages_post = get_num_pages_post(link, session)
    df_list = []

    for thread_page in range(1, number_of_pages_post + 1, 1):
        for idx, post in enumerate(get_posts_page(link, thread_page, session)):
            try:
                post_dict = get_post(post, link, session)
                df_list.append(post_dict)
            except Exception as ex:
                traceback.print_exc()
                print("problem with post", idx, ":", link)

    df = pd.DataFrame(df_list)

    link_array = link[9:].split("=")
    sufix = re.sub("/", "", link_array[-1])

    df.to_csv("./data/forums/redpilltalk/posts/redpilltalk_" +
              sufix + ".csv", index=False)


def get_num_pages_post(link, session=None):
    session = get_html_session(session)
    r_post = session.get(link)

    try:
        number_of_pages_post = int(
            r_post.html.find(".pagination span a")[-1].text)
    except IndexError:
        number_of_pages_post = 1
    return number_of_pages_post


def get_posts_page(link, thread_page, session=None):
    session = get_html_session(session)
    # r_post = session.get(INCELS_THREAD_BASE + link +"page/" + str(thread_page))
    r_post = session.get(
        "https://redpilltalk.com/viewtopic.php?f=11&t=172" +
        "&start=" + str((int(thread_page)-1)*30))
    return r_post.html.find('#page-body .post ')


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

    if post.find(".post-author"):
        autor = post.find(".post-author")[0].text.replace("\n", " ")
    else:
        autor = None

    if post.find('dl dd'):
        joined_author = int(post.find('dl dd')[0].text.replace("\n", " ")),
    else:
        joined_author = None

    if post.find('dl dd'):
        messages_author = str(post.find('dl dd')[1].text.replace("\n", " ")),
    else:
        messages_author = None

    if post.find('.content'):
        content_text = post.find('.content')[0].text.replace("\n", " "),
        content_html = post.find('.content')[0].html.replace("\n", " "),
    else:
        content_text = ''
        content_html = ''

    if post.find(".author time"):
        date_post = post.find(".author time")[0].text.replace("\n", " "),
    else:
        date_post = ''

    post_dict = {

        "author": autor,
        "resume_author": None,
        "joined_author": joined_author,
        "messages_author": messages_author,
        "text_post": str(content_text),
        "html_post": str(content_html),
        "number_post": None,  # Use a count,
        "id_post": None,
        "id_post_interaction": post.attrs["class"],
        "date_post": date_post,
        "links": re.findall(LINKS_REGEX, str(content_html)),
        "thread": link,
    }

    print(post_dict)
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
