# clustering.py

from sentence_transformers import SentenceTransformer, util
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")  # Lightweight, fast, accurate

def embed_articles(articles):
    return model.encode([a["content"] for a in articles], convert_to_tensor=True)

def cluster_articles(articles, similarity_threshold=0.82):
    embeddings = embed_articles(articles)
    clusters = []
    assigned = set()

    for i, emb in enumerate(embeddings):
        if i in assigned:
            continue
        cluster = [i]
        for j in range(i + 1, len(embeddings)):
            if j in assigned:
                continue
            sim = float(util.cos_sim(emb, embeddings[j]))
            if sim >= similarity_threshold:
                cluster.append(j)
                assigned.add(j)
        clusters.append(cluster)
        assigned.update(cluster)

    # Assign cluster ID to each article
    for cluster_id, article_indices in enumerate(clusters):
        for idx in article_indices:
            articles[idx]["cluster_id"] = cluster_id

    return articles
