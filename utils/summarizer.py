# summarizer.py

import os
from groq import Groq
from prompts import SUMMARY_PROMPT

# Set your GROQ_API_KEY in the .env file
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def summarize_article(article_text: str) -> str:
    prompt = SUMMARY_PROMPT.format(article_text=article_text[:1500])

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",  # Fast and capable model on Groq
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] Groq summarization failed: {e}")
        return ""
