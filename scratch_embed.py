import os
import importlib
from dotenv import load_dotenv

load_dotenv(override=True)
genai = importlib.import_module("google.genai")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
texts = ["hello", "world"]
response = client.models.embed_content(model="gemini-embedding-2-preview", contents=texts)
print(f"Num embeddings: {len(response.embeddings)}")
