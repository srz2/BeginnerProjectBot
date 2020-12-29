import os
import sys
import praw

class BotInternals:
    def __init__(self):

        self.SIMULATE = False
        self.SIMULATE_WAIT_TO_CONFIRM = False

        self.subreddits_to_scan = []

        self.idea_query_words = []
        self.active_rejection_words = []
        self.ideas = {
            'all': [],
            'easy': [],
            'medium': [],
            'hard': [],
        }
        print('Initialized BotInternal')

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
        self.SIMULATE = True
        print('Simulation mode turned: ON')


    def turn_OFF_simulation_mode(self):
        ''' Turn off the simulation flag '''
        self.SIMULATE = False
        print('Simulation mode turned: OFF')

    def add_to_idea_list(self, newIdea):
        if not isinstance(newIdea, list):
            raise Exception('Failed to add new idea, not a list object')
        if len(newIdea) != 3:
            raise Exception('Failed to add new idea, improperly formatted list')
        difficulty = newIdea[1].replace('"', '').strip()
        self.ideas['all'].append(newIdea)
        self.ideas[difficulty].append(newIdea)