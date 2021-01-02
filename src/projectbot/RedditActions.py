import praw
from projectbot.Constants import Error

class RedditInterface:
    def __init__(self):
        self.init_reddit_client()

    def init_reddit_client(self):
        ''' Initialize an instance of the PRAW reddit client using the assumed praw.ini in the same directory '''
        self.reddit = praw.Reddit()
        try:
            self.reddit.user.me()
        except:
            print('Failed to log into bot')
            exit(Error.LOGIN_FAILED)


    def send_comment_response(self, comment, response):
        new_comment = comment.reply(response)
        if new_comment == None:
            print('[Error]: Failed to post new comment')


    def send_submission_response(self, submission, response):
        new_comment = submission.reply(response)
        if new_comment == None:
            print("[Error]: Failed to post new comment")

    def query_subreddit(self, query):
        return self.reddit.subreddit(query)
