def score_credibility(ai_prob, domain_trust=0.7, content_type="blog"):
    type_weights = {"news": 1.0, "research": 0.9, "blog": 0.7, "pdf": 0.8}
    type_score = type_weights.get(content_type, 0.7)
    score = (1 - ai_prob) * 50 + domain_trust * 30 + type_score * 20
    return round(score, 2)