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

    with youtube_dl.YoutubeDL({"ignoreerrors": True, "playlistend": 3000}) as ydl:
        playd = ydl.extract_info(playlist_id, download=False)
        videos = [{"Id": channel_id, "description": vid["description"], "view_count": vid["view_count"],
                   "like_count": vid["like_count"], "dislike_count": vid["dislike_count"],
                   "title": vid["title"], "video_id": vid["id"], "upload_date": vid["upload_date"]} for vid in
                  playd["entries"] if type(vid) is dict]

        all_videos += videos

    return all_videos


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


def channel(dg):
    with open("./data/logs/yt_{0}.txt".format(mp.current_process().pid), "a") as f:
        if os.path.isfile("./data/yt/{0}.csv".format(dg["Id"])):
            print(dg["Name"], "already exists!")
            return
        download = Download()
        channel_id, name, category, data_step, channels_dst = dg["Id"], dg["Name"], dg["Sub-Category"], \
                                                              dg["Data Collection step"], dg["channel_dst"]
        df_list = []

        for video in videos_in_channel(channel_id):
            video["captions"] = video_captions(video["video_id"], download, f)
            video["comments"] = video_comments(video["video_id"], f)
            video["name"] = name
            video["step"] = data_step
            video["category"] = category
            video["id"] = channel_id
            df_list.append(video)

        df = pd.DataFrame(df_list)
        df.to_csv(channels_dst + channel_id + ".csv", index=False)


def channels(channels_src, channels_dst):
    df = pd.read_csv(channels_src)
    all_args = []
    for idx, row in df.iterrows():
        args = dict(row)
        args["idx"] = str(idx)
        args["channel_dst"] = channels_dst
        all_args.append(args)
    pool = mp.Pool(mp.cpu_count())
    pool.map(channel, all_args)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Wrong number of arguments")
    else:
        os.makedirs(sys.argv[2], exist_ok=True)
        channels(sys.argv[1], sys.argv[2])
