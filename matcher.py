"""Candidate generation: fast lexical matching before semantic verification."""
from __future__ import annotations

import re
from models import CandidatePair, Market

STOP_WORDS = {"will", "the", "a", "an", "to", "by", "in", "of", "for", "and", "or", "be", "is", "if", "on", "at", "with", "before", "after", "us", "u", "s"}


def keywords(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) > 2 and word not in STOP_WORDS}


def match_markets(kalshi: list[Market], polymarket: list[Market], threshold: float = .18) -> list[CandidatePair]:
    candidates = []
    for km in kalshi:
        kt = keywords(km.title)
        for pm in polymarket:
            pt = keywords(pm.title)
            shared = kt & pt
            score = len(shared) / max(1, len(kt | pt))
            if score >= threshold:
                candidates.append(CandidatePair(km, pm, score, sorted(shared)))
    return sorted(candidates, key=lambda pair: pair.keyword_score, reverse=True)
