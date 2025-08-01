# 📰 AI-Powered News Aggregator & Chatbot

This is an AI-powered system that scrapes Australian news across **sports**, **lifestyle**, **music**, and **finance**, clusters similar articles, summarizes them, and ranks key daily highlights. A built-in chatbot allows users to ask questions about the news using **Retrieval-Augmented Generation (RAG)**.

---

## 🚀 Features

Multi-domain `.au` news scraping  
LLM-based classification & summarization (Groq)  
Duplicate detection with semantic clustering  
Keyword and frequency-based highlight ranking  
Interactive Streamlit dashboard  
Chatbot with RAG using ChromaDB and Groq (Llama 4)

---

## 📦 Project Structure

NewsBotAI/ <br/>
├── app.py # Streamlit UI <br/>
├── scraper.py # Extracts articles <br/>
├── process_articles.py # Classification, summarization, clustering <br/>
├── highlights.py # Highlight ranking logic <br/>
├── chatbot.py # RAG chatbot pipeline <br/>
├── prompts.py # LLM prompt templates <br/>
├── utils/ <br/>
│ ├── classification.py <br/>
│ ├── summarizer.py <br/>
│ └── clustering.py <br/>
├── data/ <br/>
│ ├── articles.json <br/>
│ └── articles_enriched.json <br/>
├── vector_store/ # ChromaDB persistent folder <br/>
├── .env # API keys <br/>
└── requirements.txt <br/>

---

## 🔧 Setup

### 1. Clone the repo
```bash
git clone https://github.com/Kritz23/NewsBotAI.git
cd NewsBotAI
```

### 2. Create environment
```bash
python3 -m venv venv
source venv/bin/activate        # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. Create .env with your API key
```bash
GROQ_API_KEY=your_groq_api_key_here
```

## 🧠 Workflow
### 1. Scrape articles
```bash
python scraper.py
```

### 2. Classify, summarize, cluster
```bash
python process_articles.py
```

### 3. Build vector DB for chatbot
```bash
python -c "import chatbot; chatbot.build_vector_db(force=True)"
```

### 4. Run the Streamlit UI
```bash
streamlit run app.py
```

### 5. Enjoy reading News by AI
Select a topic from the sidebar.
Click _"Run Scraper"_ to extract news articles.
Click _"Process Articles"_ to classify, summarize, cluster and store articles in DB.
Ask follow-up questions in the chat interface below the highlights.


## 👨‍💻 Built with
Streamlit
ChromaDB
Groq
Sentence Transformers
BeautifulSoup

## How NewsBotAI Works

This system is composed of five coordinated components that work together to scrape, process, and interact with real-world news in a contextual, AI-powered way.

<p align="center">
  <img src="resources/block.png" width="90%">
</p>

1. **Data Acquisition**
    - NewsLLM uses a custom Python-based web scraper (scraper.py) to gather fresh news articles from Australian media outlets.
    - Topics are predefined (sports, lifestyle, music, finance) and scraped individually from .au domains like:
    - smh.com.au, news.com.au, theguardian.com/au, etc.
    - The scraper retrieves up to N results per domain per topic, ensuring broad coverage across outlets.
    - Output is saved to data/articles.json.

2. **Database** (ChromaDB)
    - Articles are classified, summarized, and embedded using SentenceTransformers (MiniLM-L6 model).
    - Vector embeddings are stored in ChromaDB, allowing for fast and relevant document retrieval.
    - Each article's semantic fingerprint (vector) represents its meaning, context, and tone.
    - Vector DB is rebuilt using chatbot.build_vector_db() after new summaries are added.
    - This enables real-time similarity search when a user asks a question.

3. **Context Retrieval** (RAG)
    - When a user submits a query in the chatbot UI:
        - The query is embedded using the same transformer model.
        - Vector similarity is computed between the query and all stored summaries.
        - The top k=5 most relevant summaries are selected as context.
    - These summaries form a context window for answering the user's question.

4. **Output Generation**
    - The structured prompt and context are sent to the Groq API, using the powerful Mixtral-8x7B model.
    - The model generates a natural, grounded response with:
        - Key takeaways from relevant articles
        - Comparisons across sources
        - Context, trends, controversies, and outlook
    - Users can ask follow-up questions — creating a RAG-powered conversation loop.

5. **Daily Highlights** (UI Dashboard)
    - A Streamlit app presents:
        - Top-ranked daily news per topic
        - Keyword-weighted + frequency-ranked highlights
        - Summaries and source URLs
    - The UI also provides controls to:
        - Run scraping, article processing, or DB rebuilds manually
        - Interact with the news via a chatbot in real time


## Contributing

Contributions are welcome! Please feel free to open issues and submit pull requests.
