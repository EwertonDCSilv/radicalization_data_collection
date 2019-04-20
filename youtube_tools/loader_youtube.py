from youtube_tools.utils import channel, try_except
from multiprocessing import Pool
from functools import partial
import pandas as pd
import argparse

parser = argparse.ArgumentParser(description="""This scripts receives a `.csv` file with channel ids, categories and 
                                                the data collection step, and a dest folder. It creates one file per
                                                channel in the destiny folder containing info about the videos for that
                                                channel.""")

parser.add_argument("--src", dest="src", type=str, default="./data/youtube/sources.csv",
                    help="A .csv containing rows `Name`, `Category`, `Data Collection step`, `Id`")

parser.add_argument("--dst", dest="dst", type=str, default="./data/youtube/yt/",
                    help="Where to save the output files.")

parser.add_argument("--nump", dest="nump", type=int, default=5,
                    help="Number of simultaneous processes.")

parser.add_argument("--debug", dest="debug", action="store_true",
                    help="Runs w/o multiprocessing for debugging.")

args = parser.parse_args()

df = pd.read_csv(args.src)

to_run = []
for idx, row in df.iterrows():
    args_pd = dict(row)
    args_func = {
        "channel_dst": args.dst,
        "name": args_pd["Name"],
        "channel_id": args_pd["Id"],
        "data_step": args_pd["Data Collection step"],
        "category": args_pd["Category"]}
    if not args.debug:
        to_run.append((try_except, args_func))
    else:
        to_run.append(partial(try_except, channel, args_func))

if not args.debug:
    p = Pool(args.nump)
    p.starmap(try_except, to_run)
else:
    for i in to_run:
        i()
