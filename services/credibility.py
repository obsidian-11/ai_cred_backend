from urllib.parse import urlparse
import math
import numpy as np

DOMAIN_TRUST = {
    # Top-tier News
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
    "usatoday.com": 0.80,
    "nbcnews.com": 0.82,
    "abcnews.go.com": 0.82,
    "cbsnews.com": 0.82,
    "cnbc.com": 0.83,
    "cnn.com": 0.80,
    "foxnews.com": 0.65,
    "thehill.com": 0.78,
    "axios.com": 0.85,
    "vox.com": 0.80,
    "slate.com": 0.75,
    "salon.com": 0.65,
    "huffpost.com": 0.65,

    # Tech News
    "forbes.com": 0.78,
    "businessinsider.com": 0.72,
    "techcrunch.com": 0.78,
    "wired.com": 0.82,
    "arstechnica.com": 0.83,
    "theverge.com": 0.80,
    "cnet.com": 0.75,
    "technewsworld.com": 0.70,
    "zdnet.com": 0.74,
    "engadget.com": 0.74,
    "gizmodo.com": 0.70,
    "venturebeat.com": 0.74,
    "technologyreview.com": 0.88,
    "ieee.org": 0.92,
    "acm.org": 0.92,

    # Medical / Health
    "clevelandclinic.org": 0.92,
    "mayoclinic.org": 0.95,
    "nih.gov": 0.97,
    "cdc.gov": 0.97,
    "who.int": 0.95,
    "fda.gov": 0.95,
    "webmd.com": 0.75,
    "healthline.com": 0.72,
    "medicalnewstoday.com": 0.70,
    "medlineplus.gov": 0.95,
    "hopkinsmedicine.org": 0.93,
    "health.harvard.edu": 0.94,
    "nejm.org": 0.97,
    "thelancet.com": 0.97,
    "jamanetwork.com": 0.96,
    "bmj.com": 0.96,

    # Academic / Research
    "nature.com": 0.97,
    "science.org": 0.97,
    "pubmed.ncbi.nlm.nih.gov": 0.97,
    "scholar.google.com": 0.90,
    "jstor.org": 0.92,
    "arxiv.org": 0.88,
    "springer.com": 0.90,
    "wiley.com": 0.90,
    "sciencedirect.com": 0.91,
    "researchgate.net": 0.82,
    "academia.edu": 0.72,
    "ssrn.com": 0.83,
    "plos.org": 0.88,
    "frontiersin.org": 0.80,

    # Government
    "gov.uk": 0.93,
    "europa.eu": 0.91,
    "un.org": 0.90,
    "usa.gov": 0.94,
    "whitehouse.gov": 0.88,
    "congress.gov": 0.92,
    "senate.gov": 0.91,
    "supremecourt.gov": 0.93,
    "data.gov": 0.92,
    "census.gov": 0.93,
    "bls.gov": 0.93,

    # Finance
    "sec.gov": 0.95,
    "federalreserve.gov": 0.95,
    "imf.org": 0.93,
    "worldbank.org": 0.92,
    "investopedia.com": 0.75,
    "marketwatch.com": 0.78,
    "morningstar.com": 0.82,

    # Legal
    "law.cornell.edu": 0.92,
    "justia.com": 0.88,
    "oyez.org": 0.90,

    # Low trust / tabloid
    "medium.com": 0.45,
    "substack.com": 0.50,
    "buzzfeed.com": 0.55,
    "buzzfeednews.com": 0.65,
    "dailymail.co.uk": 0.40,
    "nypost.com": 0.52,
    "breitbart.com": 0.25,
    "infowars.com": 0.05,
    "naturalnews.com": 0.08,
    "thegatewaypundit.com": 0.10,
    "zerohedge.com": 0.25,
    "rt.com": 0.20,
    "sputniknews.com": 0.15,

    # AI content farms
    "copy.ai": 0.20,
    "jasper.ai": 0.20,
    "writesonic.com": 0.20,
    "rytr.me": 0.20,
    "anyword.com": 0.20,
    "contentatscale.com": 0.15,
    "articleforge.com": 0.15,
}

TYPE_WEIGHTS = {
    "news": 1.0,
    "research": 0.95,
    "pdf": 0.85,
    "blog": 0.65,
    "unknown": 0.60,
}

RESEARCH_DOMAINS = {
    "arxiv.org", "pubmed.ncbi.nlm.nih.gov", "nature.com", "science.org",
    "nejm.org", "thelancet.com", "jamanetwork.com", "bmj.com", "plos.org",
}
NEWS_DOMAINS = {
    "nytimes.com", "theguardian.com", "bbc.com", "reuters.com", "apnews.com",
    "washingtonpost.com", "bloomberg.com", "npr.org", "axios.com", "cnbc.com",
}


def get_domain_trust(url: str) -> float:
    try:
        domain = urlparse(url).netloc.replace("www.", "")
        if domain in DOMAIN_TRUST:
            return DOMAIN_TRUST[domain]
        for known_domain, trust in DOMAIN_TRUST.items():
            if domain.endswith(known_domain):
                return trust
        return 0.40
    except Exception:
        return 0.40


def get_content_type(url: str, hint: str = "blog") -> str:
    try:
        domain = urlparse(url).netloc.replace("www.", "")
        if domain in RESEARCH_DOMAINS:
            return "research"
        if domain in NEWS_DOMAINS:
            return "news"
        if ".gov" in domain or ".edu" in domain:
            return "research"
    except Exception:
        pass
    return hint


def burstiness(text: str) -> float:
    sentences = [s.strip() for s in text.split('.') if len(s.strip().split()) > 2]
    if len(sentences) < 3:
        return 0.5
    lengths = [len(s.split()) for s in sentences]
    mean = np.mean(lengths)
    std = np.std(lengths)
    if mean == 0:
        return 0.5
    cv = std / mean
    return float(min(cv / 0.8, 1.0))


def bayesian_combine(signals: dict) -> float:
    log_odds = 0.0
    for s in signals.values():
        s = max(0.01, min(0.99, s))
        log_odds += 0.5 * math.log(s / (1 - s))
    prob = 1 / (1 + math.exp(-log_odds))
    return max(0.10, min(0.92, prob))


def score_credibility(ai_prob: float, url: str, content_type: str = "blog", text: str = None):
    domain_trust = get_domain_trust(url)
    domain = urlparse(url).netloc.replace("www.", "")

    content_type = get_content_type(url, content_type)
    type_weight = TYPE_WEIGHTS.get(content_type, 0.60)

    # Force high ai_prob for known low-trust/AI farm domains
    # so the detector can't override domain knowledge
    if domain_trust <= 0.25:
        ai_prob = max(ai_prob, 0.90)

    signals = {
        "ai_detection": 1 - ai_prob,
        "domain_trust": domain_trust,
        "content_type": type_weight,
        "length": min(len(text.split()) / 500, 1.0) if text else 0.5,
        "burstiness": burstiness(text) if text else 0.5,
    }

    if domain_trust <= 0.25:
        signals["source_penalty"] = 0.10

    combined_prob = bayesian_combine(signals)
    total = round(combined_prob * 100, 2)

    # Build reasoning
    reasons = []

    if ai_prob > 0.65:
        reasons.append(f"Content appears likely AI-generated ({round(ai_prob * 100)}% probability)")
    elif ai_prob < 0.35:
        reasons.append(f"Content appears human-written ({round((1 - ai_prob) * 100)}% confidence)")
    else:
        reasons.append(f"AI authorship is uncertain ({round(ai_prob * 100)}% AI probability)")

    if domain_trust >= 0.90:
        reasons.append(f"{domain} is a highly trusted source")
    elif domain_trust >= 0.75:
        reasons.append(f"{domain} has moderate-to-high domain trust")
    elif domain_trust >= 0.50:
        reasons.append(f"{domain} has below-average domain trust")
    elif domain_trust <= 0.25:
        reasons.append(f"{domain} is a low-trust or AI content source")
    else:
        reasons.append(f"{domain} is an unknown domain with no established trust score")

    if content_type == "news":
        reasons.append("Recognized as a news source")
    elif content_type == "research":
        reasons.append("Academic or research content carries high credibility weight")
    elif content_type == "blog":
        reasons.append("Blog content carries lower credibility weight")

    if text:
        word_count = len(text.split())
        burst = signals["burstiness"]
        if word_count >= 500:
            reasons.append(f"Substantive article length ({word_count} words)")
        elif word_count < 150:
            reasons.append(f"Short content may lack depth ({word_count} words)")
        if burst > 0.65:
            reasons.append("High sentence variation suggests human authorship")
        elif burst < 0.35:
            reasons.append("Low sentence variation is consistent with AI writing")

    return {
        "credibility_score": total,
        "reasoning": reasons,
        "signals": {k: round(v, 3) for k, v in signals.items()},
    }