from youtube_tools.utils import video_captions
from ytcc.download import Download
from multiprocessing import Pool
from functools import partial
import pandas as pd
import argparse
import glob


def write_captions_fun(_fun, _channel_id, _video_ids, _channel_dst, download=None):
    if download_global is not None:
        download = download_global
    _fun(_channel_id, _video_ids, _channel_dst, download)


def initialize_worker():
    global download_global
    download_global = Download()


parser = argparse.ArgumentParser(description="""""")

parser.add_argument("--src", dest="src", type=str, default="./data/youtube/yt/",
                    help="Source folder created by `loader_youtube.py`")

parser.add_argument("--dst", dest="dst", type=str, default="./data/youtube/cp/",
                    help="Where to save the output files.")

parser.add_argument("--nump", dest="nump", type=int, default=10,
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
        to_run.append((video_captions, channel_id, video_ids, args.dst))
    else:
        to_run.append(partial(write_captions_fun, video_captions, _channel_id=channel_id,
                              _video_ids=video_ids, _channel_dst=args.dst))

if not args.debug:
    p = Pool(args.nump, initializer=initialize_worker)
    p.starmap(write_captions_fun, to_run)
else:
    for i in to_run:
        initialize_worker()
        i()
