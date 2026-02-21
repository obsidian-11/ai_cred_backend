# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from services.fetcher import fetch_page_text
from services.ai_detector import detect_ai
from services.credibility import score_credibility
from utils.mongo import get_collection
from concurrent.futures import ThreadPoolExecutor
import traceback

app = FastAPI()

class URLList(BaseModel):
    urls: list[str]
    
    
@app.delete("/flush_cache")
def flush_cache():
    collection = get_collection()
    result = collection.delete_many({})
    return {"deleted": result.deleted_count}

@app.post("/analyze_urls")
def analyze_urls(payload: URLList):
    urls = payload.urls
    print(f"[analyze_urls] Received {len(urls)} URLs: {urls}")
    collection = get_collection()

    def process_url(url):
        try:
            print(f"[process_url] Starting: {url}")

            # Check cache
            existing = collection.find_one({"url": url})
            if existing:
                print(f"[process_url] Cache hit for {url}, returning cached result")
                existing["_id"] = str(existing["_id"])
                return existing

            print(f"[process_url] No cache hit, fetching page content...")
            text = fetch_page_text(url)
            print(f"[process_url] fetch_page_text returned: {repr(text[:200]) if text else None}")

            if not text:
                print(f"[process_url] No text returned for {url}")
                return {"url": url, "error": "Failed to fetch content"}

            print(f"[process_url] Calling detect_ai on {len(text)} chars of text...")
            ai_prob = detect_ai(text)
            print(f"[process_url] detect_ai returned: {ai_prob}")

            # Determine content type
            content_type = "blog"
            if ".pdf" in url:
                content_type = "pdf"
            elif any(domain in url for domain in ["news", "nytimes", "guardian"]):
                content_type = "news"
            print(f"[process_url] content_type: {content_type}")

            # Calculate credibility score
            credibility = score_credibility(ai_prob, 0.7, content_type)
            print(f"[process_url] credibility: {credibility}")

            # Save to DB
            record = {
                "url": url,
                "ai_probability": ai_prob,
                "credibility_score": credibility,
                "content_type": content_type,
            }
            inserted = collection.insert_one(record)
            record["_id"] = str(inserted.inserted_id)
            print(f"[process_url] Saved to DB with _id: {record['_id']}")
            return record

        except Exception as e:
            print(f"[process_url] EXCEPTION for {url}: {e}")
            print(traceback.format_exc())
            return {"url": url, "error": str(e)}

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(process_url, urls))

    print(f"[analyze_urls] Done. Results: {results}")
    return results