# ProgrammingIdeaBot
# 
# This bot will randomly select an idea from a database and optionally
# based on the given difficulty level, give the user an idea
#
# Usage: python3 bot.py [action] <args...>
#     action: All possible actions which can be added to bot
#         run: Run the default application of the bot
#         test: Test a specific phrase to determine how the bot interprets it. It does not run the main application
#             phrase: Add this following the test action
#         sim: Set the bot to simulation mode where it does not post to reddit
#             confirm: Add this following the test action
#         help: Show help/usage output
# 

import os
import sys
import csv
import math
import time
import praw
import random
import threading
import configparser
import initialize as init
import threadChecker as ThreadChecker
import stream as stream
config = None
MIN_NUM_ARGS = 1

SIMULATE = False
SIMULATE_WAIT_TO_CONFIRM = False

subreddits_to_scan = []
subreddits_to_scan_prod = ['learnpython']
subreddits_to_scan_stag = ['SRZ2_TestEnvironment']

idea_query_words = []
active_rejection_words = []

ERROR_GENERAL = 1
ERROR_FILE_MISSING = 2
ERROR_LOGIN_FAILED = 3


def create_user_agent():
    ''' Create the user agent string '''
    c = config['DEFAULT']
    username = c['username']
    version = c['version']
    author = c['author']
    user_agent = f'{username}:{version} (by {author})'
    return user_agent

def audit_app_level():
    ''' Audit the app level and configure settings on it '''
    level = os.environ.get('app_level')

    # Change subreddits to scan
    if level == 'production':
        subreddits_to_scan = subreddits_to_scan_prod
    elif level == 'staging':
        subreddits_to_scan = subreddits_to_scan_stag
    else:
        subreddits_to_scan = subreddits_to_scan_stag

    return subreddits_to_scan

def run(simulate,subreddits):
    ''' Run the main purpose application '''
    initialized = init.initialize(simulate,subreddits)

    threads = []
    thread_post_checker = ThreadChecker.ThreadPostChecker('Post Checker', initialized)
    threads.append(thread_post_checker)

    thread_comment_checker = ThreadChecker.ThreadCommentChecker('Comment Stream Checker', initialized)
    threads.append(thread_comment_checker)

    # Start all threads
    for thread in threads:
        thread.daemon = True
        thread.start()

    # Join all threads
    for thread in threads:
        thread.join()

def test_phrase(phrase):
    ''' Test a specific phrase to see how the main application would interpret it '''
    reject_words = init.init_rejection_words()
    suggest_words = init.init_suggestion_words()

    # Process the phrase and report
    ratio, count, total, error = stream.process_title(phrase,reject_words,suggest_words)
    stream.output_stats(phrase, count, total, ratio, error)

def start(subreddits):
    ''' Run test method for the application '''
    simulate = {
        'sim' : False,
        'sim-confirm' : False 
    }
    action = sys.argv[1].lower()
    if action == 'run': 
        if len(sys.argv) > MIN_NUM_ARGS:
            run(simulate,subreddits)
        else:
            print('Too many arguments to run normal operation')
    elif action == 'test':
        if len(sys.argv) >= 3:
            phrase = sys.argv[2]
            test_phrase(phrase)
    elif action == 'sim':
        simulate['sim'] = turn_ON_simulation_mode()

        if len(sys.argv) >= 3:
            if sys.argv[2].lower() == 'confirm':
               simulate['sim-confirm']  = True
            else:
                print('Unknown simulation argument:', sys.argv[2])

        run(simulate,subreddits)
    elif action == 'ver':
        config = init.init_config_file()
        c = config['DEFAULT']
        print(c['version'])
    elif action == 'help':
        show_help()
    else:
        print('Unknown test argument:', action)

def turn_ON_simulation_mode():
    ''' Turn on the simulation flag '''
    simulate = True
    print('Simulation mode turned: ON')
    return simulate

def turn_OFF_simulation_mode():
    ''' Turn off the simulation flag '''
    simulate = False
    print('Simulation mode turned: OFF')
    return simulate

def show_help():
    output = ''

    output += f'Usage: python3 bot.py [action] <args...>\n'
    output += f'    action: All possible actions which can be added to bot\n'
    output += f'        run: Run the default application of the bot\n'
    output += f'        test: Test a specific phrase to determine how the bot interprets it. It does not run the main application\n'
    output += f'            phrase: Add this following the test action\n'
    output += f'        sim: Set the bot to simulation mode where it does not post to reddit\n'
    output += f'            confirm: Add this following the test action\n'
    output += f'        help: Show help/usage output\n'

    print(output)

def main():
    ''' Main method to fire up the application based on command args '''
    
    # Remove one args, first one is name of bot
    num_args = len(sys.argv) - 1

    # Differ settings based on app_level
    subreddits_to_scan = audit_app_level()

    try:
        # Determine type of runtime
        if num_args >= MIN_NUM_ARGS:
            start(subreddits_to_scan)
        else:
            print(f'Unexpected usage with {num_args} args')
            show_help()
    except KeyboardInterrupt:
        print('')

if __name__ == "__main__":
    main()
