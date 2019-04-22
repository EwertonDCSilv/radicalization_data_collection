import pandas.errors as pderr
import pandas as pd
import argparse
import json
import os

parser = argparse.ArgumentParser(description="""""")

parser.add_argument("--src", dest="src", type=str, default="./data/youtube/yt/",
                    help="Source folder created by `loader_youtube.py`")

parser.add_argument("--graph", dest="graph", type=str, default="./data/youtube/rc/recommended_20190416Apr.jsonl",
                    help="Source folder created by `loader_youtube.py`")

args = parser.parse_args()


def error_msg(channel_id, name, error_msg):
    print("{}: {}\n{}".format(name, channel_id, error_msg))
    print("-" * 60)


with open(args.graph) as f:
    for line in f.readlines():
        channel = json.loads(line)

        try:
            df = pd.read_csv(args.src + channel["channel_id"] + ".csv")
            num_videos, expected_num_videos = len(df), int(channel["statistics"]["videoCount"])

            if num_videos < expected_num_videos and \
                    (num_videos - expected_num_videos > .15 * expected_num_videos or
                     num_videos - expected_num_videos > 5):
                print(num_videos, expected_num_videos)
                error_msg(channel["channel_id"], channel["name"], "Less videos than expected ({0} vs {1})"
                          .format(num_videos, expected_num_videos))

        except FileNotFoundError:
            error_msg(channel["channel_id"], channel["name"], "Does Not Exists!")

        except pderr.EmptyDataError:
            os.remove(args.src + channel["channel_id"] + ".csv")
            error_msg(channel["channel_id"], channel["name"], "Empty")
