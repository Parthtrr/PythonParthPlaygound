import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from readability import Document


class NewsService:
    BASE_URL = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"

    def __init__(self, timeout: int = 15, sleep_seconds: float = 1.2, max_content_chars: int = 12000):
        self.timeout = timeout
        self.sleep_seconds = sleep_seconds
        self.max_content_chars = max_content_chars

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0 Safari/537.36"
            )
        })

    def fetch(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Fetch latest news for query.
        """
        items = self._fetch_rss_sorted(query)[:max_results]

        # remove internal fields before returning
        for item in items:
            item["_published_dt"] = str(item["_published_dt"])
            # item.pop("_published_dt", None)
            item.pop("link", None)

        return items

    def _fetch_rss_sorted(self, query: str) -> List[Dict]:

        query = query.replace(" ", "+")
        url = self.BASE_URL.format(query=query)

        feed = feedparser.parse(url)

        items: List[Dict] = []
        seen_titles = set()

        for entry in feed.entries:

            title = (entry.get("title") or "").strip()
            if not title or title in seen_titles:
                continue

            seen_titles.add(title)

            published_str = entry.get("published", "") or entry.get("updated", "")
            published_dt = self._parse_rss_datetime(published_str)

            source = entry.source.title if hasattr(entry, "source") else "Unknown"
            link = entry.get("link", "")

            items.append({
                "title": title,
                "published": published_str,
                "source": source,
                "link": link,
                "_published_dt": published_dt
            })

        # sort by latest
        items.sort(
            key=lambda x: x["_published_dt"] or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True
        )

        return items

    @staticmethod
    def _parse_rss_datetime(value: str) -> Optional[datetime]:

        if not value:
            return None

        try:
            dt = parsedate_to_datetime(value)

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            return dt

        except Exception:
            return None

    def _resolve_final_url(self, url: str) -> Optional[str]:

        if not url:
            return None

        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            resp.raise_for_status()

            final = resp.url

            if self._is_google_news_url(final):
                canonical = (
                    self._extract_canonical(resp.text)
                    or self._extract_canonical_from_link_header(resp.headers)
                )
                return canonical or final

            return final

        except Exception:
            return None

    @staticmethod
    def _is_google_news_url(url: str) -> bool:

        try:
            host = urlparse(url).netloc.lower()
            return host.endswith("news.google.com")

        except Exception:
            return False

    @staticmethod
    def _extract_canonical(html: str) -> Optional[str]:

        try:
            soup = BeautifulSoup(html, "lxml")
            tag = soup.find("link", rel="canonical")

            if tag and tag.get("href"):
                return tag["href"].strip()

        except Exception:
            pass

        return None

    @staticmethod
    def _extract_canonical_from_link_header(headers: Dict) -> Optional[str]:

        link = headers.get("Link") or headers.get("link")

        if not link:
            return None

        try:
            parts = [p.strip() for p in link.split(",")]

            for p in parts:
                if 'rel="canonical"' in p or "rel=canonical" in p:
                    start = p.find("<")
                    end = p.find(">", start + 1)

                    if start != -1 and end != -1:
                        return p[start + 1:end].strip()

        except Exception:
            return None

        return None

    def _extract_article_text(self, url: str) -> Optional[str]:

        if not url:
            return None

        try:
            resp = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            resp.raise_for_status()

            doc = Document(resp.text)
            html = doc.summary()

            soup = BeautifulSoup(html, "lxml")
            text = soup.get_text("\n", strip=True)

            if not text or len(text) < 200:
                return None

            return text[: self.max_content_chars]

        except Exception:
            return None