from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import re

yt_v3_api = "https://www.googleapis.com/youtube/v3/"
url = "https://www.youtube.com/channel/"
wait = 3


def init_driver():
    driver = webdriver.Chrome()
    driver.wait = WebDriverWait(driver, 5)
    driver.set_window_size(1600, 1024)
    return driver


def lookup(driver, channel_id, name, api_key, dst_csv):
    session = HTMLSession()
    print(yt_v3_api + "channels?part=snippet,statistics&id={0}&key={1}".format(channel_id, api_key))
    v = session.get(yt_v3_api + "channels?part=snippet,statistics&id={0}&key={1}".format(channel_id, api_key))
    statistics = v.json()["items"][0]["statistics"]
    description = v.json()["items"][0]["snippet"]["description"]

    dict_out = {"name": name, "channel_id": channel_id, "statistics": statistics, "description": description,
                "edges":[]}

    print(url + channel_id)
    driver.get(url + channel_id)

    html = driver.page_source
    bs = BeautifulSoup(html, "html.parser")

    sections = bs.find_all("ytd-vertical-channel-section-renderer")
    for section in sections:
        title = section.find("h2").text
        channels = section.find_all("a", {"class": "ytd-mini-channel-renderer"})
        for channel in channels:
            name = re.sub("\n", "", channel.text)
            tmp = channels[0].attrs["href"].split("/")[1:]
            if tmp[0] == "channel":
                other_id = tmp[1]
            else:
                v = session.get(yt_v3_api + "channels?part=id&forUsername={0}&key={1}".format(tmp[1], api_key))
                other_id = v.json()["items"][0]["id"]
            dict_out["edges"].append({"name": name, "channel_id": other_id, "type": title})

    with open(dst_csv, "a") as dst:
        dst.write("{0}\n".format(dict_out))


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Wrong number of arguments")
    else:
        with open("./youtube_tools/api_key.json") as f:
            api_key = json.load(f)["key"]
        driver = init_driver()
        src_csv = sys.argv[1]
        dst_csv = sys.argv[2]
        df = pd.read_csv(src_csv)

        for idx, row in df.iterrows():
            time.sleep(wait)
            args = dict(row)
            name = args["Name"]
            channel_id = args["Id"]
            print("Started collecting {}...".format(name))
            lookup(driver, channel_id, name, api_key, dst_csv)
            print("Finished collecting {}...".format(name))


        driver.quit()
