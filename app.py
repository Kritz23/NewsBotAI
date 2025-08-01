# app.py

import streamlit as st
from scraper import NewsScraperPipeline
from highlights import get_highlights
from process_articles import main as process_articles_main
from chatbot import build_vector_db
import chatbot

st.set_page_config(page_title="Daily News Highlights", layout="wide")

st.title("📰 AI-Powered Daily News Highlights")

# --- Sidebar Controls ---
st.sidebar.header("🔍 Filter News")
category = st.sidebar.selectbox("Select Category", ["sports", "lifestyle", "music", "finance"])

st.sidebar.header("🧠 Run Pipelines")

# Run Step 1: Scraper
if st.sidebar.button("🔁 Run Scraper"):
    with st.spinner("Scraping news..."):
        scraper = NewsScraperPipeline()
        raw_articles = scraper.run_pipeline()
        filtered_articles = scraper.filter_articles(raw_articles)
        scraper.save_articles(filtered_articles)
        st.success("✅ Scraper complete. Articles saved.")
        st.markdown(f"- **Total Articles Scraped:** {len(raw_articles)}")
        st.markdown(f"- **After Filtering:** {len(filtered_articles)}")

# Run Step 2: Process articles
if st.sidebar.button("⚙️ Process Articles"):
    with st.spinner("Classifying, summarizing, clustering and storing in DB..."):
        process_articles_main()
        build_vector_db(force=True)
        st.success("✅ Article processing complete. Chatbot memory updated.")

# --- Load Highlights ---
highlights = get_highlights(category)

# --- Show Highlights ---
st.subheader(f"Top News in {category.title()}")

if not highlights:
    st.warning("No highlights available.")
else:
    for i, item in enumerate(highlights, 1):
        with st.expander(f"#{i}. {item['title']}", expanded=True):
            clean_summary = item['summary'].replace("Here is a 2-3 sentence summary of the news article:", "").strip()
            st.markdown(f"**📝 Summary:** {clean_summary}")
            st.markdown(f"**👤 Author:** {item.get('author', 'N/A')} | **🗓️ Date:** {item.get('published_date', 'N/A')}")
            st.markdown(f"**📡 Sources ({item['frequency']}):**")
            for url in item["source_urls"]:
                st.markdown(f"- [🔗 Source]({url})")

st.divider()
st.subheader("💬 Ask a Question About Today's News")

with st.spinner("Initializing chatbot..."):
    chatbot.build_vector_db()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_query = st.text_input("Ask anything about today's news", key="user_input")
if st.button("Ask"):
    if user_query:
        with st.spinner("Generating response..."):
            response = chatbot.ask_question(user_query)
            st.session_state.chat_history.append((user_query, response))

# Display history
for q, a in reversed(st.session_state.chat_history):
    st.markdown(f"**🧠 You:** {q}")
    st.markdown(f"**🤖 Chatbot:** {a}")
    st.markdown("---")
