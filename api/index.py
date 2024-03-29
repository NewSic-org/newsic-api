from flask import Flask, request, jsonify
import os
from flask_cors import CORS
from pymongo import MongoClient
from pinecone import Pinecone
from openai import OpenAI
import requests
# import pathlib
# from dotenv import load_dotenv

# env_path = pathlib.Path('..') / '.local.env'
# load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
CORS(app)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MONGO_DB_URI = os.getenv('MONGO_DB_URI')
pinecone_key = os.getenv('PINECONE_DB')


client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key = pinecone_key)
index = pc.Index("newsic")
client_db = MongoClient(MONGO_DB_URI)
db = client_db.get_database('newsic')
records = db.articles

@app.before_request
def check_token():
    if request.method == 'OPTIONS':
        return handle_preflight()
    authorization_header = request.headers.get('Authorization')
    if not authorization_header:
        return jsonify({'error': 'Missing Authorization header'}), 401

    token = authorization_header.split('Bearer ')[-1].strip()

    if not verify_google_oauth_token(token):
        return jsonify({'error': 'Invalid Google OAuth token'}), 401


def verify_google_oauth_token(token):
    google_response = requests.get(f'https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={token}')
    if google_response.status_code == 200:
        return True
    else:
        return False

def handle_preflight():
    response = jsonify({'message': 'Preflight request accepted'})
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
    return response

@app.route('/api/data', methods=['GET'])
def get_data():
    articles = db.articles.find({}, {"_id": 0})
    articles_list = list(articles)
    response = jsonify({'response': articles_list})
    response.headers['Content-Type'] = 'application/json'
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

@app.route('/regenerate', methods=['POST'])
def regenerate():
    data = request.get_json()
    summary = data.get('summary', '')
    title = data.get('title', '')
    regenerate = regenerate_content(summary, title)
    return regenerate

def regenerate_content(summary, title):
    response = client.chat.completions.create(
    model="ft:gpt-3.5-turbo-1106:personal::8eovJ1Vq",
    messages=[
        {"role": "system", "content": "You are a Bollywood lyricist and will generate Bollywood songs lyrics and title based on the user input, which is news content of an article. The song lyrics need to be mostly in Hindi and might include English in between. Do not include the translation to these lyrics."},
        {"role": "user", "content": f"{summary}"}
    ],
    temperature=1,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )
    content = response.choices[0].message.content
    song_title_start = content.find("Song Title: '") + len("Song Title: '")
    song_title_end = content.find("'", song_title_start)
    song_title = content[song_title_start:song_title_end]
    records.update_one(
            {'art_title': title},
            {
                '$set': {
                    'song': content,
                    'song_title': song_title
                }
            }
        )
    return jsonify({'title': song_title, 'generatedContent': content})
  

# @app.after_request
# def cors_headers(response):
#     response.headers["Access-Control-Allow-Origin"] = "*"
#     return response



if __name__ == '__main__':
    app.run()
