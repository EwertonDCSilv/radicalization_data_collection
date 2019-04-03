from requests_html import HTMLSession
import multiprocessing as mp
import pandas as pd
import os
import re


def get_page(idv):
    url_tmp = template.format(str(idv), 1)