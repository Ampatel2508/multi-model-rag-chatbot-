"""URL Crawler - Fetch and process content from URLs."""

import logging
from typing import List
from langchain_core.documents import Document
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class URLCrawler:
    
    def __init__(self, timeout: int = 20, max_pages: int = 5000, min_text_length: int = 40):
        """
        Initialize URLCrawler.
        
        Args:
            timeout: Request timeout in seconds
            max_pages: Maximum number of pages to crawl
            min_text_length: Minimum text length to include in documents
        """
        self.timeout = timeout
        self.max_pages = max_pages
        self.min_text_length = min_text_length
        
        # Content tags to extract
        self.CONTENT_TAGS = ["p", "li", "pre", "code", "h1", "h2", "h3"]
        
        # File extensions to skip
        self.SKIP_EXTENSIONS = (
            ".jpg", ".jpeg", ".png", ".svg", ".gif",
            ".css", ".js", ".json", ".xml",
            ".pdf", ".zip", ".ico"
        )
    
    def is_valid_url(self, url: str, base_domain: str) -> bool:
        """Check if URL is valid and belongs to the same domain."""
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in ("http", "https") and
                parsed.netloc == base_domain and
                not parsed.path.endswith(self.SKIP_EXTENSIONS)
            )
        except Exception:
            return False
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and trailing slashes."""
        url = url.split("#")[0]
        return url.rstrip("/")
    
    def crawl(self, base_url: str) -> List[Document]:
        """
        Crawl website starting from base_url and extract all text content.
        
        Args:
            base_url: Starting URL to crawl
            
        Returns:
            List of Document objects with extracted content
        """
        visited = set()
        documents = []
        base_domain = urlparse(base_url).netloc
        
        logger.info(f"Starting crawl from {base_url}")
        
        def crawl_recursive(url: str):
            """Recursively crawl URLs."""
            if len(visited) >= self.max_pages:
                logger.info(f"Reached maximum page limit: {self.max_pages}")
                return
            
            url = self.normalize_url(url)
            
            if url in visited or not self.is_valid_url(url, base_domain):
                return
            
            visited.add(url)
            logger.info(f"Crawling ({len(visited)}/{self.max_pages}): {url}")
            
            # Fetch page
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {str(e)}")
                return
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract text from content tags
            for tag in soup.find_all(self.CONTENT_TAGS):
                text = tag.get_text(" ", strip=True)
                
                if len(text) >= self.min_text_length:
                    doc = Document(
                        page_content=text,
                        metadata={
                            "source": base_url,
                            "url": url,
                            "tag": tag.name
                        }
                    )
                    documents.append(doc)
            
            # Discover and crawl links
            for a in soup.find_all("a", href=True):
                next_url = urljoin(url, a["href"])
                crawl_recursive(next_url)
        
        crawl_recursive(base_url)
        
        logger.info(f"✓ Crawl completed. Found {len(documents)} documents from {len(visited)} pages")
        return documents
    
    def process_url(self, url: str) -> List[Document]:
        """
        Process a single URL or crawl from it.
        
        Args:
            url: URL to process
            
        Returns:
            List of Document objects
        """
        return self.crawl(url)