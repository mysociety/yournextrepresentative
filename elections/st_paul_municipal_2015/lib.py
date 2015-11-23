import re
import os
import json

from candidates.static_data import BaseAreaPostData




class AreaPostData(BaseAreaPostData):

    def shorten_post_label(self, post_label):
        return re.sub(r'^Council Member for ', '', post_label)

    def area_to_post_group(self, area_data):
        return area_data['country_name']

    def post_id_to_party_set(self, post_id):
        return 'st-paul'
