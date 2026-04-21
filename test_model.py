import os, importlib
from dotenv import load_dotenv
load_dotenv(override=True)
genai = importlib.import_module("google.genai")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
print("Testing gemma-3-12b-it")
try:
    response = client.models.generate_content(model="gemma-3-12b-it", contents="hello")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
