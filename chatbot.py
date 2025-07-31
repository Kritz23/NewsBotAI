# chatbot.py

import os
import json
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from groq import Groq
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load from .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

DATA_PATH = Path("data/articles_enriched.json")
CHROMA_PATH = "vector_store"
COLLECTION_NAME = "news_summaries"

embedding_function = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_function
)

def build_vector_db(force=False):
    if not force and len(collection.get()['ids']) > 0:
        print("✅ Vector DB already exists.")
        return

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        articles = json.load(f)

    docs, ids, metadata = [], [], []
    for idx, article in enumerate(articles):
        if not article.get("summary"):
            continue
        ids.append(str(idx))
        docs.append(article["summary"])
        metadata.append({
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "topic": article.get("topic", "")
        })

    collection.add(documents=docs, ids=ids, metadatas=metadata)
    print(f"✅ Added {len(ids)} summaries to ChromaDB.")

def ask_question(query: str, k: int = 5) -> str:
    results = collection.query(query_texts=[query], n_results=k)
    context_blocks = results['documents'][0]

    prompt = f"""
You are a news assistant. Based on the following summaries, answer the user’s question.

Summaries:
{chr(10).join(f"- {c}" for c in context_blocks)}

Question: {query}
Answer:
    """.strip()

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[ERROR] Failed to generate answer: {e}"
