from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
api_token = os.getenv("OPENAPI_TOKEN")
client = OpenAI(api_key=api_token)

def generate(description, song_count):
    context = "Please create a playlist containing " + str(song_count) + " songs that is based on the following description: " + description
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "developer", "content": "You are a helpful assistant curating playlists "
                                             "based on user descriptions and it needs to be passed a python array. "
                                             "Do not include anything other than an array of the songs"},
            {
                "role": "user",
                "content": context
            }
        ]
    )
    text = completion.choices[0].message.split()
    print(text)
    return text


