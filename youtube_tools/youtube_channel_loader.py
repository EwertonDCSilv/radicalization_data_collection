# Slightly adapted from: https://stackoverflow.com/questions/15512239/python-get-all-youtube-video-urls-of-a-channel

from ytcc.download import Download
import multiprocessing as mp
import pandas as pd
import youtube_dl
import subprocess
import json
import os

def videos_in_channel(channel_id):
    all_videos = []

    playlist_id = 'UU' + channel_id[2:]

    with youtube_dl.YoutubeDL({"ignoreerrors": True, "playlistend": 1000}) as ydl:
        playd = ydl.extract_info(playlist_id, download=False)
        videos = [{"channel_id": channel_id, "description": vid["description"], "view_count": vid["view_count"],
                   "like_count": vid["like_count"], "dislike_count": vid["dislike_count"],
                   "title": vid["title"], "video_id": vid["id"], "upload_date": vid["upload_date"]} for vid in
                  playd["entries"] if type(vid) is dict]

        all_videos += videos

    return all_videos


def video_captions(video_id, download):
    try:
        captions = download.get_captions(video_id)
    except Exception:
        captions = None
    return captions


def video_comments(video_id):
    try:
        p = subprocess.check_output('node ./youtube_tools/get_comments.js {0}'.format(video_id), shell=True)
        comment = json.loads(p)
    except Exception:
        print("Could not load comment for video", video_id)
        comment = None
    # print(comment)
    return comment


def channel(dg):
    print(dg["channel_id"])
    if os.path.isfile("./data/subs/{0}.csv".format( dg["channel_id"])):
        print(dg["name"],  "already exists!")
        return
    download = Download()
    channel_id, name, category, channels_dst = dg["channel_id"], dg["name"], dg["category"], dg["channel_dst"]
    df_list = []

    for video in videos_in_channel(channel_id):
        video["captions"] = video_captions(video["video_id"], download)
        video["comments"] = video_comments(video["video_id"])
        video["name"] = name
        # video["category"] = category
        video["channel_id"] = channel_id
        df_list.append(video)

    df = pd.DataFrame(df_list)
    df.to_csv(channels_dst + channel_id + ".csv", index=False)


def channels(channels_src, channels_dst):
    df = pd.read_csv(channels_src)
    all_args = []
    for idx, row in df.iterrows():
        args = dict(row)
        args["channel_dst"] = channels_dst
        all_args.append(args)
    pool = mp.Pool(mp.cpu_count())
    pool.map(channel, all_args)


channels("./data/manosphere.csv", "./data/subs/")
