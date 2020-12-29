import os
import sys
import time
import configparser
from Constants import Asset, Error

class ResponseFormatter:
    def __init__(self, repo_url):
        self.repo_url = repo_url

    def get_bot_reference_text(self):
        ''' Format the text response for bot disclaimer '''

        response = ''
        response += f'^(I am a bot, so give praises if I was helpful or curses if I was not.)\n'
        response += f'^(Want a project? Comment with "!projectbot" and optionally add easy, medium, or hard to request a difficulty!)\n'
        response += f'^(If you want to understand me more, my code is on) ^[Github]({self.repo_url})'

        return response

    def create_link_reference(self, text, url):
        '''
            Create a link for reddit for response

            Argument:
                - text (string): The shown text for the link
                - url (string): The destination URL for the link

            Returns:
                A link to put in the markdown response to a user
        '''

        return f'- [{text}]({url})\n'

    def format_idea_response(self, idea):
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
        response += self.get_bot_reference_text()

        return response

    def format_basic_response(self):
        ''' Return the formatted text to post to reddit to direct a user to some project resources '''

        response = ''
        response += f'Hey, I think you are trying to figure out a project to do; Here are some helpful resources:\n\n'
        response += self.create_link_reference('/r/learnpython - Wiki', 'https://www.reddit.com/r/learnpython/wiki/index#wiki_flex_your_coding_skill.21')
        response += self.create_link_reference('Five mini projects', 'https://knightlab.northwestern.edu/2014/06/05/five-mini-programming-projects-for-the-python-beginner/')
        response += self.create_link_reference('Automate the Boring Stuff with Python', 'https://automatetheboringstuff.com/')
        response += self.create_link_reference('RealPython - Projects', 'https://realpython.com/tutorials/projects/')
        response += '\n'
        response += self.get_bot_reference_text()

        return response


def output_stats(title, count, total, ratio, error_msg):
    ''' DEBUG: Used for outputting information '''
    if error_msg == '':
        status = 'Accepted'
    else:
        status = 'Rejected'

    print(f'Title: {title}\nCount: {count}\nLenth: {total}\nRatio: {ratio}\nStatus: {status}\nError Message: {error_msg}\n-------------')


def get_help():
    ''' Get the help string for showing usage '''

    output = ''
    output += f'Usage: python3 bot.py [action] <args...>\n'
    output += f'    action: All possible actions which can be added to bot\n'
    output += f'        run: Run the default application of the bot\n'
    output += f'        test: Test a specific phrase to determine how the bot interprets it. It does not run the main application\n'
    output += f'            phrase: Add this following the test action\n'
    output += f'        sim: Set the bot to simulation mode where it does not post to reddit\n'
    output += f'            confirm: Add this following the test action\n'
    output += f'        help: Show help/usage output\n'

    return output


def check_file_exists(path, error_msg):
    ''' 
    Check if file exists, if not then print message

    Parameters:
        path (string): Path to a file/folder
        error_msg (string): Error message to display if file/dir doesnt exist
    
    Returns:
        exists (boolean): File/dir does exist
    '''
    if not os.path.exists(path):
        print(error_msg)
        return False
    else:
        return True


def create_user_agent():
    ''' Create the user agent string '''

    temp_config = configparser.ConfigParser()
    temp_config.read(Asset.file_praw_ini)

    c = temp_config['DEFAULT']
    username = c['username']
    version = c['version']
    author = c['author']
    user_agent = f'{username}:{version} (by {author})'
    return user_agent


def is_recongized_difficulty(dif):
    if dif is None:
        return False

    dif = dif.lower()
    if dif in ['easy', 'medium', 'hard', 'all']:
        return True
    else:
        return False


def prompt_for_confirmation():
    option = input('Would you like to continue (Y/n/p):').lower()
    if option == 'y' or option == '':
        print('\n\n\n\n\n\n\n\n\n')
        print(f'[{time.time()}]: Waiting for more posts...')
    elif option == 'p':
        return option
    else:
        exit(Error.USER_QUIT)
