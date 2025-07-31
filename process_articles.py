# process_articles.py

import json
from pathlib import Path
from tqdm import tqdm

from utils.classification import classify_article
from utils.summarizer import summarize_article
from utils.clustering import cluster_articles

INPUT_PATH = Path("data/articles.json")
OUTPUT_PATH = Path("data/articles_enriched.json")

VALID_TOPICS = {"sports", "lifestyle", "music", "finance"}

def load_articles():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}")
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Flatten structure from topic -> [articles] to a single list
    all_articles = []
    for topic, articles in data.items():
        for article in articles:
            # Ensure topic is included in article (in case it's missing)
            article["topic"] = topic
            all_articles.append(article)
    return all_articles

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

        # Classify topic if missing or invalid
        category = article.get("topic", "").lower()
        if category not in VALID_TOPICS:
            category = classify_article(text)
            article["topic"] = category

        # Summarize content
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
