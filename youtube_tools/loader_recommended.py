from youtube_tools.utils import get_recommended_n_stats, get_yt_api_key
from requests_html import HTMLSession
from multiprocessing import Pool
from datetime import datetime
from functools import partial
import pandas as pd
import argparse
import json
import fcntl


def write_json_fun(_fun, _channel_id, _name, _api_key, _dst_csv, session=None):
    if session_global is not None:
        session = session_global
    dict_out = _fun(_channel_id, _name, _api_key, session)
    with open(_dst_csv, "a") as g:
        fcntl.flock(g, fcntl.LOCK_EX)
        g.write(json.dumps(dict_out) + "\n")
        fcntl.flock(g, fcntl.LOCK_UN)


def initialize_worker():
    global session_global
    session_global = HTMLSession()


parser = argparse.ArgumentParser(description="""Makes a graph with recommended channels from YouTube. For each channel,
                                                we also collect statistics, such as number of subscribers, etc.""")

parser.add_argument("--src", dest="src", type=str, default="./data/sources.csv",
                    help="A .csv containing channel ids in a row `Id`.")

parser.add_argument("--dst", dest="dst", type=str, default="./data/rc/",
                    help="Folder to save the .jsonl output.")

parser.add_argument("--key_path", dest="key_path", type=str, default="./youtube_tools/api_key.json",
                    help="Destination to .json containing the key to ytv3 API.")

parser.add_argument("--key", dest="key", default=None, help="ytv3 API key.")

parser.add_argument("--num_processes", dest="nump", type=int, default=8,
                    help="Number of simultaneous processes.")

parser.add_argument("--debug", dest="debug", action="store_true",
                    help="Runs w/o multiprocessing for debugging.")

args = parser.parse_args()
api_key = args.key if args.key is not None else get_yt_api_key(args.key_path)
df = pd.read_csv(args.src)
dst = args.dst + "recommended_{0}.jsonl".format(datetime.now().strftime("%Y%m%d%h"))

to_run = []
for idx, row in df.iterrows():
    args_pd = dict(row)
    name = args_pd["Name"]
    channel_id = args_pd["Id"]

    if not args.debug:
        to_run.append((get_recommended_n_stats, channel_id, name, api_key, dst))

    else:
        to_run.append(partial(write_json_fun, _fun=get_recommended_n_stats, _channel_id=channel_id,
                              _name=name, _api_key=api_key, _dst_csv=dst))

if not args.debug:
    p = Pool(args.nump, initializer=initialize_worker)
    p.starmap(write_json_fun, to_run)
else:
    initialize_worker()
    for i in to_run:
        i()
