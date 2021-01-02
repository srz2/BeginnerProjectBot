from os import path, remove
from shutil import copy
import configparser
import unittest
from projectbot.Configuration import Configuration


class FileINIConfigured(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.file_test_ini = 'praw.ini'
        self.create_test_ini(self)

    @classmethod
    def tearDownClass(self):
        remove(self.file_test_ini)

    def create_test_ini(self):
        sample_ini = '\
            [DEFAULT]\n\
            username=BeginnerProjectBot\n\
            user_agent=[REDDIT_USER_AGENT]\n\n\
            ; App Information\n\
            version=0.6\n\
            author=/u/srz2\n'

        with open(self.file_test_ini, 'w') as file:
            file.write(sample_ini)

    def test_ini_exists(self):
        exists = path.exists(self.file_test_ini)
        self.assertTrue(exists)

    def test_ingest_ini(self):
        parser = configparser.ConfigParser()
        parser.read(self.file_test_ini)
        config = parser['DEFAULT']
        config['dummy'] = 'dummy'
    
    def test_configuration_ini(self):
        config = Configuration()
        self.assertRegex(config['user_agent'], r'BeginnerProjectBot:[0-9].[0-9] \(by \/u\/srz2\)')
