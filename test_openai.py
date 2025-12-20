
import openai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
print(f"Loaded Key: {api_key[:10]}...{api_key[-5:] if api_key else 'None'}")

if not api_key:
    print("❌ No API Key found in .env")
    exit()

client = openai.OpenAI(api_key=api_key)

try:
    print("Sending test request to OpenAI...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Say 'It works!'"}
        ],
        max_tokens=10
    )
    print(f"✅ Success! Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Error: {e}")
