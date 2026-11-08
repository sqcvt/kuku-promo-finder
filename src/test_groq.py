
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

model = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": "Reply with exactly: Groq connection successful."
        }
    ],
    max_completion_tokens=100
)

print(response.choices[0].message.content)

print("Model:", model)
print("Groq API connection successful!")
