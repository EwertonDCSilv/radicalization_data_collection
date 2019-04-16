from youtube_tools.utils import get_recommended_n_stats, get_yt_api_key, write_json_fun
from multiprocessing import Pool
import pandas as pd
import argparse


parser = argparse.ArgumentParser(description="""Makes a graph with recommended channels from YouTube. For each channel,
                                                we also collect statistics, such as number of subscribers, etc.""")

parser.add_argument("--src", dest="src", type=str, default="./data/sources.csv",
                    help="A .csv containing channel ids in a row `Id`.")

parser.add_argument("--dst", dest="dst", type=str, default="./data/recommended.jsonl",
                    help="Where to save the .jsonl output.")

parser.add_argument("--key_path", dest="key_path", type=str, default="./youtube_tools/api_key.json",
                    help="Destination to .json containing the key to ytv3 API.")

parser.add_argument("--key", dest="key", default=None, help="ytv3 API key.")

parser.add_argument("--num_processes", dest="nump", type=int, default=4,
                    help="Number of simultaneous processes.")

args = parser.parse_args()
api_key = args.key if args.key is not None else get_yt_api_key(args.key_path)
df = pd.read_csv(args.src)

to_run = []
for idx, row in df.iterrows():
    args_pd = dict(row)
    name = args_pd["Name"]
    channel_id = args_pd["Id"]
    to_run.append((get_recommended_n_stats, channel_id, name, api_key, args.dst))

p = Pool(args.nump)
p.starmap(write_json_fun, to_run)
