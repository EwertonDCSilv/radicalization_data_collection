from requests_html import HTMLSession
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import subprocess
import youtube_dl
import logging
import json
import time
import re
import os


YT_V3_API_URL = "https://www.googleapis.com/youtube/v3/"
YT_CHANNEL_URL = "https://www.youtube.com/channel/"
THREE_SECONDS_WAIT = 3





def video_captions(video_id, download, f):
    try:
        captions = download.get_captions(video_id)
    except Exception:
        captions = None
        f.write("Could not load captions for {0}".format(video_id))
    return captions


def video_comments(video_id, f):
    try:
        p = subprocess.check_output('node ./youtube_tools/get_comments.js {0}'.format(video_id), shell=True)
        comment = json.loads(p)
    except Exception:
        comment = None
        f.write("Could not load comments for {0}".format(video_id))

    return comment


def videos_in_channel(channel_id, dateafter):
    all_videos = []

    playlist_id = 'UU' + channel_id[2:]

    t1 = datetime.now()

    args_dl = {"ignoreerrors": True, "dateafter": dateafter.strftime("%Y%m%d"), "quiet": True, "playlistend":1}

    with youtube_dl.YoutubeDL(args_dl) as ydl:
        playd = ydl.extract_info(playlist_id, download=False)
        videos = [{"Id": channel_id,
                   "description": vid["description"],
                   "view_count": vid["view_count"],
                   "like_count": vid["like_count"],
                   "dislike_count": vid["dislike_count"],
                   "title": vid["title"],
                   "video_id": vid["id"],
                   "upload_date": vid["upload_date"],
                   "crawl_date": str(datetime.now())} for vid in
                  playd["entries"] if type(vid) is dict]

        all_videos += videos

    t2 = datetime.now()

    print("{}: {} videos in {} seconds".format(channel_id, len(all_videos), (t2 - t1).total_seconds()))

    return all_videos


def channel(channel_id, channel_dst, name, data_step, category):
    df_list = []
    latest_date = datetime.strptime("19700101", '%Y%m%d')

    print(name, ":", channel_id)

    if os.path.isfile("{0}/{1}.csv".format(channel_dst, channel_id)):
        print(name, "already exists!")
        df = pd.read_csv("{0}/{1}.csv")
        for idx, row in df.iterrows():
            args_pd = dict(row)
            df_list.append(args_pd)
            if args_pd["upload_date"] > latest_date:
                latest_date = args_pd["upload_date"]

    print("had {} videos already...".format(len(df_list)))

    if len(df_list) > 0:
        print("latest date {}...".format(latest_date))
    for video in videos_in_channel(channel_id, latest_date):
        video["name"] = name
        video["step"] = data_step
        video["category"] = category
        video["id"] = channel_id
        df_list.append(video)

    df = pd.DataFrame(df_list)
    df.to_csv("{0}/{1}.csv".format(channel_dst, channel_id), index=False)


# download = Download()
# video["captions"] = video_captions(video["video_id"], download, f)
# video["comments"] = video_comments(video["video_id"], f)

def get_html_session(session):
    if session is None:
        print("new html session")
        return HTMLSession()
    else:
        return session


def get_yt_api_key(path):
    with open(path) as f:
        return json.load(f)["key"]


def get_channel_stats_n_desc(channel_id, api_key, session=None):
    try:
        session = get_html_session(session)
        v = session.get(YT_V3_API_URL + "channels?part=snippet,statistics&id={0}&key={1}".format(channel_id, api_key))
        statistics = v.json()["items"][0]["statistics"]
        description = v.json()["items"][0]["snippet"]["description"]
        return {"statistics": statistics, "description": description}
    except Exception:
        print("Could not load statistics for {0}".format(channel_id))
        return {"statistics": None, "description": None}


def channel_text_to_id(href, api_key, session=None):
    session = get_html_session(session)
    tmp = href.split("/")[1:]
    if tmp[0] == "channel":
        other_id = tmp[1]
    else:
        v = session.get(YT_V3_API_URL + "channels?part=id&forUsername={0}&key={1}".format(tmp[1], api_key))
        other_id = v.json()["items"][0]["id"]
    return {"channel_id": other_id}


def get_recommended_n_stats(channel_id, name, api_key, session=None):
    session = get_html_session(session)
    time.sleep(THREE_SECONDS_WAIT)
    stats_n_desc_out = get_channel_stats_n_desc(channel_id, api_key, session)
    dict_out = {"name": name, "channel_id": channel_id, "edges": [], **stats_n_desc_out}
    print(YT_CHANNEL_URL + channel_id)
    v = session.get(YT_CHANNEL_URL + channel_id)
    v.html.render()
    html = v.html.raw_html
    bs = BeautifulSoup(html, "html.parser")
    sections = bs.find_all("ytd-vertical-channel-section-renderer")
    for section in sections:
        title = section.find("h2").text
        channels = section.find_all("a", {"class": "ytd-mini-channel-renderer"})
        for channel in channels:
            name = re.sub("\n", "", channel.text)
            channel_out = channel_text_to_id(channel.attrs["href"], api_key, session)
            dict_out["edges"].append({"name": name, "type": title, **channel_out})
    return dict_out


