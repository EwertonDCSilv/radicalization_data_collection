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
        number_of_pages = int(list_aux[1].replace("page=",""))

    # Get a name of subforum
    subforum = r.html.find(".forumtitle")[0].text

    df_list = []

    for page_num in range(1, number_of_pages + 1, 1):
        print("Forum: {0} - Page {1}/{2}".format(subforum,
                                                 page_num, number_of_pages))
        r = session.get(INCELS_THREAD_BASE + link+"&page=" + str(page_num))

        print((INCELS_THREAD_BASE + link+"&page=" + str(page_num)))

        for thread in r.html.find("#thread_inlinemod_form .threadbit "):

            
            thread_dict = {
                "type": None,
                "title": thread.find('.title')[0].text,
                "link": list(thread.find('.title')[1].links)[0],
                "author_topic": thread.find('.author')[0].text,
                "replies": thread.find('.threadstats li')[0].text,
                "views":  thread.find('.threadstats li')[1].text,
                "subforum": subforum
            }
           
            print(thread_dict)

            df_list.append(thread_dict)

    subforum = subforum.replace("?","-")
    subforum = subforum.replace("!","-")
    subforum = subforum.replace(" ","_")

    df = pd.DataFrame(df_list)
    df.to_csv(dst.replace(".csv", "")+"_"+subforum+".csv")


def build_topics_index(src, dst, nump):

    session = get_html_session()

    # Gets the first page
    r = session.get(INCELS_URL)

    df_list = []

    for thread in r.html.find("#forums li ol .forumrow "):

        thread_dict = {
            "link": list(thread.find(".forumtitle a")[0].links)[0],
            "subforum": thread.find('.forumtitle a')[0].text,
        }

        df_list.append(thread_dict)

    df = pd.DataFrame(df_list)
    df.to_csv(dst)


def get_thread(link, session=None):

    session = get_html_session(session)
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

        exit()

    df = pd.DataFrame(df_list)
    df.to_csv("./data/forums/mgtow/posts/" +
              re.sub("/", "", link[9:]) + ".csv", index=False)


def get_num_pages_post(link, session=None):
    session = get_html_session(session)
    r_post = session.get(
        "https://www.mgtow.com/forums/topic/back-again-advice-needed/")
    try:
        number_of_pages_post = int(r_post.html.find(
            ".bbp-pagination-links a")[-2].text)
    except IndexError:
        number_of_pages_post = 1
    return number_of_pages_post


def get_posts_page(link, thread_page, session=None):
    session = get_html_session(session)
    #r_post = session.get(INCELS_THREAD_BASE + link +"page/" + str(thread_page))
    r_post = session.get(
        "https://www.mgtow.com/forums/topic/introduction-30/" + "page/" + str(thread_page))
    return r_post.html.find('.topic')


def get_post(post, link, session=None):
    # number_blockquotes = post.find(
    #    '.message-content')[0].html.count("</blockquote>")
    #bs_text = BeautifulSoup(post.find('.message-content')[0].html, "lxml")
    #
    # for i in range(number_blockquotes):
    #    try:
    #        bs_text.blockquote.decompose()
    #    except AttributeError:
    #        pass

    has_author = post.find(".bbp-reply-author a") is not None

    post_dict = {
        # "author": post.find('.username', first=True).text,
        # "resume_author": post.find('.message-userTitle', first=True).text,
        # "joined_author": post.find('.message-userExtras dd', first=True).text,
        # "messages_author": int(re.sub(",", "", post.find('.message-userExtras dd')[1].text)),
        # "text_post": re.sub("[\n|\xa0]+", " ", bs_text.text),
        # "html_post": post.find('.message-content')[0].html,
        # "number_post": post.find('.message-attribution-opposite a')[1].text,
        # "id_post": re.sub("js-post-", "", post.attrs["id"]),
        # "id_post_interaction": [re.sub(r'/goto/post\?id=', "", list(v.links)[0])
        #                        for v in post.find(".bbCodeBlock-title")],
        # "date_post": post.find('.u-concealed')[0].text,
        # "links": re.findall(LINKS_REGEX, str(bs_text.html)),
        # "thread": link


        "author": post.find(".bbp-reply-author a") if has_author else post.find(".bbp-reply-author"),
        "resume_author": None,
        "joined_author": None,
        "messages_author": None,
        "text_post": post.find(" .bbp-reply-content", first=True).text,
        "html_post": post.find(" .bbp-reply-content")[0].html,
        "number_post": None,  # Use a count,
        # "id_post": post.find(""),
        # "id_post_interaction": post.find(""),
        # "date_post": post.find(".bbp-reply-post-date").text,
        "links": re.findall(LINKS_REGEX, str(post.find(" .bbp-reply-content")[0].html)),
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
