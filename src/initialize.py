import praw 
import configparser
import csv
import utility as util

file_praw_ini = 'src/praw.ini'
file_ideas_csv = 'src/assets/ideas.csv'
file_rejection_words = 'src/assets/rejection_words.txt'
file_suggestion_words = 'src/assets/suggestion_words.txt'

ERROR_GENERAL = 1
ERROR_FILE_MISSING = 2
ERROR_LOGIN_FAILED = 3

def init_reddit_client():
    ''' Initialize an instance of the PRAW reddit client using the assumed praw.ini in the same directory '''
    reddit = praw.Reddit()
    try:
        reddit.user.me()
    except:
        print('Failed to log into bot')
        exit(ERROR_LOGIN_FAILED)

    return reddit

def init_config_file():
    ''' Initizalize the config file in the same directory'''

    util.check_file_exists(file_praw_ini, "The config file praw.ini is missing")

    config = configparser.ConfigParser()
    config.read('praw.ini')
    return config

def init_ideas():
    ''' Open the Ideas Database and fill idea structure '''

    ideas = {
    'all': [],
    'easy': [],
    'medium': [],
    'hard': [],
    }

    util.check_file_exists(file_ideas_csv, 'Ideas csv is missing')
    with open(file_ideas_csv) as csvfile:
        reader = csv.reader(csvfile, delimiter=',', skipinitialspace=True)
        for index, row in enumerate(reader):
            if index == 0:
                continue
            difficulty = row[1].replace('"', '').strip()
            ideas['all'].append(row)
            ideas[difficulty].append(row)
    
    return ideas

def init_suggestion_words():
    ''' Open the suggestion words database and fill list '''

    util.check_file_exists(file_suggestion_words, 'Suggestion text file is missing')
    with open(file_suggestion_words, 'r') as reader:
        idea_query_words = reader.read().split()
        return idea_query_words

def init_rejection_words():
    ''' Open the rejection words database and fill list '''

    util.check_file_exists(file_rejection_words, 'Rejection text file is missing')
    with open(file_rejection_words, 'r') as reader:
        active_rejection_words = reader.read().split()
        return active_rejection_words

def initialize(simulate,subreddits):
    ''' Initialize all things used for the application '''

    initialized = {
    'config': {},
    'ideas': {},
    'query_words': [],
    'rejection_words': [],
    'reddit' : [],
    'subreddits' : subreddits,
    'simulate' : simulate
    }
    # Read the configuration INI file
    initialized['config'] = init_config_file()

    # Import the ideas
    initialized['ideas'] = init_ideas()
    print('Read:', len(initialized['ideas']['all']), 'idea entries')

    # Import suggestion words
    initialized['query_words'] = init_suggestion_words()
    print('Read:', len(initialized['query_words']), 'suggestion entries')

    # Import rejection words
    initialized['rejection_words'] = init_rejection_words()
    print('Read:', len(initialized['rejection_words']), 'rejection entries')

    # Initialize the reddit client
    initialized['reddit'] = init_reddit_client()

    return initialized