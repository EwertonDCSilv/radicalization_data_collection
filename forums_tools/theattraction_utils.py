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

INCELS_URL = "https://www.theattractionforums.com/"
INCELS_THREAD_BASE = "https://www.theattractionforums.com/"


def build_index(link, dst, nump):
    session = get_html_session()

    # Gets the first page
    r = session.get(INCELS_THREAD_BASE + link+"&page")

    # Find number of pages
    number_of_pages = 1

    if r.html.find(".first_last a"):
        url_end_page = str(r.html.find(".first_last a")[0].links)
        list_aux = url_end_page.split("&")
        number_of_pages = int(list_aux[1].replace("page=", ""))

    # Get name of subforum
    subforum = r.html.find(".forumtitle")[0].text

    df_list = []

    # Get data index
    for page_num in range(1, number_of_pages + 1, 1):
        print("Forum: {0} - Page {1}/{2}".format(subforum,
                                                 page_num, number_of_pages))

        r = session.get(INCELS_THREAD_BASE + link+"&page=" + str(page_num))

        thread = list(r.html.find("#thread_inlinemod_form"))[0]
        len_list = len(r.html.find("#thread_inlinemod_form .inner"))

        j = 0  # Count element secundary

        for i in range(len_list):

            if thread.find('.threadstats li')[j]:
                strAux = str(thread.find('.threadstats li')
                             [j].text.replace("Replies:", ""))
                strAux = strAux.replace(",", "")
                replies = strAux.replace(" ", "")
            else:
                replies = 0

            if thread.find('.threadstats li')[j+1]:
                strAux = str(thread.find('.threadstats li')
                             [j+1].text).replace("Views:", "")
                strAux = strAux.replace(",", "")
                views = strAux.replace(" ", "")
            else:
                views = 0

            thread_dict = {
                "type": None,
                "title": str(thread.find('.inner .title')[i].text).replace("\n", ""),
                "link": str(list(thread.find('.inner .title')[i].links)[0]).replace("\n", ""),
                "author_topic": str(thread.find('.inner .author .username ')[i].text).replace("\n", ""),
                "replies": replies,
                "views": views,
                "subforum": subforum
            }

            df_list.append(thread_dict)

            j = j + 3  # Each element content 3 subelements

    # Export data index
    subforum = subforum.replace("?", "-")
    subforum = subforum.replace("!", "-")
    subforum = subforum.replace(" ", "_")

    df = pd.DataFrame(df_list)
    df.to_csv(dst.replace(".csv", "")+"_"+subforum+".csv")


def build_topics_index(src, dst, nump):

    session = get_html_session()

    # Gets the first page
    r = session.get(INCELS_URL)

    df_list = []

    # Processing data topics index
    for thread in r.html.find("#forums li ol .forumrow "):

        thread_dict = {
            "link": list(thread.find(".forumtitle a")[0].links)[0],
            "subforum": thread.find('.forumtitle a')[0].text,
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
        for idx, post in enumerate(get_posts_page(link, thread_page, session)):
            try:
                post_dict = get_post(post, link, session)
                df_list.append(post_dict)
            except Exception as ex:
                traceback.print_exc()
                print("problem with post", idx, ":", link)

        exit()

    # Export data posts
    df = pd.DataFrame(df_list)
    df.to_csv("./data/forums/mgtow/posts/" +
              re.sub("/", "", link[9:]) + ".csv", index=False)


def get_num_pages_post(link, session=None):
    session = get_html_session(session)
    r_post = session.get(
        "https://www.mgtow.com/forums/topic/back-again-advice-needed/")

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

    # Get elements post
    return r_post.html.find('.postlist')


def get_post(post, link, session=None):
    '''
        "resume_author": $('.userstats dd'),
        "messages_author": none,
        "text_post": $('.postlist .postbit .postcontent'),
        "html_post": $('.postlist .postbit .postcontent')
        "number_post": $('.postlist .postbit .nodecontrols'),
                *"id_post": $(""),
                *"id_post_interaction": $(""),
        "date_post": $(".postlist .postdate"),
        "links": $('.postlist .postbit .postcontent').eq(0),
        "thread": $('#pagecontent tr td').eq(9),

    '''

    if post.find(".postbit .username"):
        autor = str(post.find(".postbit .username")
                    [0].text.replace("\n", " "))
    else:
        autor = None

    if post.find('dl dd'):
        joined_author = str(
            post.find('dl dd')[1].text.replace("\n", " ")),
    else:
        joined_author = None

    if post.find('dl dd'):
        messages_author = str(
            post.find('dl dd')[0].text.replace("\n", " ")),
    else:
        messages_author = None

    if post.find('.postbit .postcontent'):

        # Verify interactions inter posts
        if post.find("blockquote"):
            blockquoteList = post.find("blockquote")
            id_post_interaction = []

            # Processing id interactions of post
            # for blockquot in blockquoteList:
            #     if blockquot.find(".d4p-bbt-quote-title a"):
            #         str_aux = str(blockquot.find(
            #             ".d4p-bbt-quote-title a")[0].links)
            #
            #         str_aux = str_aux.split("-")
            #         id_post_aux = str_aux[-1].split("'")
            #         id_post_interaction.append(int(id_post_aux[0]))

            # number_blockquotes = post.find(
            #     '.bbp-reply-content')[0].html.count("</blockquote>")

            bs_text = BeautifulSoup(
                post.find('.postbit .postcontent')[0].html, "html.parser")

            # for i in range(number_blockquotes):
            #     try:
            #         bs_text.blockquote.decompose()
            #     except AttributeError:
            #         pass

            content_html = str(bs_text)
            content_text = str(bs_text.get_text())
        else:
            content_text = str(post.find('.content')
                               [0].text.replace("\n", " ")),
            content_html = str(post.find('.content')
                               [0].html.replace("\n", " ")),
            id_post_interaction = []
    else:
        return False

    if post.find(".author time"):
        date_post = str(post.find(".author time")
                        [0].text.replace("\n", " ")),
    else:
        date_post = ''

    # Data of post
    post_dict = {

        "author": autor,
        "resume_author": None,
        "joined_author": joined_author,
        "messages_author": messages_author,
        "text_post": str(content_text),
        "html_post": str(content_html),
        "number_post": None,
        "id_post": 0,  # int(post.attrs["id"].replace("post_", "")),
        "id_post_interaction": id_post_interaction,
        "date_post": date_post,
        "links": re.findall(LINKS_REGEX, str(content_html)),
        "thread": link,
    }

    print(post_dict)
    exit()

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
