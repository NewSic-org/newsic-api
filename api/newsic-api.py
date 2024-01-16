import pathlib
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import os
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

env_path = pathlib.Path('..') / '.local.env'
load_dotenv(dotenv_path=env_path)
MONGO_DB_URI = os.getenv('MONGO_DB_URI')

client_db = MongoClient(MONGO_DB_URI)
db = client_db.get_database('newsic')
records = db.articles

@app.route('/api/data', methods=['GET'])
def get_data():
    articles = db.articles.find({}, {"_id": 0})
    articles_list = list(articles)
    return jsonify(articles_list)

@app.route('/api/data/headlines' ,methods=['GET'])
def headlines():
    headlines = db.articles.find({}, {"art_title": 1, "_id": 0})
    headlines_list = [article["art_title"] for article in headlines]
    return jsonify({"headlines": headlines_list})

@app.route("/", methods=['GET'])
def home():
    return "Connection Succesful"

if __name__ == '__main__':
    app.run()