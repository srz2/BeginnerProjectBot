import os
import configparser
from Utilities import *
from Constants import Const, Asset

class Configuration:
    def __init__(self):

        self.config = None
        self.SIMULATE = False
        self.SIMULATE_WAIT_TO_CONFIRM = False

        self.init_config_with_ini()
    
    def __getitem__(self, item):
        return self.config[item]

    def init_config_with_ini(self):
        exists = check_file_exists(Asset.file_praw_ini, "The config file praw.ini is missing")
        if not exists:
            raise Exception('Missing praw.ini')

        parser = configparser.ConfigParser()
        parser.read(Asset.file_praw_ini)
        self.config = parser['DEFAULT']

def get_app_level():
    level = os.environ.get('app_level')
    if level is None:
        level = Const.DEFAULT_APP_LEVEL
    return level


def add_user_agent_to_ini(new_user_agent):
    ''' Put new user agent text into the ini file '''

    temp_config = configparser.ConfigParser()
    temp_config.read(Asset.file_praw_ini)
    temp_config['DEFAULT']['user_agent'] = new_user_agent

    with open(Asset.file_praw_ini, 'w') as config_writer:
        temp_config.write(config_writer)
