# ProgrammingIdeaBot
# 
# This bot will randomly select an idea from a database and optionally
# based on the given difficulty level, give the user an idea
#
# Usage: python3 bot.py [action] <phrase>
#     action: All possible actions which can be added to bot
#         run: Run the default application of the bot
#         test: Test a specific phrase to determine how the bot interprets it. It does not run the main application
#         sim: Set the bot to simulation mode where it does not post to reddit
#         help: Show help/usage output
#     phrase: This is the phrase to test with the 'test' action
# 

import os
import sys
import csv
import math
import time
import praw
import random
import configparser

config = None
MIN_NUM_ARGS = 1

SIMULATE = False
SIMULATE_WAIT_TO_CONFIRM = False
MIN_NUM_WORDS_IN_TITLE = 4
ACCEPTABLE_RATIO = 0.25

subreddits_to_scan = ['learnpython']

idea_query_words = []
active_rejection_words = []

ideas = {
    'all': [],
    'easy': [],
    'intermediate': [],
    'hard': [],
}

file_praw_ini = 'praw.ini'
file_ideas_csv = 'assets/ideas.csv'
file_rejection_words = 'assets/rejection_words.txt'
file_suggestion_words = 'assets/suggestion_words.txt'

ERROR_GENERAL = 1
ERROR_FILE_MISSING = 2

def create_user_agent():
    ''' Create the user agent string '''
    c = config['DEFAULT']
    username = c['username']
    version = c['version']
    author = c['author']
    user_agent = f'{username}:{version} (by {author})'
    return user_agent

def init_reddit_client():
    ''' Initialize an instance of the PRAW reddit client using the assumed praw.ini in the same directory '''
    reddit = praw.Reddit()
    reddit.user.me()
    return reddit

def init_config_file():
    ''' Initizalize the config file in the same directory'''

    check_file_exists(file_praw_ini, "The config file praw.ini is missing")

    global config
    config = configparser.ConfigParser()
    config.read('praw.ini')

def check_file_exists(path, error_msg):
    ''' Check if file exists, if not then quit application '''
    if not os.path.exists(path):
        print(error_msg)
        sys.exit(ERROR_FILE_MISSING)

def init_ideas():
    ''' Open the Ideas Database and fill idea stucture '''

    check_file_exists(file_ideas_csv, 'Ideas csv is missing')
    with open(file_ideas_csv) as csvfile:
        reader = csv.reader(csvfile, delimiter=',', skipinitialspace=True)
        for index, row in enumerate(reader):
            if index == 0:
                continue
            diffculty = row[1].replace('"', '').strip()
            ideas['all'].append(row)
            ideas[diffculty].append(row)

def init_suggestion_words():
    ''' Open the suggestion words database and fill list '''

    check_file_exists(file_suggestion_words, 'Suggestion text file is missing')
    with open(file_suggestion_words, 'r') as reader:
        global idea_query_words
        idea_query_words = reader.read().split()

def init_rejection_words():
    ''' Opne the rejection words database and fill list '''

    check_file_exists(file_rejection_words, 'Rejection text file is missing')
    with open(file_rejection_words, 'r') as reader:
        global active_rejection_words
        active_rejection_words = reader.read().split()

def initialize():
    ''' Initialize all things used for the application '''

    # Read the configuration INI file
    init_config_file()

    # Import the ideas
    init_ideas()
    print('Read:', len(ideas['all']), 'idea entries')

    # Import suggestion words
    init_suggestion_words()
    print('Read:', len(idea_query_words), 'suggestion entries')

    # Import rejection words
    init_rejection_words()
    print('Read:', len(active_rejection_words), 'rejction entries')

    # Initialize the reddit client
    reddit = init_reddit_client()

    return reddit

def process_title(title):
    '''
        Process the title to determine if help is requested

        Parameters:
            title (string): The title of the reddit post/phrase
        
        Returns:
            ratio (string): 0.0 - 1.0 Representing the ratio of cout to total_words
            count (int): The number of words in the suggestion_words list
            total_words (int): The number of words in the title
            error (string): Reason for rejection
    '''

    errors = []

    # Put to lowercase and remove extras
    title = title.lower().replace("?", "").replace("!", "").replace(".", "").replace(",", "").replace("/", " ").replace("[", "").replace("]", "")
    words = title.split()

    count = 0
    total_words = len(words)

    # Confirm Word length is met
    if total_words < MIN_NUM_WORDS_IN_TITLE:
        errors.append(f'Minimum number of words {MIN_NUM_WORDS_IN_TITLE} not met with {total_words} words')

    # Process each work
    for word in words:
        if word in active_rejection_words:
            errors.append(f'Rejecting ({word}): {title}')
        if word in idea_query_words:
            count += 1

    # Calculate ratio
    ratio = float(count / total_words)
    if ratio < ACCEPTABLE_RATIO:
        errors.append(f'Minimum ratio is not met')

    # Append label to error message to get total number errors
    if len(errors) > 0:
        errors.insert(0, f'{len(errors)} Errors')

    return ratio, count, total_words, '\n'.join(errors)

def output_stats(title, count, total, ratio, error_msg):
    ''' DEBUG: Used for outputting information '''
    if error_msg == '':
        status = 'Accepted'
    else:
        status = 'Rejected'

    print(f'Title: {title}\nCount: {count}\nLenth: {total}\nRatio: {ratio}\nStatus: {status}\nError Message: {error_msg}\n-------------')

def submission_contains_bot_response(submission):
    ''' Determine if the submission contains the bot post already '''
    for comment in submission.comments:
        if comment.author == config['DEFAULT']['username']:
            return True
    return False

def submission_has_idea_request(submission):
    ''' Determine if the given submission has an idea request '''

    has_idea_request = False

    # Confirm bot has not commented on post before
    contains_bot_already = submission_contains_bot_response(submission)
    if contains_bot_already:
        return has_idea_request

    # Process the post's title to check if it pass criteria for idea request
    ratio, count, total_words, error = process_title(submission.title)
    output_stats(submission.title, count, total_words, ratio, error)
    if error == '':
        # print(f'Accepting:', submission.title)
        has_idea_request = True
    else:
        # print(f'Rejecting:', error)
        has_idea_request = False

    return has_idea_request

def get_random(ideas, desired_difficulty='none'):
    '''
    Get a random idea from the list

    Argument:
        ideas (list<csvrow>): The list of ideas parsed from database
        desired_difficulty (string): The default difficulty. Defaults (none/all).

    Returns:
        idea (csvrow): A random idea
    '''
    if desired_difficulty == 'easy' or desired_difficulty == 'intermediate' or desired_difficulty == 'hard':
        tmp_ideas = ideas[desired_difficulty]
    else:
        tmp_ideas = ideas['all']

    num = random.randrange(0, len(tmp_ideas))
    return tmp_ideas[num]

def format_response(idea):
    ''' Return the formatted text to post to reddit '''

    repo_url = config['DEFAULT']['repo_url']
    raw_project_name = idea[0]
    raw_difficulty = idea[1]
    raw_description = idea[2]

    # Replace the text for the difficulty for diffent output
    if raw_difficulty == 'easy':
        difficulty = 'nice'
    elif raw_difficulty == 'intermediate':
        difficulty = 'cool'
    elif raw_difficulty == 'hard':
        difficulty = 'challenging'
    else:
        difficulty = 'fasinating'

    response = ''
    response += f'Hey, I think you are trying to figure out a project to do; how about this one?\n\n'
    response += f'Project: **{raw_project_name}** \n\n'
    response += f'I think its a _{difficulty}_ project for you! Try it out but, dont get discouraged. If you need more guidance, here\'s a description:\n'
    response += f'>{raw_description}\n\n\n'
    response += f'^(I am a bot, so give praises if I was helpful or curses if I was not.)\n'
    response += f'^(If you want to undertand me more, my code is on [Github]({repo_url}) )\n'
    
    return response

def reply_with_idea(submission, idea):
    ''' Reply with the idea to given reddit submission (post) '''
    print('Responding with idea:', idea[0])
    response = format_response(idea)
    try:
        if SIMULATE:
            print('Would be output:\n', response)
            if SIMULATE_WAIT_TO_CONFIRM:
                option = input('Would you like to continue (Y/n):').lower()
                if option == 'y' or option == '':
                    print('\n\n\n\n\n\n\n\n\n')
                    print(f'[{time.time()}]: Waiting for more posts...')
                else:
                    exit(1)
        else:
            new_comment = submission.reply(response)
            if new_comment == None:
                print("[Error]: Failed to post new comment")
    except praw.exceptions.RedditAPIException as e:
        print(e)
    return False

def stream_subreddits(reddit):
    ''' Blocking method to continuously check all 'subreddits_to_scan' for new posts '''
    query = '+'.join(subreddits_to_scan)
    print('Query:', query, '\n\n----------------')
    subreddits = reddit.subreddit(query)
    for submission in subreddits.stream.submissions():
        idea_requested = submission_has_idea_request(submission)
        if idea_requested:
            idea = get_random(ideas)
            reply_with_idea(submission, idea)
    return False

def run():
    ''' Run the main purpose application '''
    reddit = initialize()
    stream_subreddits(reddit)

def test_phrase(phrase):
    ''' Test a specific phrase to see how the main application would interpret it '''
    init_rejection_words()
    init_suggestion_words()

    # Process the phrase and report
    ratio, count, total, error = process_title(phrase)
    output_stats(phrase, count, total, ratio, error)

def start():
    ''' Run test method for the application '''

    action = sys.argv[1].lower()
    if action == 'run': 
        if len(sys.argv) > MIN_NUM_ARGS:
            run()
        else:
            print('Too many arguments to run normal operation')
    elif action == 'test':
        if len(sys.argv) >= 3:
            phrase = sys.argv[2]
            test_phrase(phrase)
    elif action == 'sim':
        turn_ON_simulation_mode()
        run()
    elif action == 'ver':
        init_config_file()
        c = config['DEFAULT']
        print(c['version'])
    elif action == 'help':
        show_help()
    else:
        print('Unknown test argument:', action)

def turn_ON_simulation_mode():
    ''' Turn on the simulation flag '''
    global SIMULATE
    SIMULATE = True
    print('Simulation mode turned: ON')

def turn_OFF_simulation_mode():
    ''' Turn off the simulation flag '''
    global SIMULATE
    SIMULATE = False
    print('Simulation mode turned: OFF')

def show_help():
    output = ''

    output += f'Usage: python3 bot.py [action] <phrase>\n'
    output += f'    action: All possible actions which can be added to bot\n'
    output += f'        run: Run the default application of the bot\n'
    output += f'        test: Test a specific phrase to determine how the bot interprets it. It does not run the main application\n'
    output += f'        sim: Set the bot to simulation mode where it does not post to reddit\n'
    output += f'        help: Show help/usage output\n'
    output += f'    phrase: This is the phrase to test with the "test" action\n'

    print(output)

def main():
    ''' Main method to fire up the application based on command args '''
    
    # Remove one args, first one is name of bot
    num_args = len(sys.argv) - 1

    try:
        # Determine type of runtime
        if num_args >= MIN_NUM_ARGS:
            start()
        else:
            print(f'Unexpected usage with {num_args} args')
            show_help()
    except KeyboardInterrupt:
        print('')

if __name__ == "__main__":
    main()
