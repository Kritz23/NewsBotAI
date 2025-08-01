# highlights.py

import json
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Dict

DATA_PATH = Path("data/articles_enriched.json")

# You can expand this set
KEYWORDS = {
    "breaking": 3,
    "update": 2,
    "exclusive": 2,
    "alert": 2,
    "warning": 1,
    "major": 1,
    "emergency": 1,
    "highlights": 1,
}

def load_articles():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"File not found: {DATA_PATH}")
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def keyword_score(text: str) -> int:
    text = text.lower()
    score = 0
    for word, weight in KEYWORDS.items():
        if re.search(rf"\b{re.escape(word)}\b", text):
            score += weight
    return score

def get_highlights(category: str, top_k: int = 5) -> List[Dict]:
    articles = load_articles()
    filtered = [a for a in articles if a.get("topic") == category]

    # Group by cluster
    cluster_articles = defaultdict(list)
    for article in filtered:
        cluster_id = article.get("cluster_id", -1)
        cluster_articles[cluster_id].append(article)

    highlights = []
    for cluster_id, articles in cluster_articles.items():
        cluster_size = len(articles)

        # Representative article = longest summary
        representative = max(articles, key=lambda x: len(x.get("summary", "")))

        score = keyword_score(representative["title"]) + cluster_size
        highlights.append({
            "cluster_id": cluster_id,
            "score": score,
            "frequency": representative["source"],
            "title": representative["title"],
            "summary": representative["summary"].replace("Here is a 2-3 sentence summary of the news article:", "").strip(),
            "source_urls": [a["url"] for a in articles],
            "author": representative.get("author"),
            "published_date": representative.get("published")[:10] ,
        })

    # Sort by score descending
    highlights.sort(key=lambda x: x["score"], reverse=True)
    return highlights[:top_k]
