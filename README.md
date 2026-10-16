# EventArb AI

An AI-gated, cross-market prediction-market arbitrage demonstrator. It compares Kalshi and Polymarket binary contracts, produces lexical candidate pairs, validates contract meaning, models fees/slippage, and supports simulated paper trades. It deliberately does **not** submit real-money orders.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

The scanner calls public venue endpoints first and uses a deterministic demo snapshot if a venue is unavailable or its response changes. That makes the hackathon presentation dependable even without network access.

## Sarvam AI (optional, recommended)

Put `SARVAM_API_KEY=...` in `.env`. With the key present, EventArb calls Sarvam 105B for structured contract-equivalence decisions and multilingual explanations. With no key or an API failure it falls back conservatively to a local rule verifier; that fallback can never turn a detected rule conflict into a `SAFE_MATCH`.

Sarvam integration follows the [official Chat Completions API](https://docs.sarvam.ai/api-reference/chat/chat-completions-v1).

## Architecture

```
Kalshi + Polymarket → normalized Market objects → keyword candidate matcher
    → Sarvam / conservative verifier → arbitrage calculator → Streamlit dashboard
    → paper portfolio + multilingual copilot
```

## Safety model

- A signal requires a positive net return **and** an equivalence score meeting the selected gate (90% by default).
- Fee and slippage estimates are added to cost before calculating return.
- Resolution-source or settlement-date differences are highlighted and block `SAFE_MATCH` in fallback mode.
- All trading is simulated. Prices, liquidity, and outputs are informational estimates only.





WEBSITE LINK
https://lightshrey-eventarb-ai-app-6m9yvj.streamlit.app/
