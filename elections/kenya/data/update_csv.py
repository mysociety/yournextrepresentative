#!/usr/bin/env python

import requests


URLS = (
    ('2017_candidates_presidency.csv',
     'https://docs.google.com/a/mysociety.org/spreadsheets/d/10RBG4fIluYn2jBgCRBBQ--6yHTtppYrB2ef-zpmVxhE/export?format=csv'),
    ('2017_candidates_senate.csv',
     'https://docs.google.com/a/mysociety.org/spreadsheets/d/1x3_otOE376QFwfGO9vMC5qZxeIvGR3MR_UeflgLVLj8/export?format=csv'),
    ('2017_candidates_county_assemblies.csv',
     'https://docs.google.com/a/mysociety.org/spreadsheets/d/1ZWRN6XeN6dVhWqvdikDDeMp6aFM3zJVv9cmf80NZebY/export?format=csv'),
    ('2017_candidates_governors.csv',
     'https://docs.google.com/a/mysociety.org/spreadsheets/d/1RxXOwbHly8nv5-wVwnRSvNx5zYEs1Xvl0bPF1hfn_NI/export?format=csv'),
    ('2017_candidates_assembly.csv',
     'https://docs.google.com/a/mysociety.org/spreadsheets/d/1Ccj-yg_B92j5H9mUUCo6vaw1Zgjra0KoX9s5fzMDzJA/export?format=csv'),
    ('2017_candidates_wr.csv',
     'https://docs.google.com/a/mysociety.org/spreadsheets/d/1SPkbrnUbstmHWeIU0W3yxvOehhnj7GLHzcwWp2pGeXc/export?format=csv'),
)


for filename, url in URLS:
    with open(filename, 'wb') as f:
        f.write(requests.get(url).content)
