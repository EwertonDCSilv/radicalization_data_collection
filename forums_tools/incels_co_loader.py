from requests_html import HTMLSession
from multiprocessing import Pool
from bs4 import BeautifulSoup
import pandas as pd
import re

LINKS_REGEX = r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?'
INCELS_URL = "https://incels.co/forums/inceldom-discussion.2/page-"
INCELS_THREAD_BASE = "https://incels.co"


def get_html_session(session=None):
    if session is None:
        print("new html session")
        return HTMLSession()
    else:
        return session


def handle_date():
    pass


def build_index(dst, nump):
    session = get_html_session()

    # Gets the first page
    r = session.get(INCELS_URL + str(1))

    # Find number of pages
    number_of_pages = int([v.text for v in r.html.find(".pageNav-page")][-1])

    df_list = []

    for page_num in range(1, number_of_pages + 1, 1):
        print("Page {0}/{1}".format(page_num, number_of_pages))
        r = session.get(INCELS_URL + str(page_num))

        for thread in r.html.find(".structItem--thread"):
            has_type = thread.find('.labelLink', first=True) is not None

            thread_dict = {
                "type": thread.find('.labelLink', first=True).text if has_type else None,
                "title": thread.find('.structItem-title a')[1].text if has_type
                else thread.find('.structItem-title a')[0].text,
                "link": list(thread.find('.structItem-title a')[1].links)[0] if has_type
                else list(thread.find('.structItem-title a')[0].links)[0],
                "author_topic": thread.find('.username')[0].text,
                "replies": int(re.sub("K", "000", thread.find('.structItem-cell--meta dd')[0].text)),
                "views": int(re.sub("K", "000", thread.find('.structItem-cell--meta dd')[1].text)),
                "subforum": "Inceldom Discussion"
            }

            df_list.append(thread_dict)

    df = pd.DataFrame(df_list)

    df.to_csv(dst)


def get_thread(link, session=None):
    session = get_html_session(session)
    number_of_pages_post = get_num_pages_post(link, session)
    df_list = []

    for thread_page in range(1, number_of_pages_post + 1, 1):
        for post in get_posts_page(link, thread_page, session):
            post_dict = get_post(post, session)
            df_list.append(post_dict)

    df = pd.DataFrame(df_list)
    df.to_csv("./data/forums/incels/posts/" + re.sub("/", "", link[9:]) + ".csv")


def get_num_pages_post(link, session=None):
    session = get_html_session(session)
    r_post = session.get(INCELS_THREAD_BASE + link)
    try:
        number_of_pages_post = int([v.text for v in r_post.html.find(".pageNav-page")][-1])
    except IndexError:
        number_of_pages_post = 1
    return number_of_pages_post


def get_posts_page(link, thread_page, session=None):
    session = get_html_session(session)
    r_post = session.get(INCELS_THREAD_BASE + link + "page-" + str(thread_page))
    return r_post.html.find('.message--post')


def get_post(post, session=None):
    number_blockquotes = post.find('.message-content')[0].html.count("</blockquote>")
    bs_text = BeautifulSoup(post.find('.message-content')[0].html, "lxml")
    for i in range(number_blockquotes):
        bs_text.blockquote.decompose()

    post_dict = {
        "author": post.find('.username', first=True).text,
        "link_author": list(post.find('.username', first=True).links)[0],
        "resume_author": post.find('.message-userTitle', first=True).text,
        "joined_author": post.find('.message-userExtras dd', first=True).text,
        "messages_author": int(re.sub(",", "", post.find('.message-userExtras dd')[1].text)),
        "text_post": re.sub("[\n|\xa0]+", " ", bs_text.text),
        "html_post": post.find('.message-content')[0].html,
        "number_post": post.find('.message-attribution-opposite a')[1].text,
        "id_post": re.sub("js-post-", "", post.attrs["id"]),
        "id_post_interaction": [re.sub(r'/goto/post\?id=', "", list(v.links)[0])
                                for v in post.find(".bbCodeBlock-title")],
        "date_post": post.find('.u-concealed')[0].text,
        "links": re.findall(LINKS_REGEX, str(bs_text.html))
    }
    return post_dict


if __name__ == "__main__":
    import argparse


    def get_thread_global(link):
        if session_global is not None:
            session = session_global
        get_thread(link, session)


    def initialize_worker():
        global session_global
        session_global = HTMLSession()


    parser = argparse.ArgumentParser(description="""""")

    parser.add_argument("--index", dest="index", type=str, default="./data/forums/incels/index.csv",
                        help="Location of index file`")

    parser.add_argument("--build_index", dest="build_index", action="store_true",
                        help="If true, builds index, otherwise gets posts.")

    parser.add_argument("--nump", dest="nump", type=int, default=4,
                        help="Number of simultaneous processes.")

    parser.add_argument("--debug", dest="debug", action="store_true",
                        help="Runs w/o multiprocessing for debugging.")

    args = parser.parse_args()

    if args.build_index:
        build_index(args.index)

    else:
        to_run = list(pd.read_csv(args.index)["link"].values)
        if args.debug:
            for i in to_run:
                get_thread(to_run)
        else:
            p = Pool(args.nump, initializer=initialize_worker)
            p.map(get_thread_global, to_run)
