import os
import shutil
import csv
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

username = os.environ.get('MONGO_USERNAME')
password = os.environ.get('MONGO_PASSWORD')
dbname = os.environ.get('MONGO_DATABASE_NAME')
if None in [username, password, dbname]:
    print('Configuration failed')
    exit(1)

client = MongoClient(f'mongodb+srv://{username}:{password}@cluster0.5398r.mongodb.net/{dbname}?retryWrites=true&w=majority')

def get_docs_from_collection(list_name):
    database = client.get_database(dbname)
    collection = database.get_collection(list_name)

    docs = collection.find({})
    return docs

def get_list_from_collection(list_name):
    all = []
    docs = get_docs_from_collection(list_name)
    for doc in docs:
        all.append(doc['term'])

    return all

def create_assets(ideas, suggestions, rejections):
    # Create asset directory
    dest = 'assets'
    if os.path.exists(dest):
        shutil.rmtree(dest, ignore_errors=True)
    os.mkdir('assets')

    # Write Suggestions
    with open(os.path.join(dest, 'suggestions_words.txt'), 'w') as file:
        file.writelines(suggestion + '\n' for suggestion in suggestions)
    # Write Rejections
    with open(os.path.join(dest, 'rejection_words.txt'), 'w') as file:
        file.writelines(rejection + '\n' for rejection in rejections)
    # Write Ideas
    with open(os.path.join(dest, 'ideas.csv'), 'w', newline='') as file:
        writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(['Idea', 'difficulty', 'description'])
        for idea in ideas:
            name = idea['name']
            diff = idea['difficulty']
            desc = idea['description']
            writer.writerow([name, diff, desc])

def main():
    ideas = get_docs_from_collection('ideas')
    suggestions = get_list_from_collection('suggestion-words')
    rejections = get_list_from_collection('rejection-words')

    create_assets(ideas, suggestions, rejections)

if __name__ == "__main__":
    main()
