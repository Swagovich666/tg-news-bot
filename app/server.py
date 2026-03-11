import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from news import get_candidates, fetch_article_text
from rewrite import rewrite_news
from publish import post_to_telegram
from storage import is_posted, mark_posted

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))
RUN_ON_STARTUP = os.getenv("RUN_ON_STARTUP", "true").lower() == "true"

logger = logging.getLogger("autoposter")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"),
                    format="%(asctime)s | %(levelname)s | %(message)s")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код до yield выполняется при ЗАПУСКЕ (startup)
    if RUN_ON_STARTUP:
        task = asyncio.create_task(worker_loop())
        logger.info("Lifespan startup: Background worker task created.")
    yield
    # Код после yield выполняется при ЗАВЕРШЕНИИ (shutdown)
    logger.info("Lifespan shutdown: Cleaning up...")

# Передаём lifespan в FastAPI
app = FastAPI(title="Autoposter Health", lifespan=lifespan)

async def worker_loop():
    logger.info("Background worker started. Interval=%s", CHECK_INTERVAL)
    while True:
        try:
            candidates = get_candidates()
            for item in candidates:
                url = item["link"]
                if is_posted(url):
                    continue
                logger.info("Processing: %s", url)
                text = fetch_article_text(url)
                rewritten = rewrite_news(item["title"], text, url)
                if "http" not in rewritten:
                    rewritten += f"\n\nИсточник: {url}"
                post_to_telegram(rewritten.strip())
                mark_posted(url)
                logger.info("Posted: %s", item["title"])
        except Exception as e:
            logger.exception("Loop error: %s", e)
        await asyncio.sleep(CHECK_INTERVAL)

@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/last")
async def last():
    return {"message": "Service is running", "interval": CHECK_INTERVAL}
