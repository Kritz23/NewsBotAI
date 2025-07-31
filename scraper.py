import json
from collections import defaultdict, Counter
from newspaper import Article, build
from urllib.parse import urlparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 1. Define sources
AU_OUTLETS = {
    "7News": "https://7news.com.au",
    "ABC": "https://www.abc.net.au/news",
    "News.com.au": "https://www.news.com.au",
    "SBS": "https://www.sbs.com.au/news",
}

# 2. Define categories and match keywords
CATEGORIES = {
    "sports": ["sport", "football", "cricket", "tennis", "rugby", "afl"],
    "lifestyle": ["lifestyle", "health", "home", "beauty", "food", "travel"],
    "music": ["music", "concert", "album", "band", "artist"],
    "finance": ["finance", "money", "economy", "stock", "market", "business"],
}

TOPIC_LIMIT = 100
OUTPUT_FILE = "data/articles.json"

# Track article frequency by title
frequency_counter = Counter()

# Store final articles: topic -> list
output_by_topic = defaultdict(list)


def match_category(url: str) -> str:
    url_lower = url.lower()
    for category, keywords in CATEGORIES.items():
        if any(k in url_lower for k in keywords):
            return category
    return None


def is_valid_article(article_obj):
    url = article_obj.url.lower()
    bad_substrings = ["video", "ondemand", "collection", "watch", "/live"]
    return (
        all(b not in url for b in bad_substrings)
        and article_obj.text
        and len(article_obj.text.strip()) > 200
    )


def process_article(article_obj, source_name):
    try:
        article_obj.download()
        article_obj.parse()

        category = match_category(article_obj.url)
        if not category:
            return None

        if not is_valid_article(article_obj):
            return None

        title = article_obj.title.strip()
        if not title:
            return None

        frequency_counter[title] += 1

        return {
            "topic": category,
            "title": title,
            "author": ", ".join(article_obj.authors) if article_obj.authors else "Unknown",
            "source": source_name,
            "url": article_obj.url,
            "published": article_obj.publish_date.isoformat() if article_obj.publish_date else datetime.utcnow().isoformat(),
            "content": article_obj.text.strip(),
            "frequency": frequency_counter[title],
        }
    except Exception:
        return None


def run_news_pipeline():
    print("📰 Running news scraper...")
    seen_titles = set()

    with ThreadPoolExecutor(max_workers=6) as executor:
        for source_name, base_url in AU_OUTLETS.items():
            print(f"🔍 Scraping from {source_name}...")
            paper = build(base_url, memoize_articles=False)
            articles = paper.articles[:200]  # optional: limit how many we try per site

            futures = [executor.submit(process_article, art, source_name) for art in articles]

            domain_topic_counts = defaultdict(int)

            for future in futures:
                article = future.result()
                if article:
                    topic = article["topic"]

                    # Skip duplicates by title
                    if article["title"] in seen_titles:
                        continue

                    # Enforce per-domain topic limit
                    key = f"{source_name}:{topic}"
                    if domain_topic_counts[key] >= TOPIC_LIMIT:
                        continue

                    domain_topic_counts[key] += 1
                    seen_titles.add(article["title"])
                    output_by_topic[topic].append(article)

    # Save final JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_by_topic, f, indent=2, ensure_ascii=False)

    total = sum(len(v) for v in output_by_topic.values())
    print(f"✅ Saved {total} articles to {OUTPUT_FILE}")


if __name__ == "__main__":
    run_news_pipeline()
