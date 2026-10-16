"""Semantic contract comparison and multilingual answers.

Sarvam is optional: a careful local verifier keeps the MVP usable without an API key.
"""
from __future__ import annotations

import os
import re
import json
from models import Market, Opportunity, Verification


def _dates(text: str) -> set[str]:
    return set(re.findall(r"20\d{2}-\d{2}-\d{2}", text))


def verify_equivalence(a: Market, b: Market) -> Verification:
    """Use Sarvam when configured, otherwise return a safety-first local assessment."""
    api_key = os.getenv("SARVAM_API_KEY")
    if api_key:
        try:
            from sarvamai import SarvamAI
            prompt = f"""You are a prediction-market contract auditor. Compare these binary contracts. Return ONLY JSON with equivalence_score (integer 0-100), verdict (SAFE_MATCH, POSSIBLE_MATCH, or NOT_EQUIVALENT), critical_differences (array of strings), short_reason (string), and checks (object with keys: Underlying event, Subject / entity, Settlement deadline, Resolution criteria, Resolution source; each value MATCH, REVIEW, or MISMATCH).

CONTRACT A (Kalshi)
Title: {a.title}
Close time: {a.close_time}
Rules: {a.rules}

CONTRACT B (Polymarket)
Title: {b.title}
Close time: {b.close_time}
Rules: {b.rules}

Be conservative: different cutoff times, sources, or resolution criteria must not be SAFE_MATCH."""
            client = SarvamAI(api_subscription_key=api_key)
            response = client.chat.completions(model="sarvam-105b", messages=[{"role": "user", "content": prompt}], temperature=0, max_tokens=700)
            data = json.loads(response.choices[0].message.content)
            return Verification(int(data["equivalence_score"]), data["verdict"], data.get("critical_differences", []), data["short_reason"], data["checks"], "Sarvam 105B")
        except Exception:
            # Credentials/API outages must never turn a market mismatch into a green signal.
            pass
    a_words = set(re.findall(r"[a-z]{4,}", (a.title + " " + a.rules).lower()))
    b_words = set(re.findall(r"[a-z]{4,}", (b.title + " " + b.rules).lower()))
    overlap = len(a_words & b_words) / max(1, len(a_words | b_words))
    deadlines_match = bool(_dates(a.close_time + " " + a.rules) & _dates(b.close_time + " " + b.rules)) or a.close_time[:10] == b.close_time[:10]
    title_overlap = len(set(re.findall(r"[a-z0-9]+", a.title.lower())) & set(re.findall(r"[a-z0-9]+", b.title.lower())))
    score = min(98, int(48 + overlap * 120 + min(title_overlap, 5) * 6 + (16 if deadlines_match else -22)))
    score = max(20, score)
    critical = []
    if not deadlines_match:
        critical.append(f"Different settlement deadlines: {a.close_time[:10]} vs {b.close_time[:10]}.")
    if "coinbase" in a.rules.lower() and "binance" in b.rules.lower():
        critical.append("Different price sources (Coinbase vs Binance) can resolve differently.")
    if critical:
        score = min(score, 72)
    verdict = "SAFE_MATCH" if score >= 92 and not critical else "POSSIBLE_MATCH" if score >= 75 and not critical else "NOT_EQUIVALENT"
    checks = {
        "Underlying event": "MATCH" if title_overlap >= 2 else "REVIEW",
        "Subject / entity": "MATCH" if title_overlap >= 2 else "REVIEW",
        "Settlement deadline": "MATCH" if deadlines_match else "MISMATCH",
        "Resolution criteria": "MATCH" if overlap > .12 else "REVIEW",
        "Resolution source": "REVIEW" if critical else "MATCH",
    }
    reason = "Contracts have aligned event, deadline, and broad resolution language." if not critical else "Rule-level differences prevent a safe arbitrage certification."
    return Verification(score, verdict, critical, reason, checks, "local safety verifier")


def explain_best(question: str, opportunities: list[Opportunity]) -> str:
    """A transparent offline multilingual copilot response, safe for demos without credentials."""
    if not opportunities:
        return "I found no AI-verified, positive-net-spread opportunity at the selected safety threshold."
    best = opportunities[0]
    api_key = os.getenv("SARVAM_API_KEY")
    if api_key:
        try:
            from sarvamai import SarvamAI
            context = "\n".join(f"- {x.label}; ROI {x.roi:.2f}%; match {x.verification.equivalence_score}%; risk: {x.verification.short_reason}" for x in opportunities[:5])
            prompt = f"""You are EventArb AI, a cautious paper-trading copilot. Answer in the user's language. Never tell the user a trade is guaranteed; note this is an estimate and no real trade is executed.\nOpportunities:\n{context}\n\nUser question: {question}"""
            client = SarvamAI(api_subscription_key=api_key)
            response = client.chat.completions(model="sarvam-105b", messages=[{"role": "user", "content": prompt}], temperature=.2, max_tokens=350)
            return response.choices[0].message.content
        except Exception:
            pass
    hindi = bool(re.search(r"[\u0900-\u097F]", question))
    if hindi:
        return (f"Abhi sabse strong opportunity **{best.label}** hai. Net ROI {best.roi:.2f}% aur contract match score "
                f"{best.verification.equivalence_score}% hai. Phir bhi liquidity aur rule changes check karke hi paper trade karein.")
    return (f"The strongest verified opportunity is **{best.label}**: estimated net ROI is {best.roi:.2f}% with a "
            f"{best.verification.equivalence_score}% contract-equivalence score. It is ranked first because it combines return, match confidence, and available liquidity.")
