# prompts.py

CATEGORY_PROMPT = """
You are an expert journalist. Given the following news article content, classify it into one of:
1. sports
2. lifestyle
3. music
4. finance

Article:
"{article_text}"

Respond with only the category name.
"""

SUMMARY_PROMPT = """
You are a summarization assistant. Summarize the following news article clearly in 2-3 sentences. Do not include any introductory phrases like "Here is a summary" or "This article is about." Only return the summary content itself.

Article:
"{article_text}"

Summary:
"""
