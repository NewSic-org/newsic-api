import pathlib
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import os
from flask_cors import CORS
from pymongo import MongoClient
from pinecone import Pinecone
from openai import OpenAI

app = Flask(__name__)
CORS(app)

env_path = pathlib.Path('..') / '.local.env'
load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MONGO_DB_URI = os.getenv('MONGO_DB_URI')
pinecone_key = os.getenv('PINECONE_DB')


client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key = pinecone_key)
index = pc.Index("newsic")
client_db = MongoClient(MONGO_DB_URI)
db = client_db.get_database('newsic')
records = db.articles

@app.route('/api/data', methods=['GET'])
def get_data():
    articles = db.articles.find({}, {"_id": 0})
    articles_list = list(articles)
    response = jsonify(response=articles_list)
    return response

@app.route('/api/data/headlines' ,methods=['GET'])
def headlines():
    headlines = db.articles.find({}, {"art_title": 1, "_id": 0})
    headlines_list = [article["art_title"] for article in headlines]
    return jsonify(response=headlines_list)

@app.route("/", methods=['GET'])
def home():
    return jsonify(message="Welcome to Newsic")

@app.route('/semantic-search', methods=['POST'])
def semantic_search():
    data = request.get_json()
    search = data.get('search', '')

    response2 = client.embeddings.create(
      input = search,
      model = "text-embedding-ada-002"
  )

    doc = index.query(
        vector=response2.data[0].embedding,
        top_k = 3
  )
    ids = [match['id'] for match in doc['matches']]
    # print(ids)

    articles = []
    for title in ids:
        article = records.find_one({'art_title': title}, {'_id': 0})
        if article:
            articles.append(article)
    return jsonify(response=articles)

@app.after_request
def cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

if __name__ == '__main__':
    app.run()
