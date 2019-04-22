import pandas.errors as pderr
import pandas as pd
import json
import os

src_folder = "./data/youtube/yt/yt/"

src_graph = "./data/youtube/rc/recommended_20190416Apr1555420335.jsonl"


def error_msg(channel_id, name, error_msg):
    print("{}: {}\n{}".format(name, channel_id, error_msg))
    print("-" * 60)


with open(src_graph) as f:
    for line in f.readlines():
        channel = json.loads(line)

        try:
            df = pd.read_csv(src_folder + channel["channel_id"] + ".csv")
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
            os.remove(src_folder + channel["channel_id"] + ".csv")
            error_msg(channel["channel_id"], channel["name"], "Empty")
