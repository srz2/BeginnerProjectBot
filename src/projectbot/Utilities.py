import os
import sys
import configparser
from Constants import Asset


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
