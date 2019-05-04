import pandas as pd
import argparse

parser = argparse.ArgumentParser(description="""This script creates an new index out of the difference between two
                                                existing indexes. The new index contains new posts and posts with 
                                                different number of replies.""")

parser.add_argument("--index_old", dest="index_old", type=str, default="./data/forums/incels/index_old.csv",
                    help="Location of old index file.")

parser.add_argument("--index_new", dest="index_new", type=str, default="./data/forums/incels/index_new.csv",
                    help="Location of old index file.")

parser.add_argument("--dst", dest="dst", type=str, default="./data/forums/incels/index_new.csv",
                    help="Location to save the diff index.")

args = parser.parse_args()

index_old = pd.read_csv(args.index_old)

index_new = pd.read_csv(args.index_new)

existing_links = list(index_old.link.values)

link_to_replies_old = {link: num_replies for link, num_replies in zip(index_old.link.values, index_old.replies.values)}

flag_new = index_new.link.apply(lambda x: x not in existing_links)

flag_replies = index_new.apply(lambda x: x["link"] in existing_links and
                                         x["replies"] != link_to_replies_old[x["link"]], axis=1)

index_new[flag_new | flag_replies].to_csv(args.dst, index=False)
