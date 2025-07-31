# classification.py

import os
from groq import Groq
from prompts import CATEGORY_PROMPT

# Set your GROQ_API_KEY in the .env file
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def classify_article(article_text: str) -> str:
    prompt = CATEGORY_PROMPT.format(article_text=article_text[:1500])  # Truncate to avoid token overload
    try:
        response = openai.ChatCompletion.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",  # Fast and capable model on Groq
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        category = response.choices[0].message.content.lower().strip()
        return category if category in {"sports", "lifestyle", "music", "finance"} else "unknown"
    except Exception as e:
        print(f"[ERROR] Classification failed: {e}")
        return "unknown"
