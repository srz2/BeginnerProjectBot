import utility as util
import praw 

def prompt_for_confirmation():
    option = input('Would you like to continue (Y/n/p):').lower()
    if option == 'y' or option == '':
        print('\n\n\n\n\n\n\n\n\n')
        print(f'[{time.time()}]: Waiting for more posts...')
    elif option == 'p':
        return option
    else:
        exit(1)

def reddit_send_submission_response(submission, response):
    new_comment = submission.reply(response)
    if new_comment == None:
        print("[Error]: Failed to post new comment")

def reply_submission_with_idea(submission, idea,simulate):
    ''' Reply with the idea to given reddit submission (post) '''
    print('Responding to post with idea:', idea[0])
    response = util.format_idea_response(idea)
    try:
        if simulate['sim']:
            print('Would be output:\n', response)
            if simulate['sim-confirm']:
                option = prompt_for_confirmation()
                if option == 'p':
                    reddit_send_submission_response(submission, response)
        else:
            reddit_send_submission_response(submission, response)
        return True
    except praw.exceptions.RedditAPIException as e:
        print(e)
        return False

def respond_with_basic_response(submission,simulate,config):
    ''' Reply with the basic response to give resources to a user'''
    print('Responding with basic response')
    response = format_basic_response(config)
    try:
        if simulate['sim']:
            print('Would be output:\n', response)
            if simulate['sim-confirm']:
                option = prompt_for_confirmation()
                if option == 'p':
                    reddit_send_submission_response(submission, response)
        else:
            reddit_send_submission_response(submission, response)
        return True
    except praw.exceptions.RedditAPIException as e:
        print(e)
        return False

def reddit_send_comment_response(comment, response):
    new_comment = comment.reply(response)
    if new_comment == None:
        print('[Error]: Failed to post new comment')

def reply_comment_with_idea(comment, idea,simulate):
    ''' Reply with the idea to given reddit comment '''
    print(f'Responding to comment({comment.permalink}) with idea:', idea[0])
    response = util.format_idea_response(idea)
    try:
        if simulate['sim']:
            print('Would be output:\n', response)
            if simulate['sim-confirm']:
                option = prompt_for_confirmation()
                if option == 'p':
                    reddit_send_comment_response(comment, response)
        else:
            reddit_send_comment_response(comment, response)
        return True
    except praw.exceptions.RedditAPIException as e:
        print(e)
        return False

def get_random(ideas, desired_difficulty='all'):
    '''
    Get a random idea from the list

    Argument:
        ideas (list<csvrow>): The list of ideas parsed from database
        desired_difficulty (string): The default difficulty. Defaults to all.

    Returns:
        idea (csvrow): A random idea
    '''
    if util.is_recognized_difficulty(desired_difficulty):
        tmp_ideas = ideas[desired_difficulty]
    else:
        tmp_ideas = ideas['all']

    num = random.randrange(0, len(tmp_ideas))
    return tmp_ideas[num]

def get_idea_and_respond_comment(comment,initialized,difficulty='all'):
    ''' Randomly get an idea and reply to the submission with it '''
    idea = get_random(initialized['ideas'], difficulty)
    success = reply_comment_with_idea(comment, idea,initialized['simulate'])
    return success

def get_idea_and_respond_submission(submission, initialized,difficulty='all'):
    ''' Randomly get an idea and reply to the submission with it '''
    idea = get_random(initialized['ideas'], difficulty)
    success = reply_submission_with_idea(submission, idea,initialized['simulate'])
    return success