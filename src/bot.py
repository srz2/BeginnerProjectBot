# BeginnerProjectBot
# 
# This bot will randomly select an idea from a database and optionally
# based on the given difficulty level, give the user an idea
# 

import os
import sys
import math
import threading
from praw.exceptions import RedditAPIException
from projectbot.Constants import Const
from projectbot.Internals import BotInternals
from projectbot.Utilities import ResponseFormatter, output_stats, get_help, check_file_exists, is_recongized_difficulty, prompt_for_confirmation, time
from projectbot.Configuration import Configuration
from projectbot.RedditActions import RedditInterface

app : BotInternals = None
formatter : ResponseFormatter = None

class ThreadPostChecker(threading.Thread):
    ''' This thread will check the posts on all queried subreddits '''
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        threading.Thread.run(self)
        stream_subreddits()

class ThreadCommentChecker(threading.Thread):
    ''' This thread will check the comments on all queried subreddits '''
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        threading.Thread.run(self)
        stream_subreddits_comments()

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
    phrases.append('u/' + app.config['username'])
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
    if total_words < Const.MIN_NUM_WORDS_IN_TITLE:
        errors.append(f'Minimum number of words {Const.MIN_NUM_WORDS_IN_TITLE} not met with {total_words} words')

    # Process each work
    for word in words:
        if word in app.active_rejection_words:
            errors.append(f'Rejecting ({word}): {title}')
        if word in app.idea_query_words:
            count += 1

    # Calculate ratio
    ratio = float(count / total_words)
    if ratio < Const.ACCEPTABLE_RATIO:
        errors.append(f'Minimum ratio is not met')

    # Append label to error message to get total number errors
    if len(errors) > 0:
        errors.insert(0, f'{len(errors)} Errors')

    return ratio, count, total_words, '\n'.join(errors)

def comment_already_has_bot_response(comment):
    ''' Determine if comment already contains the bot''s response'''

    username = app.config['username']

    # This is potentially intensive if calling for every comment
    # Inititally the replies list is empty unless this is called
    comment.refresh()

    for inner_comment in comment.replies:
        if inner_comment.author == username:
            return True
    return False

def submission_contains_bot_response(submission):
    ''' Determine if the submission contains the bot post already '''

    username = app.config['username']

    for comment in submission.comments:
        if comment.author == username:
            return True
    return False

def comment_is_made_by_bot(comment):
    ''' Determine if the comment is the bot itself '''

    username = app.config['username']
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

def respond_with_basic_response(submission):
    ''' Reply with the basic response to give resources to a user'''
    print('Responding with basic response')
    response = formatter.format_basic_response()
    try:
        if app.config.SIMULATE:
            print('Would be output:\n', response)
            if app.config.SIMULATE_WAIT_TO_CONFIRM:
                option = prompt_for_confirmation()
                if option == 'p':
                    app.reddit.send_submission_response(submission, response)
        else:
            app.reddit.send_submission_response(submission, response)
        return True
    except RedditAPIException as e:
        print(e)
        return False

def get_idea_and_respond_comment(comment, difficulty='all'):
    ''' Randomly get an idea and reply to the submission with it '''
    idea = app.get_random_idea(app.ideas, difficulty)
    success = reply_comment_with_idea(comment, idea)
    return success

def get_idea_and_respond_submission(submission, diffculty='all'):
    ''' Randomly get an idea and reply to the submission with it '''
    idea = app.get_random_idea(app.ideas, diffculty)
    success = reply_submission_with_idea(submission, idea)
    return success

def reply_comment_with_idea(comment, idea):
    ''' Reply with the idea to given reddit comment '''
    if idea == None:
        print('[CRIT]: Attempting to reply comment with a nulled idea')
        return False

    print(f'Responding to comment({comment.permalink}) with idea:', idea[0])
    response = formatter.format_idea_response(idea)
    try:
        if app.config.SIMULATE:
            print('Would be output:\n', response)
            if app.config.SIMULATE_WAIT_TO_CONFIRM:
                option = prompt_for_confirmation()
                if option == 'p':
                    app.reddit.send_comment_response(comment, response)
        else:
            app.reddit.send_comment_response(comment, response)
        return True
    except RedditAPIException as e:
        print(e)
        return False

def reply_submission_with_idea(submission, idea):
    ''' Reply with the idea to given reddit submission (post) '''
    print('Responding to post with idea:', idea[0])
    response = formatter.format_idea_response(idea)
    try:
        if app.config.SIMULATE:
            print('Would be output:\n', response)
            if app.config.SIMULATE_WAIT_TO_CONFIRM:
                option = prompt_for_confirmation()
                if option == 'p':
                    app.reddit.send_submission_response(submission, response)
        else:
            app.reddit.send_submission_response(submission, response)
        return True
    except RedditAPIException as e:
        print(e)
        return False

def stream_subreddits():
    ''' Blocking method to continuously check all 'subreddits_to_scan' for new posts '''
    query = '+'.join(app.subreddits_to_scan)
    print('Starting Submission Stream - Post Query:', query)
    subreddits = app.reddit.query_subreddit(query)
    for submission in subreddits.stream.submissions():
        project_requested = submission_has_project_request(submission)
        if project_requested:
            success = respond_with_basic_response(submission)
            if not success:
                print('Failed to respond to post, trying again in', Const.RATE_LIMIT_SLEEP_TIME, 'seconds')
                time.sleep(Const.RATE_LIMIT_SLEEP_TIME + 5)
                respond_with_basic_response(submission)

def stream_subreddits_comments():
    ''' Blocking method to continuously check all 'subreddits_to_scan' for new comments '''
    query = '+'.join(app.subreddits_to_scan)
    print('Starting Comment Stream - Comment Query:', query)
    subreddits = app.reddit.query_subreddit(query)
    for comment in subreddits.stream.comments():
        project_requested, difficulty = comment_has_project_request(comment)
        if project_requested:
            success = get_idea_and_respond_comment(comment, difficulty)
            if not success:
                print('Failed to respond to comment, trying again in', Const.RATE_LIMIT_SLEEP_TIME, 'seconds')
                time.sleep(Const.RATE_LIMIT_SLEEP_TIME + 5)
                get_idea_and_respond_comment(comment, difficulty)

def run():
    ''' Run the main purpose application '''
    app.initialize()

    threads = []
    thread_post_checker = ThreadPostChecker('Post Checker')
    threads.append(thread_post_checker)

    thread_comment_checker = ThreadCommentChecker('Comment Stream Checker')
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
    app.initialize()

    # Process the phrase and report
    ratio, count, total, error = process_title(phrase)
    output_stats(phrase, count, total, ratio, error)

def start():
    ''' Run test method for the application '''

    action = sys.argv[1].lower()
    if action == 'run': 
        if len(sys.argv) > Const.MIN_NUM_ARGS:
            run()
        else:
            print('Too many arguments to run normal operation')
    elif action == 'test':
        if len(sys.argv) >= 3:
            phrase = sys.argv[2]
            test_phrase(phrase)
    elif action == 'sim':
        app.turn_ON_simulation_mode()

        if len(sys.argv) >= 3:
            if sys.argv[2].lower() == 'confirm':
                app.config.SIMULATE_WAIT_TO_CONFIRM = True
            else:
                print('Unknown simulation argument:', sys.argv[2])

        run()
    elif action == 'ver':
        version = app.config['version']
        print(version)
    elif action == 'help':
        output = get_help()
        print(output)
    else:
        print('Unknown test argument:', action)

def main():
    ''' Main method to fire up the application based on command args '''
    
    # Remove one args, first one is name of bot
    num_args = len(sys.argv) - 1

    try:
        # Determine type of runtime
        if num_args >= Const.MIN_NUM_ARGS:
            start()
        else:
            print(f'Unexpected usage with {num_args} args')
            output = get_help()
            print(output)
    except KeyboardInterrupt:
        print('')

if __name__ == "__main__":
    app = BotInternals()
    formatter = ResponseFormatter(app.config['repo_url'])
    main()
