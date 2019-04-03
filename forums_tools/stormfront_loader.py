from requests_html import HTMLSession
import multiprocessing as mp
import pandas as pd
import os
import re


def get_page(idv):
    url_tmp = template.format(str(idv), 1)
    r = session.get(url_tmp)
    if len(re.findall(not_logged, str(r.text))) != 0 or \
            len(re.findall(dnot_exist, str(r.text))) != 0:
        return
    else:

        try:

            # print(url_tmp)

            texts = []
            try:
                num_pages = int(re.findall("[0-9]+", r.html.find(".pagenav .vbmenu_control", first=True).text)[1]) + 1
            except AttributeError:
                num_pages = 2
            navbar = [v.text.replace("> ", "").replace("/"," ").strip() for v in r.html.find(".navbar")]
            # print([v.text.replace("> ", "") for v in r.html.find(".navbar")])
            for counter in range(1, num_pages, 1):
                r = session.get(template.format(str(idv), counter))
                r.html.render()
                posts = re.findall("id=\"post[0-9]+", r.text)
                for postv in posts:
                    post_id = postv[8:]
                    try:
                        name = r.html.find("#postmenu_{0} a".format(post_id), first=True).text.split("\n")[0]
                    except AttributeError:
                        # Guest posts
                        name = None

                    acc_type = r.html.find("#postmenu_{0} + div".format(post_id), first=True).text.replace("\n", " ")
                    tmp = str(r.html.find("#edit{0}".format(post_id), first=True).text)

                    datetime_post = re.findall(r'[0-9]{2}-[0-9]{2}-[0-9]{4}, [0-9]{2}:[0-9]{2} \w{2}', tmp)
                    datetime_post = None if len(datetime_post) != 1 else datetime_post[0]

                    join_date = re.findall(r'Join Date: ([\w]{3} [0-9]{4})', tmp)
                    join_date = None if len(join_date) != 1 else join_date[0]

                    num_posts = re.findall(r'Posts: ([0-9][0-9,.]*)', tmp)
                    num_posts = None if len(num_posts) != 1 else num_posts[0]

                    post_count = r.html.find("#postcount{0}".format(post_id), first=True).text
                    title = str(r.html.find("#td_post_{0} .smallfont".format(post_id), first=True).text)
                    text = str(r.html.find("#td_post_{0} #post_message_{0}".format(post_id), first=True).text)

                    texts.append({
                        "post_count": post_count,
                        "post_id": post_id,
                        "name": name,
                        "acc_type": acc_type,
                        "join_date": join_date,
                        "num_posts": num_posts,
                        "datetime_post": datetime_post,
                        "title": title,
                        "text": text
                    })

            df = pd.DataFrame(texts)
            print("/".join(navbar))
            print("./" + "/".join(navbar[:-1]))
            os.makedirs("./" + "/".join(navbar[:-1]), exist_ok=True)
            df.to_csv("./" + "/".join(navbar) + ".csv", index=False)
        except Exception as ex:
            print(ex)
            with open("./Stormfront/logs.txt", "a+") as f:
                f.write(url_tmp + ":" + ex + "\n")


template = "https://www.stormfront.org/forum/t{0}-{1}/"
not_logged = "You are not logged in or you do not have permission to access this page"
dnot_exist = "No Thread specified. If you follownpm-inited a valid link, please notify the "
values = list(range(1, 1300000, 1))

session = HTMLSession()
pool = mp.Pool(mp.cpu_count())
pool.map(get_page, values)
