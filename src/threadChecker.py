import threading
import stream as Stream

class ThreadPostChecker(threading.Thread):
    ''' This thread will check the posts on all queried subreddits '''
    def __init__(self, name, initialized):
        threading.Thread.__init__(self)
        self.name = name
        self.initialized = initialized

    def run(self):
        threading.Thread.run(self)
        Stream.stream_subreddits(self.initialized)

class ThreadCommentChecker(threading.Thread):
    ''' This thread will check the comments on all queried subreddits '''
    def __init__(self, name, reddit):
        threading.Thread.__init__(self)
        self.name = name
        self.initialized = initialized

    def run(self):
        threading.Thread.run(self)
        Stream.stream_subreddits_comments(self.initialized)