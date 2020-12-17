import os
import sys
import csv
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

asset_path = '../src/assets/'
file_ideas = asset_path + 'ideas.csv'
file_suggestions = asset_path + 'suggestion_words.txt'
file_rejections = asset_path + 'rejection_words.txt'

username = os.environ.get('MONGO_USERNAME')
password = os.environ.get('MONGO_PASSWORD')
dbname = os.environ.get('MONGO_DATABASE')
if None in [username, password, dbname]:
    print('Configuration failed')
    exit(1)

client = MongoClient(f'mongodb+srv://{username}:{password}@cluster0.5398r.mongodb.net/{dbname}?retryWrites=true&w=majority')

force = False

def load_to_mongo_db(ideas, suggestions, rejections):
    upload_suggestions(suggestions)
    upload_rejections(rejections)
    upload_ideas(ideas)

def load_ideas():
    ideas = []
    with open(file_ideas) as csvfile:
        reader = csv.reader(csvfile, delimiter=',', skipinitialspace=True)
        for index, row in enumerate(reader):
            if index == 0:
                continue
            ideas.append(row)
    return ideas

def load_suggestions():
    suggestion_words = []
    with open(file_suggestions, 'r') as reader:
        suggestion_words = reader.read().split()
    return suggestion_words

def load_rejections():
    rejection_words = []
    with open(file_rejections, 'r') as reader:
        rejection_words = reader.read().split()
    return rejection_words

def upload_suggestions(suggestions):
    collection_name = 'suggestion-words'
    database = client.get_database(dbname)
    table = database.get_collection(collection_name)

    # Check for docs in current table
    count = table.count_documents({})
    if count > 0 and not force:
        # If force arg not given, abort
        print(f'{count} docs already exist, will not update {collection_name} collection')
        return
    elif count > 0:
        # If force arg is given and docs exist, confirm with user
        result = input(f'Are you sure you want to delete the {count} docs in the {collection_name} collection? (y/N):')
        if result != 'y':
            if not (result == '' or result == 'n'):
                print('Unknown input, aborting update for', collection_name)
            return

    # Delete current database
    database.drop_collection(collection_name)

    # Load suggestions
    docs = []
    for term in suggestions:
        docs.append(
            {
                'term': term
            }
        )
    result = table.insert_many(docs)
    print('Uploaded:', len(result.inserted_ids), 'suggestions')

def upload_rejections(rejections):
    collection_name = 'rejection-words'
    database = client.get_database(dbname)
    table = database.get_collection(collection_name)

    # Check for docs in current table
    count = table.count_documents({})
    if count > 0 and not force:
        # If force arg not given, abort
        print(f'{count} docs already exist, will not update {collection_name} collection')
        return
    elif count > 0:
        # If force arg is given and docs exist, confirm with user
        result = input(f'Are you sure you want to delete the {count} docs in the {collection_name} collection? (y/N):')
        if result != 'y':
            if not (result == '' or result == 'n'):
                print('Unknown input, aborting update for', collection_name)
            return


    # Delete current database
    database.drop_collection(collection_name)

    # Load suggestions
    docs = []
    for term in rejections:
        docs.append(
            {
                'term': term
            }
        )
    result = table.insert_many(docs)
    print('Uploaded:', len(result.inserted_ids), 'rejections')

def upload_ideas(ideas):
    collection_name = 'ideas'
    database = client.get_database(dbname)
    table = database.get_collection(collection_name)

    # Check for docs in current table
    count = table.count_documents({})
    if count > 0 and not force:
        # If force arg not given, abort
        print(f'{count} docs already exist, will not update {collection_name} collection')
        return
    elif count > 0:
        # If force arg is given and docs exist, confirm with user
        result = input(f'Are you sure you want to delete the {count} docs in the {collection_name} collection? (y/N):')
        if result != 'y':
            if not (result == '' or result == 'n'):
                print('Unknown input, aborting update for', collection_name)
            return

    # Delete current database
    database.drop_collection(collection_name)

    # Load suggestions
    docs = []
    for idea in ideas:
        docs.append(
            {
                'name': idea[0],
                'difficulty': idea[1],
                'description': idea[2]
            }
        )
    result = table.insert_many(docs)
    print('Uploaded:', len(result.inserted_ids), 'ideas')

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--force':
            global force
            force = True

    ideas = load_ideas()
    suggestions = load_suggestions()
    rejections = load_rejections()

    load_to_mongo_db(ideas, suggestions, rejections)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        pass
