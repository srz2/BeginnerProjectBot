import praw
import response as resp
import utility as util

RATE_LIMIT_SLEEP_TIME = 600    # 10 minutes
ACCEPTABLE_RATIO = 0.25
MIN_NUM_WORDS_IN_TITLE = 5

def process_title(title,reject_words,suggest_words):
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
        if word in reject_words:
            errors.append(f'Rejecting ({word}): {title}')
        if word in suggest_words:
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

def submission_contains_bot_response(submission,config):
    ''' Determine if the submission contains the bot post already '''

    username = config['DEFAULT']['username']

    for comment in submission.comments:
        if comment.author == username:
            return True
    return False

def submission_has_project_request(submission,initialized):
    ''' Determine if the given submission is requesting help for a new project '''

    has_project_request = False

    # Confirm bot has not commented on post before
    contains_bot_already = submission_contains_bot_response(submission,initialized['config'])
    if contains_bot_already:
        return has_project_request

    # Process the post's title to check if it pass criteria for project request
    ratio, count, total_words, error = process_title(submission.title,initialized['rejection_words'],initialized['query_words'])
    print('Id:', submission.id)
    output_stats(submission.title, count, total_words, ratio, error)
    if error == '':
        # print(f'Accepting:', submission.title)
        has_project_request = True
    else:
        # print(f'Rejecting:', error)
        has_project_request = False

    return has_project_request

def comment_already_has_bot_response(comment,config):
    ''' Determine if comment already contains the bot''s response'''

    username = config['DEFAULT']['username']

    # This is potentially intensive if calling for every comment
    # Inititally the replies list is empty unless this is called
    comment.refresh()

    for inner_comment in comment.replies:
        if inner_comment.author == username:
            return True
    return False

def process_comment(content,config):
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
            if not util.is_recognized_difficulty(difficulty):
                difficulty = 'all'
            return True, difficulty

    return False, ''

def comment_is_made_by_bot(comment,config):
    ''' Determine if the comment is the bot itself '''

    username = config['DEFAULT']['username']
    if comment.author == username:
        return True

    return False

def comment_has_project_request(comment,config):
    ''' Determine if the given comment is requesting help for a new project '''

    has_project_request = False

    # Confirm we are aren't processing a comment from the bot
    is_from_bot = comment_is_made_by_bot(comment,config)
    if is_from_bot:
        return has_project_request, ''

    has_project_request, difficulty = process_comment(comment.body,config)
    if has_project_request:
        # Confirm bot hasn't already responded to this comment already
        # This is after the process_comment() because it can be intensive
        # on every comment
        bot_already_responded = comment_already_has_bot_response(comment,config)
        if bot_already_responded:
            # Override the request
            has_project_request = False
            return has_project_request, ''
    
    return has_project_request, difficulty

def stream_subreddits(initialized):
    ''' Blocking method to continuously check all 'subreddits_to_scan' for new posts '''
    query = '+'.join(initialized['subreddits'])
    print('Post Query:', query, '\n\n----------------')
    subreddits = initialized['reddit'].subreddit(query)
    for submission in subreddits.stream.submissions():
        project_requested = submission_has_project_request(submission,initialized)
        if project_requested:
            success = resp.respond_with_basic_response(submission,initialized['simulate'],initialized['config'])
            if not success:
                print('Failed to respond to post, trying again in', RATE_LIMIT_SLEEP_TIME, 'seconds')
                time.sleep(RATE_LIMIT_SLEEP_TIME + 5)
                resp.respond_with_basic_response(submission,initialized['simulate'],initialized['config'])

def stream_subreddits_comments(initialized):
    ''' Blocking method to continuously check all 'subreddits_to_scan' for new comments '''
    query = '+'.join(initialized['subreddits'])
    print('Comment Query:', query, '\n\n----------------')
    subreddits = initialized['reddit'].subreddit(query)
    for comment in subreddits.stream.comments():
        project_requested, difficulty = comment_has_project_request(comment,initialized['config'])
        if project_requested:
            success = resp.get_idea_and_respond_comment(comment,initialized,difficulty)
            if not success:
                print('Failed to respond to comment, trying again in', RATE_LIMIT_SLEEP_TIME, 'seconds')
                time.sleep(RATE_LIMIT_SLEEP_TIME + 5)
                resp.get_idea_and_respond_comment(comment,initialized,difficulty)