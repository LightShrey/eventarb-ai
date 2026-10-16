import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from kalshi_service import fetch_markets as kalshi_markets
from polymarket_service import fetch_markets as polymarket_markets
from matcher import match_markets
from sarvam_service import verify_equivalence, explain_best
from arbitrage import calculate, rank

load_dotenv()
st.set_page_config(page_title="EventArb AI", page_icon="⚡", layout="wide")

st.markdown("""<style>
.stApp { background: #08111f; color: #e8eefc; }
[data-testid='stMetric'] { background: #101f36; border: 1px solid #233b60; padding: 14px; border-radius: 12px; }
.hero { padding: 28px 0 12px; } .eyebrow { color:#55d7b2; font-weight:700; letter-spacing:.12em; font-size:.8rem; }
.verdict { color:#55d7b2; font-weight:800; font-size:1.1rem; }
</style>""", unsafe_allow_html=True)

if "portfolio" not in st.session_state:
    st.session_state.portfolio = []
if "scan" not in st.session_state:
    st.session_state.scan = None

with st.sidebar:
    st.header("Scanner controls")
    fee_bps = st.slider("Estimated fees (bps)", 0, 300, 100, 5)
    slippage_bps = st.slider("Slippage (bps)", 0, 300, 50, 5)
    match_gate = st.slider("Minimum AI match score", 60, 100, 90, 1)
    position_size = st.number_input("Paper-trade capital ($)", min_value=25.0, max_value=10000.0, value=500.0, step=25.0)
    st.caption("Read-only market data. No real-money orders are sent.")

st.markdown("<div class='hero'><div class='eyebrow'>CROSS-MARKET INTELLIGENCE</div><h1>⚡ EventArb AI</h1><p>Find price discrepancies—then verify that the contracts really mean the same thing.</p></div>", unsafe_allow_html=True)

if st.button("Scan markets", type="primary", use_container_width=True):
    with st.spinner("Fetching markets, matching contracts, and checking settlement semantics..."):
        kalshi, kalshi_source = kalshi_markets()
        poly, poly_source = polymarket_markets()
        candidates = match_markets(kalshi, poly)
        all_opportunities = []
        for pair in candidates:
            verification = verify_equivalence(pair.kalshi, pair.polymarket)
            all_opportunities.extend(calculate(pair, verification, fee_bps / 10000, slippage_bps / 10000))
        st.session_state.scan = {"kalshi": kalshi, "poly": poly, "candidates": candidates, "opportunities": rank(all_opportunities, match_gate), "sources": (kalshi_source, poly_source)}

scan = st.session_state.scan
if not scan:
    st.info("Click **Scan markets** to start. The app uses public APIs when available and switches to a curated demo snapshot if an exchange endpoint is unavailable.")
    st.stop()

opportunities = scan["opportunities"]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Markets scanned", len(scan["kalshi"]) + len(scan["poly"]))
c2.metric("Candidate pairs", len(scan["candidates"]))
c3.metric("Verified opportunities", len(opportunities))
c4.metric("Portfolio", f"${10_000 - sum(x['capital'] for x in st.session_state.portfolio):,.0f}")
st.caption(f"Sources: {scan['sources'][0]} · {scan['sources'][1]}")

st.subheader("Verified opportunities")
if not opportunities:
    st.warning("No contracts clear the current safety and profitability gates. Lower the match threshold only for investigation, not execution.")
    st.stop()

rows = []
for i, item in enumerate(opportunities):
    rows.append({"#": i + 1, "Event": item.pair.kalshi.title, "Trade": item.label.replace("Buy ", ""), "Net ROI": f"{item.roi:.2f}%", "AI match": f"{item.verification.equivalence_score}%", "Liquidity": f"${min(item.pair.kalshi.liquidity, item.pair.polymarket.liquidity):,.0f}"})
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

index = st.selectbox("Inspect an opportunity", range(len(opportunities)), format_func=lambda i: f"#{i + 1} — {opportunities[i].pair.kalshi.title}")
item = opportunities[index]
left, right = st.columns([1.25, 1])
with left:
    st.subheader("Arbitrage execution plan")
    a, b = st.columns(2)
    a.metric(f"Kalshi {item.side_a}", f"${item.pair.kalshi.yes_price if item.side_a == 'YES' else item.pair.kalshi.no_price:.3f}")
    b.metric(f"Polymarket {item.side_b}", f"${item.pair.polymarket.yes_price if item.side_b == 'YES' else item.pair.polymarket.no_price:.3f}")
    x, y, z = st.columns(3)
    x.metric("Gross cost", f"${item.gross_cost:.3f}")
    y.metric("Fees + slippage", f"${item.estimated_costs:.3f}")
    z.metric("Net ROI", f"{item.roi:.2f}%")
    if st.button("Execute paper trade", type="primary"):
        payout = position_size / item.net_cost
        st.session_state.portfolio.append({"trade": item.label, "capital": position_size, "payout": payout, "profit": payout - position_size, "roi": item.roi})
        st.success(f"Paper trade executed: ${position_size:,.2f} allocated · estimated profit ${payout - position_size:,.2f}")
with right:
    st.subheader("Market equivalence")
    st.markdown(f"<div class='verdict'>{item.verification.verdict} · {item.verification.equivalence_score}% confidence</div>", unsafe_allow_html=True)
    for check, status in item.verification.checks.items():
        st.write(f"{'✅' if status == 'MATCH' else '⚠️' if status == 'REVIEW' else '❌'} {check}: **{status}**")
    st.caption(item.verification.short_reason)
    if item.verification.critical_differences:
        st.error(" ".join(item.verification.critical_differences))

st.divider()
st.subheader("Ask EventArb AI")
question = st.text_input("Ask in English or Hindi", placeholder="Abhi sabse safe arbitrage kaunsa hai?")
if question:
    st.info(explain_best(question, opportunities))

if st.session_state.portfolio:
    st.subheader("Paper portfolio")
    portfolio = pd.DataFrame(st.session_state.portfolio)
    st.dataframe(portfolio.style.format({"capital": "${:,.2f}", "payout": "${:,.2f}", "profit": "${:,.2f}", "roi": "{:.2f}%"}), use_container_width=True, hide_index=True)
