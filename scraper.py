#!/usr/bin/env python3
"""
Australian News Scraper Pipeline
Scrapes news articles from multiple Australian outlets across sports, lifestyle, music, and finance categories.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timezone
import time
import re
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Article:
    """Data class for article information"""
    topic: str
    title: str
    author: str
    source: str
    url: str
    published: str
    content: str

class NewsScraperPipeline:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-AU,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Australian news sources configuration
        self.sources = {
            'smh': {
                'name': 'Sydney Morning Herald',
                'base_url': 'https://www.smh.com.au',
                'categories': {
                    "sports": "https://www.smh.com.au/sport",
                    "lifestyle": "https://www.smh.com.au/lifestyle",
                    "music": "https://www.smh.com.au/culture/music",
                    "finance": "https://www.smh.com.au/business/banking-and-finance"
                }
            },
            'news_com_au': {
                'name': 'News.com.au',
                'base_url': 'https://news.com.au',
                'categories': {
                    'sports': 'https://news.com.au/sport',
                    'lifestyle': 'https://news.com.au/lifestyle',
                    'finance': 'https://news.com.au/finance',
                    'music': 'https://news.com.au/entertainment/music'
                }
            },
            'seven_news': {
                'name': '7News',
                'base_url': 'https://7news.com.au',
                'categories': {
                    "sports": "https://7news.com.au/sport",
                    "lifestyle": "https://7news.com.au/lifestyle",
                    "music": "https://7news.com.au/entertainment/music",
                    "finance": "https://7news.com.au/business/finance"
                }
            },
            'the_guardian': {
                'name': 'The Guardian',
                'base_url': 'https://www.theguardian.com',
                'categories': {
                    "sports": "https://www.theguardian.com/au/sport",
                    "lifestyle": "https://www.theguardian.com/au/lifeandstyle",
                    "music": "https://www.theguardian.com/music",
                    "finance": "https://www.theguardian.com/au/business"
                }
            }
        }
        
        self.scraped_urls = set()  # Track scraped URLs to avoid duplicates
        
    def fetch_page(self, url: str, timeout: int = 10) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        text = re.sub(r'\s+', ' ', text)
        # Remove ads and promotional content
        text = re.sub(r'(advertisement|sponsored|promoted content|sign up|subscribe)', '', text, flags=re.IGNORECASE)
        return text.strip()
    
    def extract_date(self, soup: BeautifulSoup, article_url: str) -> str:
        """Extract publication date from article"""
        date_selectors = [
            'time[datetime]',
            '.timestamp',
            '.date',
            '.published',
            '[data-timestamp]',
            '.article-date',
            '.story-date'
        ]
        
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                # Try datetime attribute first
                if date_elem.get('datetime'):
                    try:
                        return datetime.fromisoformat(date_elem['datetime'].replace('Z', '+00:00')).isoformat()
                    except:
                        pass
                
                # Try data-timestamp
                if date_elem.get('data-timestamp'):
                    try:
                        timestamp = int(date_elem['data-timestamp'])
                        return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
                    except:
                        pass
                
                # Try text content
                date_text = date_elem.get_text(strip=True)
                if date_text:
                    try:
                        # Parse various date formats
                        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%B %d, %Y', '%d %B %Y']:
                            try:
                                parsed_date = datetime.strptime(date_text, fmt)
                                return parsed_date.replace(tzinfo=timezone.utc).isoformat()
                            except:
                                continue
                    except:
                        pass
        
        # Fallback to current time
        return datetime.now(timezone.utc).isoformat()
    
    def extract_article_links(self, soup: BeautifulSoup, base_url: str, category: str) -> List[str]:
        """Extract article links from category page"""
        links = []
        
        # Common selectors for article links
        link_selectors = [
            'a[href*="/news/"]',
            'a[href*="/sport/"]',
            'a[href*="/lifestyle/"]',
            'a[href*="/lifeandstyle/"]',
            'a[href*="/business/"]',
            'a[href*="/finance/"]',
            'a[href*="/banking-and-finance/"]',
            'a[href*="/entertainment/"]',
            'a[href*="/music/"]',
            '.story-block a',
            '.article-link',
            '.headline a',
            'h1 a, h2 a, h3 a',
            '.story-headline a'
        ]
        
        for selector in link_selectors:
            elements = soup.select(selector)
            for elem in elements:
                href = elem.get('href')
                if href:
                    # Convert relative URLs to absolute
                    full_url = urljoin(base_url, href)
                    
                    # Filter out unwanted links
                    if self.is_valid_article_url(full_url):
                        links.append(full_url)
        
        # Remove duplicates and limit
        return list(set(links))[:20]  # Limit to 20 articles per category
    
    def is_valid_article_url(self, url: str) -> bool:
        """Check if URL is a valid news article"""
        excluded_patterns = [
            '/video/', '/videos/', '/gallery/', '/galleries/',
            '/podcast/', '/podcasts/', '/live/', '/weather/',
            'javascript:', 'mailto:', '#', '?'
        ]
        
        # Check for excluded patterns
        for pattern in excluded_patterns:
            if pattern in url.lower():
                return False
        
        # Must be a reasonable length and have path
        parsed = urlparse(url)
        if len(parsed.path) <= 1 or len(url) >= 500:
            return False
        
        # Source-specific URL validation
        domain = parsed.netloc.lower()
        
        # News.com.au - must contain "news-story"
        if 'news.com.au' in domain:
            return 'news-story' in url
        
        # SMH - must end with .html
        elif 'smh.com.au' in domain:
            return url.endswith('.html')
        
        # The Guardian - must contain "blog" (actually looking for date pattern like /2025/aug/01/)
        elif 'theguardian.com' in domain:
            # Guardian URLs typically have date patterns like /2025/aug/01/ or contain blog
            import re
            date_pattern = r'/\d{4}/(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/\d{1,2}/'
            return bool(re.search(date_pattern, url, re.IGNORECASE)) or 'blog' in url
        
        # 7News - must end with 8-digit number
        elif '7news.com.au' in domain:
            import re
            # Check if URL ends with -c-<8 digits>
            pattern = r'-c-\d{8}$'

            return bool(re.search(pattern, url))
        
        # For any other domains, use general validation
        return True
    
    def scrape_guardian_article(self, url: str, category: str) -> Optional[Article]:
        """Scrape The Guardian article with specific selectors"""
        soup = self.fetch_page(url)
        if not soup:
            return None
        
        try:
            # Guardian-specific selectors
            title_elem = soup.select_one('[data-gu-name="headline"]') or soup.select_one('h1')
            title = self.clean_text(title_elem.get_text()) if title_elem else ""
            
            author_elem = soup.select_one('[rel="author"]') or soup.select_one('.byline a') or soup.select_one('[data-component="Byline"] a')
            author = self.clean_text(author_elem.get_text()) if author_elem else "The Guardian"
            
            # Guardian content selectors
            content_elem = soup.select_one('[data-component="ArticleBody"]') or soup.select_one('.article-body-commercial-selector')
            if content_elem:
                # Remove unwanted elements
                for elem in content_elem.select('script, style, .ad, .advertisement, figure, .element-rich-link'):
                    elem.decompose()
                content = self.clean_text(content_elem.get_text())
            else:
                # Fallback to paragraphs
                paragraphs = soup.select('.content__article-body p')
                content = ' '.join([self.clean_text(p.get_text()) for p in paragraphs])
            
            published = self.extract_date(soup, url)
            
            if title and content and len(content) > 100:
                return Article(
                    topic=category,
                    title=title,
                    author=author,
                    source="The Guardian",
                    url=url,
                    published=published,
                    content=content
                )
        except Exception as e:
            logger.error(f"Error scraping Guardian article {url}: {str(e)}")
        
        return None
    
    def scrape_generic_article(self, url: str, category: str, source_name: str) -> Optional[Article]:
        """Generic article scraper for most news sites"""
        soup = self.fetch_page(url)
        if not soup:
            return None
        
        try:
            # Title extraction
            title_selectors = [
                'h1', '.headline', '.story-headline', '.article-headline',
                '.entry-title', '.post-title', '[data-testid="headline"]'
            ]
            title = ""
            for selector in title_selectors:
                elem = soup.select_one(selector)
                if elem:
                    title = self.clean_text(elem.get_text())
                    break
            
            # Author extraction
            author_selectors = [
                '.byline a', '.author', '.story-author', '[rel="author"]',
                '.article-author', '.reporter', '.journalist'
            ]
            author = source_name  # Default to source name
            for selector in author_selectors:
                elem = soup.select_one(selector)
                if elem:
                    author = self.clean_text(elem.get_text())
                    break
            
            # Content extraction
            content_selectors = [
                '.story-text', '.article-content', '.entry-content',
                '.post-content', '.article-body', '.story-body',
                '[data-testid="article-body"]', '.content'
            ]
            content = ""
            for selector in content_selectors:
                elem = soup.select_one(selector)
                if elem:
                    # Remove unwanted elements
                    for unwanted in elem.select('script, style, .ad, .advertisement, .social-share, .related-articles'):
                        unwanted.decompose()
                    content = self.clean_text(elem.get_text())
                    break
            
            # If no specific content selector works, try paragraphs
            if not content:
                paragraphs = soup.select('p')
                content = ' '.join([self.clean_text(p.get_text()) for p in paragraphs])
            
            published = self.extract_date(soup, url)
            
            if title and content and len(content) > 100:
                return Article(
                    topic=category,
                    title=title,
                    author=author,
                    source=source_name,
                    url=url,
                    published=published,
                    content=content
                )
        except Exception as e:
            logger.error(f"Error scraping article {url}: {str(e)}")
        
        return None
    
    def scrape_category(self, source_key: str, category: str) -> List[Article]:
        """Scrape articles from a specific category"""
        source_info = self.sources[source_key]
        category_url = source_info['categories'].get(category)
        
        if not category_url:
            logger.warning(f"No URL for category {category} in source {source_key}")
            return []
        
        logger.info(f"Scraping {source_info['name']} - {category}")
        
        # Fetch category page
        soup = self.fetch_page(category_url)
        if not soup:
            return []
        
        # Extract article links
        article_links = self.extract_article_links(soup, source_info['base_url'], category)
        articles = []
        
        # Scrape each article
        for link in article_links:
            if link in self.scraped_urls:
                continue
            
            self.scraped_urls.add(link)
            
            if source_key == 'the_guardian':
                article = self.scrape_guardian_article(link, category)
            else:
                article = self.scrape_generic_article(link, category, source_info['name'])
            
            if article:
                articles.append(article)
                logger.info(f"Scraped: {article.title[:50]}...")
            
            # Rate limiting
            time.sleep(0.5)
        
        return articles
    
    def run_pipeline(self, categories: List[str] = None, sources: List[str] = None, max_workers: int = 3) -> List[Article]:
        """Run the complete scraping pipeline"""
        if categories is None:
            categories = ['sports', 'lifestyle', 'music', 'finance']
        
        if sources is None:
            sources = list(self.sources.keys())
        
        all_articles = []
        
        # Create tasks for concurrent execution
        tasks = []
        for source_key in sources:
            if source_key in self.sources:
                for category in categories:
                    if category in self.sources[source_key]['categories']:
                        tasks.append((source_key, category))
        
        # Execute scraping with thread pool
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {
                executor.submit(self.scrape_category, source_key, category): (source_key, category)
                for source_key, category in tasks
            }
            
            for future in as_completed(future_to_task):
                source_key, category = future_to_task[future]
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                    logger.info(f"Completed {source_key} - {category}: {len(articles)} articles")
                except Exception as e:
                    logger.error(f"Error scraping {source_key} - {category}: {str(e)}")
        
        return all_articles
    
    def save_articles(self, articles: List[Article], filename: str = "data/articles.json"):
        """Save articles to JSON file"""
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Convert articles to dictionaries
        articles_data = [asdict(article) for article in articles]
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(articles)} articles to {filename}")
    
    def filter_articles(self, articles: List[Article]) -> List[Article]:
        """Filter out low-quality articles"""
        filtered_articles = []
        
        for article in articles:
            # Skip articles with minimal content
            if len(article.content) < 200:
                continue
            
            # Skip articles with generic titles
            generic_titles = ['breaking', 'live updates', 'watch', 'video']
            if any(generic in article.title.lower() for generic in generic_titles):
                continue
            
            # Skip duplicate articles (based on title similarity)
            is_duplicate = False
            for existing in filtered_articles:
                if self.similarity(article.title, existing.title) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_articles.append(article)
        
        return filtered_articles
    
    def similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)

    def print_detailed_statistics(self, articles: List[Article]):
        """Print detailed statistics of scraped articles"""
        if not articles:
            logger.info("No articles to analyze")
            return
        
        # Create nested dictionary for statistics
        stats = {}
        source_totals = {}
        topic_totals = {}
        
        for article in articles:
            source = article.source
            topic = article.topic
            
            # Initialize nested structure
            if source not in stats:
                stats[source] = {}
                source_totals[source] = 0
            
            if topic not in stats[source]:
                stats[source][topic] = 0
            
            # Count articles
            stats[source][topic] += 1
            source_totals[source] += 1
            topic_totals[topic] = topic_totals.get(topic, 0) + 1
        
        # Print detailed breakdown
        print("\n" + "="*80)
        print("DETAILED SCRAPING STATISTICS")
        print("="*80)
        
        print(f"\nTotal Articles Scraped: {len(articles)}")
        print(f"Sources: {len(stats)}")
        print(f"Categories: {len(topic_totals)}")
        
        # Print by source and topic
        print(f"\n{'SOURCE':<25} {'SPORTS':<8} {'LIFESTYLE':<10} {'MUSIC':<8} {'FINANCE':<8} {'TOTAL':<8}")
        print("-" * 80)
        
        for source in sorted(stats.keys()):
            sports = stats[source].get('sports', 0)
            lifestyle = stats[source].get('lifestyle', 0) 
            music = stats[source].get('music', 0)
            finance = stats[source].get('finance', 0)
            total = source_totals[source]
            
            print(f"{source:<25} {sports:<8} {lifestyle:<10} {music:<8} {finance:<8} {total:<8}")
        
        # Print totals row
        print("-" * 80)
        total_sports = topic_totals.get('sports', 0)
        total_lifestyle = topic_totals.get('lifestyle', 0)
        total_music = topic_totals.get('music', 0)
        total_finance = topic_totals.get('finance', 0)
        grand_total = len(articles)
        
        print(f"{'TOTALS':<25} {total_sports:<8} {total_lifestyle:<10} {total_music:<8} {total_finance:<8} {grand_total:<8}")
        
        # Print percentage breakdown
        print(f"\nCATEGORY BREAKDOWN:")
        for topic, count in sorted(topic_totals.items()):
            percentage = (count / len(articles)) * 100
            print(f"  {topic.capitalize():<12}: {count:>3} articles ({percentage:>5.1f}%)")
        
        print(f"\nSOURCE BREAKDOWN:")
        for source, count in sorted(source_totals.items()):
            percentage = (count / len(articles)) * 100
            print(f"  {source:<20}: {count:>3} articles ({percentage:>5.1f}%)")
        
        # Find most productive source per category
        print(f"\nTOP PERFORMING SOURCES BY CATEGORY:")
        for topic in sorted(topic_totals.keys()):
            best_source = ""
            best_count = 0
            for source in stats:
                count = stats[source].get(topic, 0)
                if count > best_count:
                    best_count = count
                    best_source = source
            
            if best_count > 0:
                print(f"  {topic.capitalize():<12}: {best_source} ({best_count} articles)")

def main():
    """Main function to run the scraper"""
    scraper = NewsScraperPipeline()
    
    # Categories to scrape
    categories = ['sports', 'lifestyle', 'music', 'finance']
    
    # Run the pipeline
    logger.info("Starting Australian news scraping pipeline...")
    articles = scraper.run_pipeline(categories=categories)
    
    # Filter articles
    filtered_articles = scraper.filter_articles(articles)
    
    # Save results
    scraper.save_articles(filtered_articles)
    
    # Print detailed statistics
    scraper.print_detailed_statistics(filtered_articles)
    
    print(f"\nArticles saved to: data/articles.json")
    print("="*80)

if __name__ == "__main__":
    main()
