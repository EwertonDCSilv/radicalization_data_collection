from youtube_tools.utils import video_comments
from multiprocessing import Pool
from functools import partial
import pandas as pd
import argparse
import glob

parser = argparse.ArgumentParser(description="""""")

parser.add_argument("--src", dest="src", type=str, default="./data/youtube/yt/",
                    help="Source folder created by `loader_youtube.py`")

parser.add_argument("--dst", dest="dst", type=str, default="./data/youtube/cm/",
                    help="Where to save the output files.")

parser.add_argument("--nump", dest="nump", type=int, default=1,
                    help="Number of simultaneous processes.")

parser.add_argument("--debug", dest="debug", action="store_true",
                    help="Runs w/o multiprocessing for debugging.")

args = parser.parse_args()

to_run = []

for file_path in glob.glob(args.src + "*.csv"):
    channel_id = file_path.split("/")[-1][:-4]
    df = pd.read_csv(file_path)
    video_ids = list(df.video_id.values)
    if not args.debug:
        to_run.append((channel_id, video_ids, args.dst))

    else:
        to_run.append(partial(video_comments, channel_id=channel_id, video_ids=video_ids, channel_dst=args.dst))

if not args.debug:
    p = Pool(args.nump)
    p.starmap(video_comments, to_run)
else:
    for i in to_run:
        i()
