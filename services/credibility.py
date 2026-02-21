from urllib.parse import urlparse
import math
import numpy as np

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
        if domain in DOMAIN_TRUST:
            return DOMAIN_TRUST[domain]
        for known_domain, trust in DOMAIN_TRUST.items():
            if domain.endswith(known_domain):
                return trust
        return 0.6
    except Exception:
        return 0.6


def burstiness(text: str) -> float:
    """
    Measures sentence length variance — humans vary sentence length more than AI.
    Returns 0-1, higher = more human-like variation.
    """
    sentences = [s.strip() for s in text.split('.') if len(s.strip().split()) > 2]
    if len(sentences) < 3:
        return 0.5
    lengths = [len(s.split()) for s in sentences]
    mean = np.mean(lengths)
    std = np.std(lengths)
    if mean == 0:
        return 0.5
    cv = std / mean  # coefficient of variation
    # Typical human CV ~0.5-0.9, AI ~0.2-0.4
    return float(min(cv / 0.8, 1.0))


def bayesian_combine(signals: dict) -> float:
    """
    Combines independent probability signals using log-odds Bayesian update.
    Each signal is treated as P(credible | evidence).
    Returns combined probability 0-1.
    """
    # Neutral prior: 50% credible before seeing any evidence
    log_odds = 0.0
    for name, s in signals.items():
        s = max(0.01, min(0.99, s))  # avoid log(0)
        log_odds += math.log(s / (1 - s))
    return 1 / (1 + math.exp(-log_odds))


def score_credibility(ai_prob: float, url: str, content_type: str = "blog", text: str = None):
    domain_trust = get_domain_trust(url)
    type_weight = TYPE_WEIGHTS.get(content_type, 0.7)
    domain = urlparse(url).netloc.replace("www.", "")

    # Build signals dict for Bayesian combination
    signals = {
        "ai_detection": 1 - ai_prob,
        "domain_trust": domain_trust,
        "content_type": type_weight,
        "length": min(len(text.split()) / 500, 1.0) if text else 0.5,
        "burstiness": burstiness(text) if text else 0.5,
    }

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
    elif domain_trust == 0.6:
        reasons.append(f"{domain} is an unknown domain with no established trust score")
    else:
        reasons.append(f"{domain} has low domain trust ({round(domain_trust * 100)}%)")

    if content_type == "news":
        reasons.append("News content carries higher credibility weight")
    elif content_type == "blog":
        reasons.append("Blog content carries lower credibility weight")
    elif content_type == "research":
        reasons.append("Research content carries high credibility weight")

    if text:
        word_count = len(text.split())
        burst = signals["burstiness"]
        if word_count >= 500:
            reasons.append(f"Substantive article length ({word_count} words)")
        elif word_count < 150:
            reasons.append(f"Short content may lack depth ({word_count} words)")
        if burst > 0.65:
            reasons.append(f"High sentence length variation suggests human authorship")
        elif burst < 0.35:
            reasons.append(f"Low sentence length variation is consistent with AI writing")

    return {
        "credibility_score": total,
        "reasoning": reasons,
        "signals": {k: round(v, 3) for k, v in signals.items()},
    }