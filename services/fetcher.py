import requests
from readability import Document
from bs4 import BeautifulSoup

def fetch_page_text(url):
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return ""

        # Extract main content with Readability
        doc = Document(resp.text)
        html_content = doc.summary()

        # Convert HTML to plain text
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator="\n")  # preserve some line breaks

        # Clean up excessive whitespace
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

        return text

    except Exception as e:
        print(f"Fetch error {url}: {e}")
        return ""