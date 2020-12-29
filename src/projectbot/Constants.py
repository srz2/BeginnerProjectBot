class Asset:
    file_praw_ini = 'praw.ini'

    file_ideas_csv = 'assets/ideas.csv'
    coll_ideas_mongo = 'ideas'

    file_rejection_words = 'assets/rejection_words.txt'
    coll_rejection_mongo = 'rejection-words'

    file_suggestion_words = 'assets/suggestion_words.txt'
    coll_suggestion_mongo = 'suggestion-words'

class Error:
    GENERAL = 1
    FILE_MISSING = 2
    LOGIN_FAILED = 3
    FILE_UPDATE = 4
    USER_QUIT = 5

class Const:
    MIN_NUM_ARGS = 1
    MIN_NUM_WORDS_IN_TITLE = 5
    ACCEPTABLE_RATIO = 0.25
    RATE_LIMIT_SLEEP_TIME = 600    # 10 minutes

    DEFAULT_APP_LEVEL = 'staging'

    SUBREDDITS_TO_SCAN_PROD = ['learnpython']
    SUBREDDITS_TO_SCAN_STAG = ['SRZ2_TestEnvironment']
