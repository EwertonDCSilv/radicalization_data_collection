from youtube_tools.utils import channel
from multiprocessing import Pool
import pandas as pd
import argparse

parser = argparse.ArgumentParser(description="""This scripts receives a `.csv` file with channel ids, categories and 
                                                the data collection step, and a dest folder. It creates one file per
                                                channel in the destiny folder containing info about the videos for that
                                                channel.""")

parser.add_argument("--src", dest="src", type=str, default="./data/sources.csv",
                    help="A .csv containing rows `Name`, `Category`, `Data Collection step`, `Id`")

parser.add_argument("--dst", dest="dst", type=str, default="./data/yt2/",
                    help="Where to save the output files.")

parser.add_argument("--nump", dest="nump", type=int, default=1,
                    help="Number of simultaneous processes.")

args = parser.parse_args()

df = pd.read_csv(args.src)

to_run = []
for idx, row in df.iterrows():
    args_pd = dict(row)
    to_run.append((args_pd["Id"], args.dst, args_pd["Name"],
                   args_pd["Data Collection step"], args_pd["Category"]))

p = Pool(args.nump)
p.starmap(channel, to_run)
