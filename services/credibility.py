from urllib.parse import urlparse

DOMAIN_TRUST = {
    # News
    "nytimes.com": 0.95,
    "theguardian.com": 0.92,
    "bbc.com": 0.93,
    "bbc.co.uk": 0.93,
    "reuters.com": 0.95,
    "apnews.com": 0.95,
    "washingtonpost.com": 0.92,
    "wsj.com": 0.91,
    "bloomberg.com": 0.91,
    "ft.com": 0.91,
    "economist.com": 0.92,
    "npr.org": 0.91,
    "politico.com": 0.85,
    "theatlantic.com": 0.87,
    "newyorker.com": 0.88,
    "time.com": 0.85,
    "forbes.com": 0.78,
    "businessinsider.com": 0.72,
    "techcrunch.com": 0.78,
    "wired.com": 0.82,
    "arstechnica.com": 0.83,
    "theverge.com": 0.80,
    "cnet.com": 0.75,
    "technewsworld.com": 0.70,

    # Medical / Health
    "clevelandclinic.org": 0.92,
    "mayoclinic.org": 0.95,
    "nih.gov": 0.97,
    "cdc.gov": 0.97,
    "who.int": 0.95,
    "webmd.com": 0.75,
    "healthline.com": 0.72,
    "medicalnewstoday.com": 0.70,

    # Academic / Research
    "nature.com": 0.97,
    "science.org": 0.97,
    "pubmed.ncbi.nlm.nih.gov": 0.97,
    "scholar.google.com": 0.90,
    "jstor.org": 0.92,
    "arxiv.org": 0.88,
    "springer.com": 0.90,
    "wiley.com": 0.90,

    # Government
    "gov.uk": 0.93,
    "europa.eu": 0.91,
    "un.org": 0.90,

    # Low trust
    "medium.com": 0.45,
    "substack.com": 0.50,
    "buzzfeed.com": 0.55,
    "dailymail.co.uk": 0.45,
    "nypost.com": 0.55,
    "breitbart.com": 0.30,
    "infowars.com": 0.10,
}

TYPE_WEIGHTS = {
    "news": 1.0,
    "research": 0.9,
    "pdf": 0.8,
    "blog": 0.7,
}

def get_domain_trust(url: str) -> float:
    try:
        domain = urlparse(url).netloc.replace("www.", "")
        # check exact match first, then check if url contains a known domain
        if domain in DOMAIN_TRUST:
            return DOMAIN_TRUST[domain]
        for known_domain, trust in DOMAIN_TRUST.items():
            if domain.endswith(known_domain):
                return trust
        return 0.6  # default for unknown domains
    except Exception:
        return 0.6


def score_credibility(ai_prob: float, url: str, content_type: str = "blog", text: str = None) -> float:
    domain_trust = get_domain_trust(url)
    type_score = TYPE_WEIGHTS.get(content_type, 0.7)

    ai_score     = (1 - ai_prob) * 40        # max 40pts
    domain_score = domain_trust * 35          # max 35pts
    type_score   = type_score * 15            # max 15pts
    length_score = min(len(text.split()) / 500, 1.0) * 10 if text else 5  # max 10pts

    return round(ai_score + domain_score + type_score + length_score, 2)