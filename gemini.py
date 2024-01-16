import os
import pathlib
import textwrap
from IPython.display import display, Markdown
from dotenv import load_dotenv  
import google.generativeai as genai


env_path = pathlib.Path('.') / '.local.env'
load_dotenv(dotenv_path=env_path)

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# Configure the generativeai library with the API key
genai.configure(api_key=GOOGLE_API_KEY)

print(GOOGLE_API_KEY)

def to_markdown(text):
    text = text.replace('•', '  *')
    return Markdown(textwrap.indent(text, '>', predicate=lambda _: True))


for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)

model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("What is the meaning of life?")
# display(to_markdown(response.text))

print(response.text)
