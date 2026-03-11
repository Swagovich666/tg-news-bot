import requests
from bs4 import BeautifulSoup
import feedparser
from typing import List, Dict

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0; +https://example.com/bot)"
}

SOURCES = [
    # Оригинальные источники
    {
        "name": "banki",
        "type": "html",
        "url": "https://www.banki.ru/news/",
        "selector": "a.WidgetNews__title",
        "link_prefix": "https://www.banki.ru"
    },
    {
        "name": "ria-economy",
        "type": "rss",
        "url": "https://ria.ru/export/rss2/economy/index.xml"
    },
    
    # Футбол (Soccer)
    {
        "name": "bbc_football",
        "type": "rss",
        "url": "http://feeds.bbci.co.uk/sport/football/rss.xml"
    },
    {
        "name": "sky_football",
        "type": "rss",
        "url": "https://www.skysports.com/rss/11095/feed.xml"
    },
    {
        "name": "espn_football",
        "type": "rss",
        "url": "https://www.espn.com/espn/rss/soccer/news"
    },
    {
        "name": "guardian_football",
        "type": "rss",
        "url": "https://www.theguardian.com/football/rss"
    },
    {
        "name": "goal",
        "type": "rss",
        "url": "https://www.goal.com/feeds/en/news"
    },
    
    # Баскетбол (Basketball)
    {
        "name": "nba_official",
        "type": "rss",
        "url": "https://www.nba.com/news/rss.xml"
    },
    {
        "name": "espn_nba",
        "type": "rss",
        "url": "https://www.espn.com/espn/rss/nba/news"
    },
    {
        "name": "bleacher_nba",
        "type": "rss",
        "url": "https://bleacherreport.com/nba/feed"
    },
    {
        "name": "cbs_nba",
        "type": "rss",
        "url": "https://www.cbssports.com/nba/rss/news"
    },
    {
        "name": "yahoo_nba",
        "type": "rss",
        "url": "https://sports.yahoo.com/nba/rss"
    },
    
    # Формула-1 (Formula 1)
    {
        "name": "f1_official",
        "type": "rss",
        "url": "https://www.formula1.com/content/fom-website/en/latest/all.xml"
    },
    {
        "name": "bbc_f1",
        "type": "rss",
        "url": "http://feeds.bbci.co.uk/sport/formula1/rss.xml"
    },
    {
        "name": "sky_f1",
        "type": "rss",
        "url": "https://www.skysports.com/rss/12040/feed.xml"
    },
    {
        "name": "espn_f1",
        "type": "rss",
        "url": "https://www.espn.com/espn/rss/f1/news"
    },
    {
        "name": "autosport_f1",
        "type": "rss",
        "url": "https://www.autosport.com/rss/f1/news"
    },
    
    # Общие спортивные новости (All Sports)
    {
        "name": "bbc_sport_all",
        "type": "rss",
        "url": "http://feeds.bbci.co.uk/sport/rss.xml"
    },
    {
        "name": "espn_all",
        "type": "rss",
        "url": "https://www.espn.com/espn/rss/news"
    },
    {
        "name": "sky_sports_all",
        "type": "rss",
        "url": "https://www.skysports.com/rss/12040/feed.xml"
    },
    {
        "name": "yahoo_sports_all",
        "type": "rss",
        "url": "https://sports.yahoo.com/rss"
    },
]

def _fetch_html_list(url: str, selector: str, link_prefix: str = "") -> List[Dict]:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    for a in soup.select(selector)[:8]:
        href = a.get("href")
        if not href:
            continue
        link = href if href.startswith("http") else f"{link_prefix}{href}"
        title = a.get_text(strip=True)
        if title and link:
            items.append({"title": title, "link": link})
    return items

def _fetch_rss(url: str) -> List[Dict]:
    feed = feedparser.parse(url)
    items = []
    for e in feed.entries[:8]:
        link = e.get("link")
        title = e.get("title")
        if link and title:
            items.append({"title": title, "link": link})
    return items

def get_candidates() -> List[Dict]:
    all_items = []
    for src in SOURCES:
        try:
            if src["type"] == "html":
                items = _fetch_html_list(src["url"], src["selector"], src.get("link_prefix", ""))
            elif src["type"] == "rss":
                items = _fetch_rss(src["url"])
            else:
                items = []
            for it in items:
                it["source"] = src["name"]
            all_items.extend(items)
        except Exception:
            continue
    return all_items

def fetch_article_text(url: str) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        r.raise_for_status()
        from readability import Document
        doc = Document(r.text)
        html = doc.summary(html_partial=True)
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        text = soup.get_text("\n", strip=True)
        return text[:12000]
    except Exception:
        return ""
