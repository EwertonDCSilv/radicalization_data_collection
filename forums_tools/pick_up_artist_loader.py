from pick_up_artist_utils import build_index, get_thread, build_topics_index
from utils import get_thread_global, initialize_worker, get_html_session
from multiprocessing import Pool
import pandas as pd
import argparse
import os

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="""This script downloads the pick up artist is forum""")

    parser.add_argument("--dst", dest="dst", type=str, default="./data/forums/pick_up_artist/",
                        help="Location to save the forum.")

    parser.add_argument("--index", dest="index", type=str, default="./data/forums/pick_up_artist/index.csv",
                        help="Location of index file.")

    parser.add_argument("--index_topics", dest="index_topics", type=str, default="./data/forums/pick_up_artist/index_topics.csv",
                        help="Location of index file.")

    parser.add_argument("--build_index", dest="build_index", action="store_true",
                        help="If true, builds index, otherwise gets posts.")

    parser.add_argument("--build_topics_index", dest="build_topics_index", action="store_true",
                        help="If true, builds topics index, otherwise gets posts.")

    parser.add_argument("--update", dest="build_index", action="store_true",
                        help="If true, rebuilds index and gets different posts.")

    parser.add_argument("--nump", dest="nump", type=int, default=15,
                        help="Number of simultaneous processes.")

    parser.add_argument("--debug", dest="debug", action="store_true",
                        help="Runs w/o multiprocessing for debugging.")

    args = parser.parse_args()

    os.makedirs(args.dst, exist_ok=True)

    if args.build_topics_index:
        build_topics_index(None, args.index, args.nump)

    elif args.build_index:
        topics_list = list(pd.read_csv(args.index_topics)["link"].values)
        for link in topics_list:
            build_index(link, args.index, args.nump)

    else:
        to_run = list(pd.read_csv(args.index)["link"].values)
        to_run = list(zip([get_thread]*len(to_run), to_run))

        if args.debug:

            get_html_session = get_html_session()
            for f, thread in to_run:
                f(thread, get_html_session)
        else:
            p = Pool(args.nump, initializer=initialize_worker)
            p.starmap(get_thread_global, to_run)
