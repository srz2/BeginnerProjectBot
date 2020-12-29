from pymongo import MongoClient

class Database:
    def __init__(self, username, password, dbname):
        self.username = username
        self.password = password
        self.dbname = dbname
    
    def get_docs_from_collection(self, list_name):
        ''' Get the doc collection from a collection '''

        client = MongoClient(f'mongodb+srv://{self.username}:{self.password}@cluster0.5398r.mongodb.net/{self.dbname}?retryWrites=true&w=majority')
        database = client.get_database(self.dbname)
        collection = database.get_collection(list_name)

        docs = collection.find({})
        return docs
    
    def get_list_from_collection(self, list_name):
        ''' Get a list of terms from a collection '''
        all = []
        docs = self.get_docs_from_collection(list_name)
        for doc in docs:
            all.append(doc['term'])

        return all
