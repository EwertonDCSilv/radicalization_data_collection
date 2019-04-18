from requests_html import HTMLSession
from datetime import datetime
from multiprocessing import Pool
from bs4 import BeautifulSoup
import pandas as pd
import re
import os

LINKS_REGEX = r'(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?'
BASE_AVMF_URL = "https://d2ec906f9aea-003845.vbulletin.net"


def get_html_session(session=None):
    if session is None:
        print("new html session")
        return HTMLSession()
    else:
        return session


def handle_date():
    pass


def build_index(src, dst, nump):

    sub_urls = list(pd.read_csv(src)["subs"].values)
    session = get_html_session()

    for sub_url in sub_urls:
        print(sub_url)

        # Gets the first page
        r = session.get(BASE_AVMF_URL + sub_url)

        # Find number of pages
        number_of_pages = int([v.text for v in r.html.find(".toolbar-pagenav-wrapper .pagetotal")][-1])

        df_list = []
        for page_num in range(1, number_of_pages + 1, 1):
            print("Page {0}/{1}".format(page_num, number_of_pages))
            r = session.get(BASE_AVMF_URL + sub_url + "/page" + str(page_num))

            for thread in r.html.find(".js-topic-item"):
                topic_info = thread.find(".topic-info")[0].text.split(",")
                author_topic = "".join(topic_info[:-2])[11:]

                prefix_l = thread.find(".js-topic-item")[0].find(".js-prefix")
                prefix = None

                if len(prefix_l) > 0:
                    if prefix_l[0].text == "Sticky:":
                        prefix = "Sticky"
                    elif prefix_l[0].text == "Redirect:":
                        continue

                thread_dict = {
                    "prefix": prefix,
                    "title": thread.find(".js-topic-title")[0].text,
                    "link": re.findall(LINKS_REGEX,
                                       list(thread.find(".js-topic-title")[0].links)[0])[0][2],
                    "author_topic": author_topic,
                    "replies": int(re.sub("[ response(s)?|,]", "", thread.find(".posts-count")[0].text)),
                    "views": int(re.sub("[ view(s)?|,]", "", thread.find(".views-count")[0].text)),
                    "subforum": sub_url
                }

                df_list.append(thread_dict)

        df = pd.DataFrame(df_list)

        df.to_csv(dst, index=False)


build_index("./data/forums/avfm_subs.csv", "./data/forums/avfm/index.csv", None)