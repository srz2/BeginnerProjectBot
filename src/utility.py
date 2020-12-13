import os 
import sys

ERROR_GENERAL = 1
ERROR_FILE_MISSING = 2
ERROR_LOGIN_FAILED = 3

def check_file_exists(path, error_msg):
    ''' Check if file exists, if not then quit application '''
    if not os.path.exists(path):
        print(error_msg)
        sys.exit(ERROR_FILE_MISSING)

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

def is_recognized_difficulty(dif):
    dif = dif.lower()
    if dif == 'easy' or dif == 'medium' or dif == 'hard' or dif == 'all':
        return True
    else:
        return False

def get_bot_reference_text(config):
    ''' Format the text response for bot disclaimer '''

    repo_url = config['DEFAULT']['repo_url']

    response = ''
    response += f'^(I am a bot, so give praises if I was helpful or curses if I was not.)\n'
    response += f'^(Want a project? Comment with "!projectbot" and optionally add easy, medium, or hard to request a difficulty!)\n'
    response += f'^(If you want to understand me more, my code is on) ^[Github]({repo_url})'

    return response

def format_basic_response(config):
    ''' Return the formatted text to post to reddit to direct a user to some project resources '''

    response = ''
    response += f'Hey, I think you are trying to figure out a project to do; Here are some helpful resources:\n\n'
    response += create_link_reference('/r/learnpython - Wiki', 'https://www.reddit.com/r/learnpython/wiki/index#wiki_flex_your_coding_skill.21')
    response += create_link_reference('Five mini projects', 'https://knightlab.northwestern.edu/2014/06/05/five-mini-programming-projects-for-the-python-beginner/')
    response += create_link_reference('Automate the Boring Stuff with Python', 'https://automatetheboringstuff.com/')
    response += create_link_reference('RealPython - Projects', 'https://realpython.com/tutorials/projects/')
    response += '\n'
    response += get_bot_reference_text(config)

    return response

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
        difficulty = 'fascinating'

    response = ''
    response += f'Hey, I think you are trying to figure out a project to do; how about this one?\n\n'
    response += f'Project: **{raw_project_name}** \n\n'
    response += f'I think it''s a _' + difficulty + '_ project for you! Try it out but, dont get discouraged. If you need more guidance, here\'s a description:\n'
    response += f'>{raw_description}\n\n\n'
    response += get_bot_reference_text()
    
    return response