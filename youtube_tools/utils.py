from requests_html import HTMLSession
from ytcc.download import Download
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import subprocess
import youtube_dl
import json
import time
import re
import os

YT_V3_API_URL = "https://www.googleapis.com/youtube/v3/"
YT_CHANNEL_URL = "https://www.youtube.com/channel/"
THREE_SECONDS_WAIT = 3


def existing_video_check(channel_id, channel_dst, row_interest, video_ids):
    df_list = []
    if os.path.isfile("{0}/{1}.csv".format(channel_dst, channel_id)):
        print(channel_id, "already exists!")
        tmp_df = pd.read_csv("{0}/{1}.csv".format(channel_dst, channel_id))
        existing_video_ids = list(tmp_df["video_id"].values)
        existing_video_captions = list(tmp_df[row_interest].values)
        for existing_video_id, existing_video_caption in zip(existing_video_ids, existing_video_captions):
            df_list.append({
                "video_id": existing_video_id,
                row_interest: existing_video_caption,
            })

        diff_videos = list(set(video_ids) - set(existing_video_ids))
    else:
        existing_video_ids = []
        diff_videos = video_ids

    print("Starting {}, had {} videos already, {} new videos...".format(channel_id,
                                                                        len(existing_video_ids),
                                                                        len(diff_videos)))

    return df_list, diff_videos


""" loader_captions.py """


def get_download(download):
    if download is None:
        print("new Download session")
        return Download()
    else:
        return download


def video_captions(channel_id, video_ids, channel_dst, download):
    df_list, diff_videos = existing_video_check(channel_id, channel_dst, "captions", video_ids)
    for video_id in diff_videos:
        df_list.append({
            "video_id": video_id,
            "captions": video_caption(video_id, download),
        })

    df = pd.DataFrame(df_list)
    df.to_csv("{0}/{1}.csv".format(channel_dst, channel_id), index=False)


def video_caption(video_id, download=None):
    download = get_download(download)
    try:
        captions = download.get_captions(video_id)
        print("success for {0}".format(video_id))
    except Exception as ex:
        print(ex)
        captions = None
    return captions


""" loader_comments.py """


def video_comments(channel_id, video_ids, channel_dst):
    df_list, diff_videos = existing_video_check(channel_id, channel_dst, "comments", video_ids)

    for video_id in diff_videos:
        df_list.append({
            "video_id": video_id,
            "comments": video_comment(video_id),
        })

    df = pd.DataFrame(df_list)
    df.to_csv("{0}/{1}.csv".format(channel_dst, channel_id), index=False)


def video_comment(video_id):
    try:
        p = subprocess.check_output('node ./youtube_tools/get_comments.js {0}'.format(video_id), shell=True)
        comment = json.loads(p)
        print("success for {0}".format(video_id))
    except Exception as ex:
        print(ex)
        comment = None

    return comment


""" loader_youtube.py """


def videos_in_channel(channel_id, dateafter, only_recent=False):
    all_videos = []

    playlist_id = 'UU' + channel_id[2:]

    t1 = datetime.now()

    args_dl = {"ignoreerrors": True, "dateafter": dateafter.strftime("today")}

    if only_recent:
        args_dl = {"playlistend": 10}

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
                   "crawl_date": datetime.now().strftime("%Y%m%d")} for vid in
                  playd["entries"] if type(vid) is dict and datetime.strptime(vid["upload_date"], "%Y%m%d") > dateafter]

        all_videos += videos

    t2 = datetime.now()

    print("{}: {} videos in {} seconds".format(channel_id, len(all_videos), (t2 - t1).total_seconds()))

    return all_videos


def channel(channel_id, channel_dst, name, data_step, category):
    df_list = []
    only_recent = False
    latest_date = datetime.strptime("19700101", '%Y%m%d')

    print(name, ":", channel_id)

    if os.path.isfile("{0}/{1}.csv".format(channel_dst, channel_id)):
        print(name, "already exists!")
        only_recent = True
        df = pd.read_csv("{0}/{1}.csv".format(channel_dst, channel_id))
        for idx, row in list(df.iterrows()):

            args_pd = dict(row)
            df_list.append(args_pd)
            current_date = datetime.strptime(str(args_pd["upload_date"]), '%Y%m%d')

            if current_date > latest_date:
                latest_date = current_date

    print("had {} videos already...".format(len(df_list)))

    if len(df_list) > 0:
        print("latest date {}...".format(latest_date))
    for video in videos_in_channel(channel_id, latest_date, only_recent):
        video["name"] = name
        video["step"] = data_step
        video["category"] = category
        video["id"] = channel_id
        df_list.append(video)

    df = pd.DataFrame(df_list)
    df.to_csv("{0}/{1}.csv".format(channel_dst, channel_id), index=False)


""" loader_recommended.py """


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
