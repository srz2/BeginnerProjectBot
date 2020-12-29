import praw

def reddit_send_comment_response(comment, response):
    new_comment = comment.reply(response)
    if new_comment == None:
        print('[Error]: Failed to post new comment')


def reddit_send_submission_response(submission, response):
    new_comment = submission.reply(response)
    if new_comment == None:
        print("[Error]: Failed to post new comment")
