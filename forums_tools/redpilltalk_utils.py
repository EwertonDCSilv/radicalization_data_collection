from utils import get_html_session
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import traceback
import re

week_day_list = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6,
                 "Yesterday": -1, "Today": -1}

month_list = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6, "July": 7, "August": 8, "September": 9, "October": 10,
              "November": 11, "December": 12, }

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

    # Get data index
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
    for thread in r.html.find(".topiclist dl"):

        if thread.find(".feed-icon-forum"):

            thread_dict = {
                "link": str(list(thread.find(".forumtitle")[0].links)[0]).replace("./", "/"),
                "subforum": thread.find(".forumtitle")[0].text,
            }

            df_list.append(thread_dict)

    # Export data topics index
    df = pd.DataFrame(df_list)
    df.to_csv(dst)


def get_thread(link, session=None):

    session = get_html_session(session)
    link = INCELS_URL+link

    number_of_pages_post = get_num_pages_post(link, session)
    df_list = []

    count_post = 1

    # Processing post pages
    for thread_page in range(1, number_of_pages_post + 1, 1):
        for idx, post in enumerate(get_posts_page(link, thread_page, session)):
            try:
                post_dict = get_post(post, link, session)

                if post_dict:
                    post_dict["number_post"] = count_post

                    df_list.append(post_dict)
                    count_post = count_post + 1

            except Exception:
                traceback.print_exc()
                print("problem with post", idx, ":", link)

    df = pd.DataFrame(df_list)

    # Export data posts
    link_array = link[9:].split("=")
    sufix = re.sub("/", "", link_array[-1])
    df.to_csv("./data/forums/redpilltalk/posts/redpilltalk_" +
              sufix + ".csv", index=False)


def get_num_pages_post(link, session=None):
    session = get_html_session(session)
    r_post = session.get(link)

    # Get number pages for post
    try:
        number_of_pages_post = int(
            r_post.html.find(".pagination span a")[-1].text)
    except IndexError:
        number_of_pages_post = 1
    return number_of_pages_post


def get_posts_page(link, thread_page, session=None):
    session = get_html_session(session)
    r_post = session.get(link +
                         "&start=" + str((int(thread_page)-1)*30))

    # Get elements post
    return r_post.html.find('#page-body article')


def get_post(post, link, session=None):

    if post.find(".post-author"):
        autor = str(post.find(".post-author")
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

    if post.find('.content'):

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
                post.find('.content')[0].html, "html.parser")

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
        date_post = str(post.find(".author time")[
                        0].text.replace("\n", " ")),
    else:
        date_post = ''

    # Data of post
    post_dict = {

        "author": autor,
        "resume_author": None,
        "joined_author": joined_author,
        "messages_author": messages_author,
        "text_post": str(content_text[0]),
        "html_post": str(content_html),
        "number_post": None,
        "id_post": int(post.attrs["id"].replace("p", "")),
        "id_post_interaction": id_post_interaction,
        "date_post": handle_date(date_post[0]),
        "links": re.findall(LINKS_REGEX, str(content_html)),
        "thread": link,
    }

    return post_dict


def handle_date(date_post):

    week_day = date_post.split()
    current_date = datetime.today().replace(
        hour=0, minute=0, second=0, microsecond=0)
    real_date = datetime.today()

    if "ago" in week_day:

        # handles date: case (1) month ago
        if "month" in week_day:
            number_day = int(week_day[0])
            real_date = current_date - relativedelta(months=number_day)
        
        # handles date: case (2) weeks ago
        elif "week" in week_day:
            number_day = int(week_day[0])*7
            real_date = current_date - relativedelta(days=number_day)

    # handles date: case (3) older post
    else:
        real_date = real_date.replace(day=1, month=int(month_list[week_day[0]]),
                                      year=int(week_day[1]), hour=0, minute=0, second=0, microsecond=0)

    return real_date
