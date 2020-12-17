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
from pymongo import MongoClient

config = None
MIN_NUM_ARGS = 1

SIMULATE = False
SIMULATE_WAIT_TO_CONFIRM = False
MIN_NUM_WORDS_IN_TITLE = 5
ACCEPTABLE_RATIO = 0.25
RATE_LIMIT_SLEEP_TIME = 600    # 10 minutes

subreddits_to_scan = []
subreddits_to_scan_prod = ['learnpython']
subreddits_to_scan_stag = ['SRZ2_TestEnvironment']

idea_query_words = []
active_rejection_words = []

ideas = {
    'all': [],
    'easy': [],
    'medium': [],
    'hard': [],
}

file_praw_ini = 'praw.ini'

file_ideas_csv = 'assets/ideas.csv'
coll_ideas_mongo = 'ideas'

file_rejection_words = 'assets/rejection_words.txt'
coll_rejection_mongo = 'rejection-words'

file_suggestion_words = 'assets/suggestion_words.txt'
coll_suggestion_mongo = 'suggestion-words'

ERROR_GENERAL = 1
ERROR_FILE_MISSING = 2
ERROR_LOGIN_FAILED = 3
ERROR_FILE_UPDATE = 4

class ThreadPostChecker(threading.Thread):
    ''' This thread will check the posts on all queried subreddits '''
    def __init__(self, name, reddit):
        threading.Thread.__init__(self)
        self.name = name
        self.reddit = reddit

    def run(self):
        threading.Thread.run(self)
        stream_subreddits(self.reddit)

class ThreadCommentChecker(threading.Thread):
    ''' This thread will check the comments on all queried subreddits '''
    def __init__(self, name, reddit):
        threading.Thread.__init__(self)
        self.name = name
        self.reddit = reddit

    def run(self):
        threading.Thread.run(self)
        stream_subreddits_comments(self.reddit)

def create_user_agent():
    ''' Create the user agent string '''

    temp_config = configparser.ConfigParser()
    temp_config.read(file_praw_ini)

    c = temp_config['DEFAULT']
    username = c['username']
    version = c['version']
    author = c['author']
    user_agent = f'{username}:{version} (by {author})'
    return user_agent

def audit_app_level():
    ''' Audit the app level and configure settings on it '''
    level = os.environ.get('app_level')

    # Change subreddits to scan
    global subreddits_to_scan
    if level == 'production':
        subreddits_to_scan = subreddits_to_scan_prod
    elif level == 'staging':
        subreddits_to_scan = subreddits_to_scan_stag
    else:
        subreddits_to_scan = subreddits_to_scan_stag

def init_reddit_client():
    ''' Initialize an instance of the PRAW reddit client using the assumed praw.ini in the same directory '''
    reddit = praw.Reddit()
    try:
        reddit.user.me()
    except:
        print('Failed to log into bot')
        exit(ERROR_LOGIN_FAILED)

    return reddit

def add_user_agent_to_ini(new_user_agent):
    ''' Put new user agent text into the ini file '''

    temp_config = configparser.ConfigParser()
    temp_config.read(file_praw_ini)
    temp_config['DEFAULT']['user_agent'] = new_user_agent

    with open(file_praw_ini, 'w') as config_writer:
        temp_config.write(config_writer)

def init_config_file():
    ''' Initizalize the config file in the same directory'''

    check_file_exists(file_praw_ini, "The config file praw.ini is missing")

    # Dynamically create user agent and modify to current INI file
    app_user_agent = create_user_agent()
    add_user_agent_to_ini(app_user_agent)

    global config
    config = configparser.ConfigParser()
    config.read(file_praw_ini)

    # Check that defailt user agent is not in INI file, quit if it is
    if config['DEFAULT']['user_agent'] == '[USER_AGENT]':
        print('Failed to update INI with user_agent')
        sys.exit(ERROR_FILE_UPDATE)

def check_file_exists(path, error_msg):
    ''' Check if file exists, if not then quit application '''
    if not os.path.exists(path):
        print(error_msg)
        sys.exit(ERROR_FILE_MISSING)

def get_docs_from_collection(list_name):
    ''' Get the doc collection from a collection '''
    dbname = config['DEFAULT']['username']
    username = config['DEFAULT']['mongo_username']
    password = config['DEFAULT']['mongo_password']

    client = MongoClient(f'mongodb+srv://{username}:{password}@cluster0.5398r.mongodb.net/{dbname}?retryWrites=true&w=majority')
    database = client.get_database(dbname)
    collection = database.get_collection(list_name)

    docs = collection.find({})
    return docs

def get_list_from_collection(list_name):
    ''' Get a list of terms from a collection '''
    all = []
    docs = get_docs_from_collection(list_name)
    for doc in docs:
        all.append(doc['term'])

    return all

def add_to_idea_list(newIdea):
    if not isinstance(newIdea, list):
        raise Exception('Failed to add new idea, not a list object')
    difficulty = newIdea[1].replace('"', '').strip()
    ideas['all'].append(newIdea)
    ideas[difficulty].append(newIdea)

def load_ideas_internal():
    ''' Open the Ideas Database and fill idea stucture '''

    check_file_exists(file_ideas_csv, 'Ideas csv is missing')
    with open(file_ideas_csv) as csvfile:
        reader = csv.reader(csvfile, delimiter=',', skipinitialspace=True)
        for index, row in enumerate(reader):
            if index == 0:
                continue
            add_to_idea_list(row)

def load_ideas_mongodb():
    docs = get_docs_from_collection(coll_ideas_mongo)
    for doc in docs:
        idea = [
            doc['name'],
            doc['difficulty'],
            doc['description']
        ]
        add_to_idea_list(idea)

def init_ideas():
    ''' Loads the ideas from external DB '''

    try:
        load_ideas_mongodb()
    except Exception as e:
        print('[Error]:', e)
        load_ideas_internal()

def load_suggestion_words_internal():
    ''' Open the suggestion words database and fill list '''

    check_file_exists(file_suggestion_words, 'Suggestion text file is missing')
    with open(file_suggestion_words, 'r') as reader:
        global idea_query_words
        idea_query_words = reader.read().split()

def load_suggestion_words_mongo():
    ''' Get the suggestion words from mongodb '''
    suggestions = get_list_from_collection(coll_suggestion_mongo)

    global idea_query_words
    idea_query_words = suggestions

def init_suggestion_words():
    ''' Loads the suggestion words from external DB '''
    try:
        load_suggestion_words_mongo()
    except Exception as e:
        print('[Error]:', e)
        load_suggestion_words_internal()
        pass

def load_rejection_words_default():
    ''' Opne the rejection words database and fill list '''

    check_file_exists(file_rejection_words, 'Rejection text file is missing')
    with open(file_rejection_words, 'r') as reader:
        global active_rejection_words
        active_rejection_words = reader.read().split()

def load_rejection_words_mongo():
    ''' Get the rejection words from mongodb '''

    rejections = get_list_from_collection(coll_rejection_mongo)

    global active_rejection_words
    active_rejection_words = rejections

def init_rejection_words():
    ''' Loads the rejectin words from external DB '''
    try:
        load_rejection_words_mongo()
    except Exception as e:
        print('[Error]:', e)
        load_rejection_words_default()

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

def is_recongized_difficulty(dif):
    dif = dif.lower()
    if dif in ['easy', 'medium', 'hard', 'all']:
        return True
    else:
        return False

def process_comment(content):
    '''
        Process the comment to determine if help is requested within the comment body

        Parameters:
            content (string): The body of the comment

        Returns:
            asking_for_help (boolean): The content is asking for a project
            difficulty (string): The difficulty requested
    '''

    # Acceptable phrases to trigger the bot
    phrases = []
    phrases.append('u/' + config['DEFAULT']['username'])
    phrases.append('!projectbot')

    # Put to lowercase and remove extras
    content = content.lower().replace('*', '').replace('_', ' ')

    difficulty = 'all'
    for phrase in phrases:
        if phrase in content:
            # Get the difficulty assuming it is the end of the phrase and the next word
            index = content.index(phrase) + len(phrase)
            if index < len(content):
                difficulty = content[index:].split()[0]
            if not is_recongized_difficulty(difficulty):
                difficulty = 'all'
            return True, difficulty

    return False, ''

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
    words = list(dict.fromkeys(title.split()).keys())

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

def comment_already_has_bot_response(comment):
    ''' Determine if comment already contains the bot''s response'''

    username = config['DEFAULT']['username']

    # This is potentially intensive if calling for every comment
    # Inititally the replies list is empty unless this is called
    comment.refresh()

    for inner_comment in comment.replies:
        if inner_comment.author == username:
            return True
    return False

def submission_contains_bot_response(submission):
    ''' Determine if the submission contains the bot post already '''

    username = config['DEFAULT']['username']

    for comment in submission.comments:
        if comment.author == username:
            return True
    return False

def comment_is_made_by_bot(comment):
    ''' Determine if the comment is the bot itself '''

    username = config['DEFAULT']['username']
    if comment.author == username:
        return True

    return False

def submission_has_project_request(submission):
    ''' Determine if the given submission is requesting help for a new project '''

    has_project_request = False

    # Confirm bot has not commented on post before
    contains_bot_already = submission_contains_bot_response(submission)
    if contains_bot_already:
        return has_project_request

    # Process the post's title to check if it pass criteria for project request
    ratio, count, total_words, error = process_title(submission.title)
    print('Id:', submission.id)
    output_stats(submission.title, count, total_words, ratio, error)
    if error == '':
        # print(f'Accepting:', submission.title)
        has_project_request = True
    else:
        # print(f'Rejecting:', error)
        has_project_request = False

    return has_project_request

def comment_has_project_request(comment):
    ''' Determine if the given comment is requesting help for a new project '''

    has_project_request = False

    # Confirm we are aren't processing a comment from the bot
    is_from_bot = comment_is_made_by_bot(comment)
    if is_from_bot:
        return has_project_request, ''

    has_project_request, difficulty = process_comment(comment.body)
    if has_project_request:
        # Confirm bot hasn't already responded to this comment already
        # This is after the process_comment() because it can be intensive
        # on every comment
        bot_already_responded = comment_already_has_bot_response(comment)
        if bot_already_responded:
            # Override the request
            has_project_request = False
            return has_project_request, ''
    
    return has_project_request, difficulty

def get_random(ideas, desired_difficulty='all'):
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

def get_bot_reference_text():
    ''' Format the text response for bot disclaimer '''

    repo_url = config['DEFAULT']['repo_url']

    response = ''
    response += f'^(I am a bot, so give praises if I was helpful or curses if I was not.)\n'
    response += f'^(Want a project? Comment with "!projectbot" and optionally add easy, medium, or hard to request a difficulty!)\n'
    response += f'^(If you want to understand me more, my code is on) ^[Github]({repo_url})'

    return response

def create_link_reference(text, url):
    '''
        Create a link for reddit for response

        Argument:
            - text (string): The shown text for the link
            - url (string): The destination URL for the link

        Returns:
            A link to put in the markdown response to a user
    '''

    return f'- [{text}]({url})\n'

def format_idea_response(idea):
    ''' Return the formatted text to post to reddit based on a given idea '''

    raw_project_name = idea[0]
    raw_difficulty = idea[1]
    raw_description = idea[2]

    # Replace the text for the difficulty for diffent output
    if raw_difficulty == 'easy':
        difficulty = 'nice'
    elif raw_difficulty == 'medium':
        difficulty = 'cool'
    elif raw_difficulty == 'hard':
        difficulty = 'challenging'
    else:
        difficulty = 'fasinating'

    response = ''
    response += f'Hey, I think you are trying to figure out a project to do; how about this one?\n\n'
    response += f'Project: **{raw_project_name}** \n\n'
    response += f'I think it''s a _' + difficulty + '_ project for you! Try it out but, dont get discouraged. If you need more guidance, here\'s a description:\n'
    response += f'>{raw_description}\n\n\n'
    response += get_bot_reference_text()
    
    return response

def format_basic_response():
    ''' Return the formatted text to post to reddit to direct a user to some project resources '''

    response = ''
    response += f'Hey, I think you are trying to figure out a project to do; Here are some helpful resources:\n\n'
    response += create_link_reference('/r/learnpython - Wiki', 'https://www.reddit.com/r/learnpython/wiki/index#wiki_flex_your_coding_skill.21')
    response += create_link_reference('Five mini projects', 'https://knightlab.northwestern.edu/2014/06/05/five-mini-programming-projects-for-the-python-beginner/')
    response += create_link_reference('Automate the Boring Stuff with Python', 'https://automatetheboringstuff.com/')
    response += create_link_reference('RealPython - Projects', 'https://realpython.com/tutorials/projects/')
    response += '\n'
    response += get_bot_reference_text()

    return response

def prompt_for_confirmation():
    option = input('Would you like to continue (Y/n/p):').lower()
    if option == 'y' or option == '':
        print('\n\n\n\n\n\n\n\n\n')
        print(f'[{time.time()}]: Waiting for more posts...')
    elif option == 'p':
        return option
    else:
        exit(1)

def reddit_send_comment_response(comment, response):
    new_comment = comment.reply(response)
    if new_comment == None:
        print('[Error]: Failed to post new comment')

def reddit_send_submission_response(submission, response):
    new_comment = submission.reply(response)
    if new_comment == None:
        print("[Error]: Failed to post new comment")

def respond_with_basic_response(submission):
    ''' Reply with the basic response to give resources to a user'''
    print('Responding with basic response')
    response = format_basic_response()
    try:
        if SIMULATE:
            print('Would be output:\n', response)
            if SIMULATE_WAIT_TO_CONFIRM:
                option = prompt_for_confirmation()
                if option == 'p':
                    reddit_send_submission_response(submission, response)
        else:
            reddit_send_submission_response(submission, response)
        return True
    except praw.exceptions.RedditAPIException as e:
        print(e)
        return False

def get_idea_and_respond_comment(comment, difficulty='all'):
    ''' Randomly get an idea and reply to the submission with it '''
    idea = get_random(ideas, difficulty)
    success = reply_comment_with_idea(comment, idea)
    return success

def get_idea_and_respond_submission(submission, diffculty='all'):
    ''' Randomly get an idea and reply to the submission with it '''
    idea = get_random(ideas, diffculty)
    success = reply_submission_with_idea(submission, idea)
    return success

def reply_comment_with_idea(comment, idea):
    ''' Reply with the idea to given reddit comment '''
    if idea == None:
        print('[CRIT]: Attempting to reply comment with a nulled idea')
        return False

    print(f'Responding to comment({comment.permalink}) with idea:', idea[0])
    response = format_idea_response(idea)
    try:
        if SIMULATE:
            print('Would be output:\n', response)
            if SIMULATE_WAIT_TO_CONFIRM:
                option = prompt_for_confirmation()
                if option == 'p':
                    reddit_send_comment_response(comment, response)
        else:
            reddit_send_comment_response(comment, response)
        return True
    except praw.exceptions.RedditAPIException as e:
        print(e)
        return False

def reply_submission_with_idea(submission, idea):
    ''' Reply with the idea to given reddit submission (post) '''
    print('Responding to post with idea:', idea[0])
    response = format_idea_response(idea)
    try:
        if SIMULATE:
            print('Would be output:\n', response)
            if SIMULATE_WAIT_TO_CONFIRM:
                option = prompt_for_confirmation()
                if option == 'p':
                    reddit_send_submission_response(submission, response)
        else:
            reddit_send_submission_response(submission, response)
        return True
    except praw.exceptions.RedditAPIException as e:
        print(e)
        return False

def stream_subreddits(reddit):
    ''' Blocking method to continuously check all 'subreddits_to_scan' for new posts '''
    query = '+'.join(subreddits_to_scan)
    print('Post Query:', query, '\n\n----------------')
    subreddits = reddit.subreddit(query)
    for submission in subreddits.stream.submissions():
        project_requested = submission_has_project_request(submission)
        if project_requested:
            success = respond_with_basic_response(submission)
            if not success:
                print('Failed to respond to post, trying again in', RATE_LIMIT_SLEEP_TIME, 'seconds')
                time.sleep(RATE_LIMIT_SLEEP_TIME + 5)
                respond_with_basic_response(submission)

def stream_subreddits_comments(reddit):
    ''' Blocking method to continuously check all 'subreddits_to_scan' for new comments '''
    query = '+'.join(subreddits_to_scan)
    print('Comment Query:', query, '\n\n----------------')
    subreddits = reddit.subreddit(query)
    for comment in subreddits.stream.comments():
        project_requested, difficulty = comment_has_project_request(comment)
        if project_requested:
            success = get_idea_and_respond_comment(comment, difficulty)
            if not success:
                print('Failed to respond to comment, trying again in', RATE_LIMIT_SLEEP_TIME, 'seconds')
                time.sleep(RATE_LIMIT_SLEEP_TIME + 5)
                get_idea_and_respond_comment(comment, difficulty)

def run():
    ''' Run the main purpose application '''
    reddit = initialize()

    threads = []
    thread_post_checker = ThreadPostChecker('Post Checker', reddit)
    threads.append(thread_post_checker)

    thread_comment_checker = ThreadCommentChecker('Comment Stream Checker', reddit)
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

        if len(sys.argv) >= 3:
            if sys.argv[2].lower() == 'confirm':
                global SIMULATE_WAIT_TO_CONFIRM
                SIMULATE_WAIT_TO_CONFIRM = True
            else:
                print('Unknown simulation argument:', sys.argv[2])

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
    audit_app_level()

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
