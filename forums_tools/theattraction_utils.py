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
SPECIAL_CHARS = r'(\t|\r\n|\n)?'

INCELS_URL = "https://www.theattractionforums.com/"
URL_THREAD_BASE = "https://www.theattractionforums.com/"


def build_index(link, dst, nump):
    session = get_html_session()

    # Gets the first page
    r = session.get(URL_THREAD_BASE + link+"&page")

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

        r = session.get(URL_THREAD_BASE + link+"&page=" + str(page_num))

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
            except Exception:
                traceback.print_exc()
                print("problem with post", idx, ":", link)

    # Export data posts
    name_file = link[9:].split("t=")
    name_file = name_file[-1].split("&")

    df = pd.DataFrame(df_list)
    df.to_csv("./data/forums/theattraction/posts/" +
              name_file[0] + ".csv", index=False)

    exit()


def get_num_pages_post(link, session=None):
    session = get_html_session(session)
    r_post = session.get(URL_THREAD_BASE+link)

    # Get number pages for post
    try:
        number_of_pages_post = int(r_post.html.find(
            ".pagination_bottom span")[-3].text)

    except IndexError:
        number_of_pages_post = 1
    return number_of_pages_post


def get_posts_page(link, thread_page, session=None):
    session = get_html_session(session)
    r_post = session.get(URL_THREAD_BASE + link +
                         "&page=" + str(thread_page))

    # Get elements post
    return r_post.html.find('.postcontainer')


def get_post(post, link, session=None):

    if post.find(".username"):
        autor = str(post.find(".username")
                    [0].text.replace("\n", " "))
    else:
        autor = None

    if post.find('.userstats dd'):
        joined_author = str(post.find('.userstats dd')[0].text)
        joined_author = re.sub(SPECIAL_CHARS, '', joined_author)

    else:
        joined_author = None

    messages_author = None

    if post.find('.userstats dd'):
        if len(post.find('.userstats dd')) == 4:
            messages_author = str(post.find('.userstats dd')[3].text)
            messages_author = re.sub(SPECIAL_CHARS, '', messages_author)

        elif len(post.find('.userstats dd')) == 3:
            messages_author = str(post.find('.userstats dd')[2].text)
            messages_author = re.sub(SPECIAL_CHARS, '', messages_author)

    if post.find('.postcontent'):

        # Verify interactions inter posts
        if post.find(".message"):
            blockquoteList = post.find(".message blockquote")
            id_post_interaction = []

            # Processing id interactions of post
            for blockquot in blockquoteList:
                if blockquot.find(".bbcode_postedby a"):
                    str_aux = str(blockquot.find(
                        ".bbcode_postedby a")[0].links)
                    str_aux = str_aux.split("#post")
                    id_post_aux = str_aux[-1]
                    id_post_interaction.append(int(id_post_aux[0]))

            number_blockquotes = post.find(
                '.message')[0].html.count("</blockquote>")

            bs_text = BeautifulSoup(
                post.find('.postcontent')[0].html, "html.parser")

            for i in range(number_blockquotes):
                try:
                    bs_text.blockquote.decompose()
                except AttributeError:
                    pass

            content_html = re.sub(SPECIAL_CHARS, '', str(bs_text))
            content_text = re.sub(SPECIAL_CHARS, '', str(bs_text.get_text()))
        else:
            content_text = re.sub(SPECIAL_CHARS, '', str(
                post.find('.postcontent')[0].text))

            content_html = re.sub(SPECIAL_CHARS, '', str(
                post.find('.postcontent')[0].html))

            id_post_interaction = []
    else:
        return False

    if post.find(".date"):
        date_post = str(post.find(".date")[0])
        date_post = re.sub(SPECIAL_CHARS, '', date_post)
    else:
        date_post = ''

    if post.find('.postcounter'):
        number_post = post.find('.postcounter')[0].text.replace("#", "")
    else:
        number_post = ''

    if post.find('.postcounter'):
        id_post = post.find('.postcontainer')[
            0].attrs["id"].replace("post_", "")
    else:
        id_post = ''

    # Data of post
    post_dict = {

        "author": autor,
        "resume_author": None,
        "joined_author": joined_author,
        "messages_author": messages_author,
        "text_post": str(content_text),
        "html_post": str(content_html),
        "number_post": int(number_post),
        "id_post": id_post,
        "id_post_interaction": id_post_interaction,
        "date_post": handle_date(date_post[0]),
        "links": re.findall(LINKS_REGEX, str(content_html)),
        "thread": link,
    }

    print(post_dict)
    # exit()
    return post_dict


def handle_date(date_post):

    return date_post
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
