from __future__ import unicode_literals

import re

def shorten_post_label(post_label):
    return re.sub(r'^(County Assembly Member for|Member of the National Assembly for|County Governor for|Women Representative for|Senator for|President of)\s+', '', post_label)
