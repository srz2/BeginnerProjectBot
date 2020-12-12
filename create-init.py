# create-ini
#
# This will read and create the required INI file for this bot based on enviornment variables
#
# Usage: python3 create-ini.py <--force>
#   --force: Optionally force create
#

import os
import configparser

file_example_ini = 'src/praw.ini.example'
file_output_ini = 'src/praw.ini'

if not os.path.exists(file_example_ini):
    print('Example INI file not found')
    exit(1)

config = configparser.ConfigParser()
config.read(file_example_ini)

def get_env(key):
    value = os.environ.get(key)
    if value == None:
        value = '[' + key.replace('REDDIT_', '') + ']'
    return value


config['DEFAULT']['CLIENT_ID'] = get_env('REDDIT_CLIENT_ID')
config['DEFAULT']['CLIENT_SECRET'] = get_env('REDDIT_CLIENT_SECRET')
config['DEFAULT']['USER_AGENT'] = get_env('REDDIT_USER_AGENT')
config['DEFAULT']['USERNAME'] = get_env('REDDIT_USERNAME')
config['DEFAULT']['PASSWORD'] = get_env('REDDIT_PASSWORD')

with open(file_output_ini, 'w') as config_file:
    config.write(config_file, space_around_delimiters=False)
