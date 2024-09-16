import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# init client and connect to localhost server
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="http://localhost:5001",  # change the default port if needed
)

# call API
chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Say this is a test",
        }
    ],
    model="Meta-Llama-3.1-8B-Instruct",
)

# print the top "choice"
if chat_completion.choices:
    print(chat_completion.choices[0].message.content)
else:
    print("Error: No completion returned")
