import os
import sys
import csv
import praw
import random
from Utilities import is_recongized_difficulty
from Configuration import *
from RedditActions import *
from Database import *

class BotInternals:
    def __init__(self):

        self.database: Database = None
        self.reddit : RedditInterface = RedditInterface()
        self.config : Configuration = Configuration()

        self.subreddits_to_scan = []

        self.idea_query_words = []
        self.active_rejection_words = []
        self.ideas = {
            'all': [],
            'easy': [],
            'medium': [],
            'hard': [],
        }

        # Set app level
        level = get_app_level()
        self.set_app_level(level)

        # Initialize the database
        self.database = Database(self.config['mongo_username'],
                            self.config['mongo_password'],
                            self.config['username'])

    def set_app_level(self, level):
        from Constants import Const

        # Change subreddits to scan
        if level == 'production':
            print('Set to production settings')
            self.subreddits_to_scan = Const.SUBREDDITS_TO_SCAN_PROD
        else:
            print('Set to staging settings')
            self.subreddits_to_scan = Const.SUBREDDITS_TO_SCAN_STAG

    def turn_ON_simulation_mode(self):
        ''' Turn on the simulation flag '''
        self.config.SIMULATE = True
        print('Simulation mode turned: ON')

    def turn_OFF_simulation_mode(self):
        ''' Turn off the simulation flag '''
        self.config.SIMULATE = False
        print('Simulation mode turned: OFF')

    def add_to_idea_list(self, newIdea):
        if not isinstance(newIdea, list):
            raise Exception('Failed to add new idea, not a list object')
        if len(newIdea) != 3:
            raise Exception('Failed to add new idea, improperly formatted list')
        difficulty = newIdea[1].replace('"', '').strip()
        self.ideas['all'].append(newIdea)
        self.ideas[difficulty].append(newIdea)
    
    def add_ideas_range(self, idea_list):
        if not isinstance(idea_list, list):
            raise Exception('Failed to add new idea list, not a list object')
        for idea in idea_list:
            self.add_to_idea_list(idea)

    def get_ideas_internal(self):
        ''' Open the Ideas Database and fill idea stucture '''

        ideas = []
        check_file_exists(Asset.file_ideas_csv, 'Ideas csv is missing')
        with open(Asset.file_ideas_csv) as csvfile:
            reader = csv.reader(csvfile, delimiter=',', skipinitialspace=True)
            for index, row in enumerate(reader):
                if index == 0:
                    continue
                ideas.append(row)
        return ideas


    def get_ideas_mongodb(self):
        ideas = []
        docs = self.database.get_docs_from_collection(Asset.coll_ideas_mongo)
        for doc in docs:
            idea = [
                doc['name'],
                doc['difficulty'],
                doc['description']
            ]
            ideas.append(idea)

        return ideas


    def get_ideas(self):
        ''' Loads the ideas from external DB '''

        ideas = []

        try:
            ideas = self.get_ideas_mongodb()
            print('Loaded ideas from mongo')
        except Exception as e:
            print('[Error]:', e)
            ideas = self.get_ideas_internal()
            print('Loaded ideas from internal')

        return ideas


    def get_suggestion_words_internal(self):
        ''' Open the suggestion words database and fill list '''

        suggestions = []
        check_file_exists(Asset.file_suggestion_words,
                        'Suggestion text file is missing')
        with open(Asset.file_suggestion_words, 'r') as reader:
            suggestions = reader.read().split()
        return suggestions


    def get_suggestion_words_mongo(self):
        ''' Get the suggestion words from mongodb '''
        suggestions = self.database.get_list_from_collection(
            Asset.coll_suggestion_mongo)
        return suggestions


    def get_suggestion_words(self):
        ''' Loads the suggestion words from external DB '''
        suggestions = []

        try:
            suggestions = self.get_suggestion_words_mongo()
            print('Loaded suggestions from mongo')
        except Exception as e:
            print('[Error]:', e)
            suggestions = self.get_suggestion_words_internal()
            print('Loaded suggestions from internal')
            pass

        return suggestions


    def get_rejection_words_default(self):
        ''' Opne the rejection words database and fill list '''

        rejections = []
        check_file_exists(Asset.file_rejection_words,
                        'Rejection text file is missing')
        with open(Asset.file_rejection_words, 'r') as reader:
            rejections = reader.read().split()

        return rejections


    def get_rejection_words_mongo(self):
        ''' Get the rejection words from mongodb '''

        rejections = self.database.get_list_from_collection(Asset.coll_rejection_mongo)
        return rejections


    def get_rejection_words(self):
        ''' Loads the rejectin words from external DB '''
        rejections = []

        try:
            rejections = self.get_rejection_words_mongo()
            print('Loaded rejections from mongo')
        except Exception as e:
            print('[Error]:', e)
            rejections = self.get_rejection_words_default()
            print('Loaded rejections from internal')

        return rejections


    def initialize(self):
        ''' Initialize all things used for the application '''

        # Import the ideas
        retrieved_ideas = self.get_ideas()
        self.add_ideas_range(retrieved_ideas)
        print('Read:', len(self.ideas['all']), 'idea entries')

        # Import suggestion words
        self.idea_query_words = self.get_suggestion_words()
        print('Read:', len(self.idea_query_words), 'suggestion entries')

        # Import rejection words
        self.active_rejection_words = self.get_rejection_words()
        print('Read:', len(self.active_rejection_words), 'rejction entries')

    def get_random_idea(self, ideas, desired_difficulty='all'):
        '''
        Get a random idea from the list

        Argument:
            ideas (list<csvrow>): The list of ideas parsed from database
            desired_difficulty (string): The default difficulty. Defaults to all.

        Returns:
            idea (csvrow): A random idea
        '''

        # Check ideas is filled
        if len(ideas['all']) == 0:
            return None

        if is_recongized_difficulty(desired_difficulty):
            tmp_ideas = ideas[desired_difficulty]
        else:
            tmp_ideas = ideas['all']

        num = random.randrange(0, len(tmp_ideas))
        return tmp_ideas[num]
