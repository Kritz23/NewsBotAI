# process_articles.py

import json
from pathlib import Path
from tqdm import tqdm

from utils.classification import classify_article
from utils.summarizer import summarize_article
from utils.clustering import cluster_articles

INPUT_PATH = Path("data/articles.json")
OUTPUT_PATH = Path("data/articles_enriched.json")

def load_articles():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_articles(articles):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Enriched articles saved to: {OUTPUT_PATH}")

def enrich_articles(articles):
    enriched = []
    print(f"\n📦 Processing {len(articles)} articles...\n")
    for article in tqdm(articles, desc="Enriching"):
        text = article.get("content", "")

        # Add category if not already present or invalid
        category = article.get("topic", "").lower()
        if category not in {"sports", "lifestyle", "music", "finance"}:
            category = classify_article(text)
            article["topic"] = category

        # Summarize
        article["summary"] = summarize_article(text)

        enriched.append(article)
    return enriched

def main():
    articles = load_articles()
    enriched_articles = enrich_articles(articles)
    clustered_articles = cluster_articles(enriched_articles)
    save_articles(clustered_articles)

if __name__ == "__main__":
    main()