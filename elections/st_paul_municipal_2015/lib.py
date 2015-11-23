import re


def shorten_post_label(post_label):
    return re.sub(r'^Council Member for ', '', post_label)
