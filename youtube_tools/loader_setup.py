import argparse
import os

parser = argparse.ArgumentParser(description="""This creates the folder structure for the other YouTube scripts""")

parser.add_argument("--apikey", dest="apikey", type=str, default="Your API key here", help="YouTube v3 API key.")
parser.add_argument("--cm", dest="cm", type=str, default="./data/youtube/cm/",
                    help="This is the folder where the comments are going to be stored.")
parser.add_argument("--cp", dest="cp", type=str, default="./data/youtube/cp/",
                    help="This is the folder where the captions are going to be stored.")
parser.add_argument("--rc", dest="rc", type=str, default="./data/youtube/rc/",
                    help="This is the folder where the graphs of recommended videos are going to be stored.")
parser.add_argument("--yt", dest="yt", type=str, default="./data/youtube/yt/",
                    help="This is the folder where stats and info about videos are going to be stored.")
args = parser.parse_args()

os.makedirs(args.cm, exist_ok=True)
os.makedirs(args.cp, exist_ok=True)
os.makedirs(args.rc, exist_ok=True)
os.makedirs(args.yt, exist_ok=True)
