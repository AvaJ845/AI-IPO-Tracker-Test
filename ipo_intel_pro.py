import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET

# Optional peer data – handled gracefully if not available
try:
    import yfinance as yf
    YF_AVAILABLE = True
except Exception:
    YF_AVAILABLE = False

# --------------------------------------------------
# Configure page
# --------------------------------------------------
st.set_page_config(
    page_title="IPO Intel Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# Custom CSS
# --------------------------------------------------
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-container {
        background: linear-gradient(90deg, #f0f2f6 0%, #ffffff 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .company-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
        border-left: 4px solid #28a745;
    }
    .high-potential {
        border-left-color: #dc3545 !important;
    }
    .medium-potential {
        border-left-color: #ffc107 !important;
    }
    .sidebar-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .small-muted { color: #666; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# SEC EDGAR – Free endpoints (no API key)
# --------------------------------------------------
SEC_HEADERS = {
    # 👇 Replace with your real email per SEC fair access policy
    "User-Agent": "IPOIntelPro/1.0 (contact: your.email@example.com)"
}

@st.cache_data(ttl=60 * 60)  # cache for 1 hour
def fetch_sec_company_map() -> pd.DataFrame:
    """
    Get SEC's official mapping of tickers/names -> CIK.
    Source: https://www.sec.gov/files/company_tickers.json
    """
    url = "https://www.sec.gov/files/company_tickers.json"
    r = requests.get(url, headers=SEC_HEADERS, timeout=20)
    r.raise_for_status()
    # The JSON is { "0": {...}, "1": {...}, ...}
    raw = r.json()
    rows = []
    for _, v in raw.items():
        rows.append({
            "ticker": v.get("ticker", ""),
            "name": v.get("title", ""),
            "cik_str": int(v.get("cik_str", 0))
        })
    df = pd.DataFrame(rows)
    df["cik"] = df["cik_str"].apply(lambda x: str(x).zfill(10))
    return df

def find_cik(query: str, company_map: pd.DataFrame) -> Optional[str]:
    """
    Resolve user input (ticker or name) to a 10-digit CIK string.
    Tries exact ticker match, then name contains.
    """
    q = (query or "").strip().upper()
    if not q or company_map is None or company_map.empty:
        return None

    # Exact ticker match
    hit = company_map[company_map["ticker"].str.upper() == q]
    if not hit.empty:
        return hit.iloc[0]["cik"]

    # Name contains (case-insensitive)
    hit = company_map[company_map["name"].str.upper().str.contains(q, na=False)]
    if not hit.empty:
        return hit.iloc[0]["cik"]

    return None

@st.cache_data(ttl=15 * 60)
def fetch_company_filings(cik10: str, form_types: List[str]) -> pd.DataFrame:
    """
    Pull recent filings for a company (via submissions file) and filter for form types.
    https://data.sec.gov/submissions/CIK##########.json
    """
    url = f"https://data.sec.gov/submissions/CIK{cik10}.json"
    r = requests.get(url, headers=SEC_HEADERS, timeout=20)
    if r.status_code != 200:
        return pd.DataFrame()
    data = r.json()
    filings = data.get("filings", {}).get("recent", {})
    if not filings:
        return pd.DataFrame()

    df = pd.DataFrame(filings)
    if df.empty:
        return df

    df = df[df["form"].isin(form_types)].copy()
    if df.empty:
        return df

    # Clean & build archive links
    df["filingDate"] = pd.to_datetime(df["filingDate"], errors="coerce")
    df["cik"] = str(data.get("cik", "")).zfill(10)
    def _archive_link(row):
        # /Archives/edgar/data/{cik_no_zeros}/{accessionnodashes}/{primaryDocument}
        cik_no_zeros = str(int(row["cik"])) if re.match(r"^\d+$", str(row["cik"])) else row["cik"].lstrip("0")
        acc_no = str(row["accessionNumber"]).replace("-", "")
        primary_doc = row.get("primaryDocument", "")
        if primary_doc:
            return f"https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/{acc_no}/{primary_doc}"
        # Fallback to index
        return f"https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/{acc_no}/{row['accessionNumber']}-index.html"

    if "primaryDocument" not in df.columns:
        df["primaryDocument"] = ""

    df["Link"] = df.apply(_archive_link, axis=1)
    cols = ["form", "filingDate", "accessionNumber", "primaryDocument", "Link"]
    return df[cols].sort_values("filingDate", ascending=False)

@st.cache_data(ttl=5 * 60)
def fetch_sec_current_ipo_feed() -> pd.DataFrame:
    """
    Parse SEC 'Current Filings' Atom feeds for S-1/S-1A/F-1 (near real-time).
    Examples:
      https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=S-1&owner=exclude&count=100&output=atom
      https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=F-1&owner=exclude&count=100&output=atom
    """
    def _parse_atom(url: str) -> List[dict]:
        res = requests.get(url, headers=SEC_HEADERS, timeout=20)
        res.raise_for_status()
        root = ET.fromstring(res.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = []
        for entry in root.findall("atom:entry", ns):
            title = entry.findtext("atom:title", default="", namespaces=ns)
            link_el = entry.find("atom:link", ns)
            link = link_el.get("href") if link_el is not None else ""
            updated = entry.findtext("atom:updated", default="", namespaces=ns)
            summary = entry.findtext("atom:summary", default="", namespaces=ns)
            items.append({
                "Title": title,
                "Updated": updated,
                "Link": link,
                "Summary": summary
            })
        return items

    feeds = []
    base = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&owner=exclude&count=100&output=atom&type="
    for f in ["S-1", "S-1/A", "F-1"]:
        try:
            feeds.extend(_parse_atom(base + requests.utils.quote(f)))
        except Exception:
            pass

    if not feeds:
        return pd.DataFrame()

    df = pd.DataFrame(feeds)
    # Extract company name and form from Title like: "Form S-1 - Example Corp"
    df["Form"] = df["Title"].str.extract(r"(S-1\/A|S-1|F-1)", expand=False)
    df["Company"] = df["Title"].str.replace(r"Form (S-1\/A|S-1|F-1)\s*[-–]\s*", "", regex=True)
    # Convert Updated to datetime
    df["Updated"] = pd.to_datetime(df["Updated"], errors="coerce")
    df = df.sort_values("Updated", ascending=False).reset_index(drop=True)
    return df

# --------------------------------------------------
# Your original data model (kept, trimmed for brevity)
# --------------------------------------------------
class AIIPOTracker:
    def __init__(self):
        self.ai_companies = self._load_ai_companies()
        self.component_companies = self._load_component_companies()
        self.investment_firms = self._load_investment_firms()

    def _load_ai_companies(self) -> pd.DataFrame:
        data = {
            "Company": [
                "Lambda Labs", "OpenAI", "Anthropic", "Databricks", "Scale AI",
                "CoreWeave", "Hugging Face", "Cohere", "Stability AI", "Runway",
                "Character.AI", "Perplexity", "Midjourney", "Notion", "Canva",
                "Figma", "Ramp", "Stripe", "ByteDance (TikTok)", "Epic Games",
                "Discord", "Reddit", "Snapchat", "Uber", "Airbnb"
            ],
            "Sector": [
                "AI Infrastructure", "AI Foundation Models", "AI Foundation Models", "Data & Analytics", "AI Training Data",
                "AI Infrastructure", "AI Platform", "AI Foundation Models", "AI Content Generation", "AI Content Generation",
                "AI Consumer Apps", "AI Search", "AI Content Generation", "Productivity AI", "Design AI",
                "Design Platform", "Fintech AI", "Payments AI", "Social AI", "Gaming AI",
                "Communication AI", "Social Platform", "Social AR/AI", "Mobility AI", "Travel AI"
            ],
            "Last_Valuation_B": [
                4.5, 157.0, 18.4, 43.0, 13.8,
                19.0, 4.5, 6.8, 1.0, 1.5,
                1.0, 2.8, 5.0, 10.0, 40.0,
                20.0, 8.1, 65.0, 220.0, 31.5,
                15.0, 12.0, 25.0, 82.0, 75.0
            ],
            "Funding_Stage": [
                "Series D", "Private", "Series C", "Series I", "Series E",
                "Series C", "Series D", "Series D", "Series A", "Series C",
                "Series A", "Series B", "Private", "Series C", "Series E",
                "Public", "Series D", "Private", "Private", "Private",
                "Private", "Public", "Public", "Public", "Public"
            ],
            "IPO_Potential_Score": [
                95, 30, 60, 85, 70,
                90, 75, 80, 40, 50,
                35, 45, 25, 65, 40,
                0, 60, 20, 15, 25,
                30, 0, 0, 0, 0
            ],
            "Key_Investors": [
                "Nvidia, ARK Invest, Andra Capital", "Microsoft, Khosla Ventures", "Google, Spark Capital", "Andreessen Horowitz, NEA", "Accel, Index Ventures",
                "Nvidia, Magnetar Capital", "Google, Amazon, Nvidia", "Nvidia, Salesforce, AMD", "Lightspeed, Coatue", "Google Ventures, Amplify",
                "Andreessen Horowitz, NEA", "NEA, Databricks Ventures", "Lightspeed Venture Partners", "Sequoia Capital, Index Ventures", "General Catalyst, Bond",
                "Greylock Partners, ICONIQ", "Founders Fund, Stripe", "Sequoia Capital, Allianz X", "General Atlantic, Sequoia", "Sony, Kirkbi",
                "Greylock Partners, Spark Capital", "Fidelity, Tencent", "General Atlantic, Tencent", "Benchmark, Menlo Ventures", "General Atlantic, T. Rowe Price"
            ],
            "Revenue_Est_M": [
                100, 3400, 850, 1600, 500,
                1200, 70, 200, 50, 100,
                80, 150, 200, 300, 1500,
                600, 300, 13500, 80000, 6000,
                600, 1000, 5000, 37000, 8500
            ],
            "Employees": [
                495, 3000, 850, 6000, 1200,
                800, 400, 300, 150, 200,
                120, 280, 100, 2500, 4000,
                1200, 900, 8000, 150000, 4000,
                1000, 2000, 6500, 32000, 6000
            ],
            "Founded_Year": [
                2012, 2015, 2021, 2013, 2016,
                2017, 2016, 2019, 2019, 2018,
                2021, 2022, 2021, 2013, 2013,
                2012, 2019, 2010, 2012, 1991,
                2015, 2005, 2011, 2009, 2008
            ],
            "Recent_News": [
                "Seeking $4-5B funding round ahead of potential IPO by end of 2025",
                "Launched GPT-4 Turbo and exploring enterprise solutions",
                "Raised $6B Series C, focusing on AI safety research",
                "Filed confidentially for IPO, targeting 2024-2025",
                "Expanding government and enterprise AI training solutions",
                "Public since March 2025, trading above IPO price",
                "Launched enterprise AI model marketplace",
                "Raised $500M at $6.8B valuation, hired ex-Meta AI executives",
                "Developing new text-to-video AI models",
                "Raised Series C for AI video generation platform",
                "Focusing on AI character interactions and personalization",
                "Raised $73M Series B for AI-powered search",
                "Maintaining private status, exploring strategic partnerships",
                "Considering public listing within 2-3 years",
                "IPO speculation continues with strong growth metrics",
                "Recently went public in successful IPO",
                "Growing rapidly in AI-powered financial services",
                "Private with no immediate IPO plans",
                "Considering spin-off of TikTok operations",
                "Private with gaming metaverse focus",
                "Considering IPO timing for 2025-2026",
                "Public company with AI initiatives",
                "Public with AR/AI investments",
                "Public mobility platform",
                "Public travel platform"
            ]
        }
        return pd.DataFrame(data)

    def _load_component_companies(self) -> pd.DataFrame:
        data = {
            "Company": ["NVIDIA", "AMD", "Intel", "Qualcomm", "Broadcom"],
            "Sector": ["GPU/AI Chips", "CPU/GPU", "CPU/AI Chips", "Mobile AI", "Networking Chips"],
            "Market_Cap_B": [3000, 240, 200, 190, 620],
            "Stock_Symbol": ["NVDA", "AMD", "INTC", "QCOM", "AVGO"],
            "AI_Exposure": ["Very High", "High", "Medium", "High", "Medium"],
            "IPO_Status": ["Public", "Public", "Public", "Public", "Public"]
        }
        return pd.DataFrame(data)

    def _load_investment_firms(self) -> pd.DataFrame:
        data = {
            "Firm": ["Andreessen Horowitz", "Sequoia Capital", "Accel", "NEA", "Lightspeed"],
            "Type": ["VC", "VC", "VC", "VC", "VC"],
            "AI_Investments": [
                "OpenAI, Character.AI, Databricks",
                "Stripe, Notion, ByteDance",
                "Scale AI, Databricks, UiPath",
                "Perplexity, Character.AI, Databricks",
                "Stability AI, Midjourney, Epic Games"
            ],
            "AUM_B": [35, 85, 25, 24, 18],
            "Notable_AI_Exits": [
                "Instagram, Skype, GitHub",
                "WhatsApp, YouTube, PayPal",
                "Facebook, Spotify, Dropbox",
                "Salesforce, Workday, Tableau",
                "Snapchat, Epic Games, AppDynamics"
            ]
        }
        return pd.DataFrame(data)

# --------------------------------------------------
# Retail-friendly helpers
# --------------------------------------------------
def simple_risk_score(revenue_growth_pct: float, debt_to_equity: float):
    """
    Very simple, transparent score:
    + Revenue growth is positive -> good
    + Lower leverage -> good
    """
    score = (revenue_growth_pct * 0.6) - (debt_to_equity * 40)  # scale D/E into similar magnitude
    if score > 20:
        return "Low", "🟢"
    elif score > 0:
        return "Medium", "🟡"
    return "High", "🔴"

def get_demo_growth_and_leverage(ticker_or_name: str):
    """
    Placeholder for real fundamentals. If yfinance is present and the user typed a ticker,
    try to fetch a rough D/E and revenue trend. Falls back to random demo values.
    """
    # Fallback demo
    demo = {
        "revenue_growth_pct": np.random.randint(-10, 45),
        "debt_to_equity": round(float(np.random.uniform(0.05, 1.5)), 2)
    }

    if not YF_AVAILABLE:
        return demo

    t = (ticker_or_name or "").strip().upper()
    if not t or len(t) > 5:
        return demo  # likely not a simple US ticker

    try:
        ticker = yf.Ticker(t)
        info = ticker.get_info() if hasattr(ticker, "get_info") else {}
        # yfinance sometimes returns None/missing values — guard them
        total_debt = info.get("totalDebt") or 0.0
        total_equity = info.get("totalStockholderEquity") or 0.0
        debt_to_equity = round((total_debt / total_equity), 2) if total_equity else 0.0

        # Try to estimate revenue growth from last 4 quarters vs previous 4 (rough)
        hist = ticker.quarterly_financials if hasattr(ticker, "quarterly_financials") else None
        rev_growth = demo["revenue_growth_pct"]
        if hist is not None and not hist.empty and "Total Revenue" in hist.index:
            rev = hist.loc["Total Revenue"].dropna().astype(float)
            if len(rev) >= 6:
                recent = rev.iloc[:4].mean()
                prior = rev.iloc[4:8].mean() if len(rev) >= 8 else rev.iloc[4:6].mean()
                if prior and prior > 0:
                    rev_growth = round(((recent - prior) / prior) * 100, 1)
        return {
            "revenue_growth_pct": rev_growth,
            "debt_to_equity": debt_to_equity
        }
    except Exception:
        return demo

# --------------------------------------------------
# Main App
# --------------------------------------------------
def main():
    st.markdown('<h1 class="main-header">🎯 IPO Intel Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 2rem;">Advanced AI & Technology IPO Intelligence Platform</p>', unsafe_allow_html=True)

    tracker = AIIPOTracker()

    # Sidebar
    st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.sidebar.header("🔍 Find a Company")
    query = st.sidebar.text_input("Ticker or Company Name", value="ARM", help="Enter a US ticker (e.g., ARM) or part of a company name.")
    st.sidebar.caption("Tip: use a simple ticker for best results with peer metrics.")
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.sidebar.header("🧰 Modules")
    show_sec_company = st.sidebar.checkbox("Company S-1/F-1 Filings", True)
    show_ipo_feed = st.sidebar.checkbox("Live IPO Feed (SEC)", True)
    show_peers = st.sidebar.checkbox("Peer Comparison", True)
    show_notes = st.sidebar.checkbox("Notes", True)
    show_education = st.sidebar.checkbox("Investor Education", True)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard",
        "🏢 AI Companies",
        "🔧 Components",
        "💰 Investors",
        "📑 SEC & IPO Tools"
    ])

    # ---------------- Dashboard
    with tab1:
        st.subheader("IPO Market Overview (Demo metrics)")

        col1, col2, col3, col4 = st.columns(4)
        high_potential = tracker.ai_companies[tracker.ai_companies["IPO_Potential_Score"] >= 80]
        medium_potential = tracker.ai_companies[(tracker.ai_companies["IPO_Potential_Score"] >= 50) & (tracker.ai_companies["IPO_Potential_Score"] < 80)]
        with col1:
            st.markdown(f'<div class="metric-container"><h3>High IPO Potential</h3><h2>{len(high_potential)}</h2></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-container"><h3>Medium IPO Potential</h3><h2>{len(medium_potential)}</h2></div>', unsafe_allow_html=True)
        with col3:
            total_valuation = tracker.ai_companies["Last_Valuation_B"].sum()
            st.markdown(f'<div class="metric-container"><h3>Total Market Value</h3><h2>${total_valuation:.1f}B</h2></div>', unsafe_allow_html=True)
        with col4:
            avg_valuation = tracker.ai_companies["Last_Valuation_B"].mean()
            st.markdown(f'<div class="metric-container"><h3>Avg Valuation</h3><h2>${avg_valuation:.1f}B</h2></div>', unsafe_allow_html=True)

        # Distribution chart
        colA, colB = st.columns(2)
        with colA:
            fig = px.histogram(
                tracker.ai_companies,
                x="IPO_Potential_Score",
                nbins=10,
                title="IPO Potential Score Distribution",
                labels={"count": "Companies"}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        with colB:
            sector_counts = tracker.ai_companies["Sector"].value_counts()
            fig2 = px.pie(
                values=sector_counts.values,
                names=sector_counts.index,
                title="Companies by Sector"
            )
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)

        # Scatter
        fig3 = px.scatter(
            tracker.ai_companies,
            x="Last_Valuation_B",
            y="IPO_Potential_Score",
            size="Revenue_Est_M",
            color="Sector",
            hover_name="Company",
            title="Valuation vs IPO Potential",
            labels={"Last_Valuation_B": "Valuation ($B)", "IPO_Potential_Score": "IPO Score"}
        )
        fig3.update_layout(height=460)
        st.plotly_chart(fig3, use_container_width=True)

    # ---------------- AI Companies
    with tab2:
        st.subheader("AI Companies Analysis")
        st.dataframe(
            tracker.ai_companies[["Company", "Sector", "Last_Valuation_B", "IPO_Potential_Score", "Revenue_Est_M", "Employees", "Funding_Stage"]],
            use_container_width=True
        )

    # ---------------- Components
    with tab3:
        st.subheader("AI Component & Infrastructure Companies")
        fig = px.bar(
            tracker.component_companies.sort_values("Market_Cap_B", ascending=True),
            x="Market_Cap_B",
            y="Company",
            color="AI_Exposure",
            title="Market Capitalization by AI Exposure",
            orientation="h",
            labels={"Market_Cap_B": "Market Cap ($B)"}
        )
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(tracker.component_companies, use_container_width=True)

    # ---------------- Investors
    with tab4:
        st.subheader("Major Investment Firms in AI")
        fig = px.scatter(
            tracker.investment_firms,
            x="AUM_B",
            y=tracker.investment_firms.index,
            size="AUM_B",
            color="Type",
            hover_name="Firm",
            title="Investment Firms by AUM",
            labels={"AUM_B": "Assets Under Management ($B)"}
        )
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(tracker.investment_firms, use_container_width=True)

    # ---------------- SEC & IPO Tools
    with tab5:
        st.subheader("SEC & IPO Tools")

        # Resolve CIK
        st.markdown("### Company Filings Lookup")
        cmap = fetch_sec_company_map()
        cik = find_cik(query, cmap)

        cols_top = st.columns(3)
        with cols_top[0]:
            st.metric("Resolved CIK", cik or "Not found")
        with cols_top[1]:
            st.metric("Input", query)
        with cols_top[2]:
            st.caption("Data: SEC EDGAR (free)")

        # Risk snapshot (simple, retail-friendly)
        st.markdown("### Risk Snapshot (Simple)")
        fundamentals = get_demo_growth_and_leverage(query)
        risk_label, risk_icon = simple_risk_score(
            fundamentals["revenue_growth_pct"], fundamentals["debt_to_equity"]
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Revenue Growth (YoY)", f"{fundamentals['revenue_growth_pct']}%")
        c2.metric("Debt/Equity", f"{fundamentals['debt_to_equity']:.2f}")
        c3.metric("Risk Level", f"{risk_icon} {risk_label}")

        # Company filings (S-1/S-1A/F-1)
        if show_sec_company:
            st.markdown("### 📑 Company S‑1 / S‑1/A / F‑1")
            if cik:
                forms = ["S-1", "S-1/A", "F-1"]
                df_fil = fetch_company_filings(cik, forms)
                if not df_fil.empty:
                    df_show = df_fil.rename(columns={
                        "form": "Form",
                        "filingDate": "Filing Date",
                        "accessionNumber": "Accession",
                        "primaryDocument": "Primary Doc",
                        "Link": "SEC Link"
                    })
                    st.dataframe(df_show, use_container_width=True)
                else:
                    st.info("No IPO-related forms found for this company.")
            else:
                st.warning("Enter a valid US ticker or company name to resolve a CIK.")

        # Live IPO feed (all registrants)
        if show_ipo_feed:
            st.markdown("### 🗓️ Live IPO Feed (SEC Current Filings)")
            feed = fetch_sec_current_ipo_feed()
            if not feed.empty:
                feed_display = feed[["Updated", "Form", "Company", "Link", "Summary"]]
                st.dataframe(feed_display, use_container_width=True)
                st.caption("Feed shows latest S‑1, S‑1/A, and F‑1 across all registrants.")
            else:
                st.info("No recent S‑1/S‑1A/F‑1 entries found in the current feed.")

        # Peer Comparison (user-entered tickers)
        if show_peers:
            st.markdown("### 📊 Peer Comparison (manual tickers)")
            with st.expander("Add up to 4 tickers (e.g., NET, DDOG, SNOW, MDB):"):
                t1, t2, t3, t4 = st.columns(4)
                p1 = t1.text_input("Peer 1", value="")
                p2 = t2.text_input("Peer 2", value="")
                p3 = t3.text_input("Peer 3", value="")
                p4 = t4.text_input("Peer 4", value="")
                tickers = [t for t in [p1, p2, p3, p4] if t.strip()]

            if tickers:
                if not YF_AVAILABLE:
                    st.warning("yfinance not installed; peer metrics disabled. Install with `pip install yfinance`.")
                else:
                    rows = []
                    for t in tickers:
                        try:
                            tk = yf.Ticker(t.strip().upper())
                            info = tk.get_info() if hasattr(tk, "get_info") else {}
                            ps = None
                            # Try to derive P/S ratio if 'priceToSalesTrailing12Months' exists
                            ps = info.get("priceToSalesTrailing12Months")
                            mcap = info.get("marketCap")
                            rev_ttm = info.get("totalRevenue")  # may be annual, depends on source
                            rows.append({
                                "Ticker": t.upper(),
                                "P/S (TTM)": round(ps, 2) if ps else None,
                                "Market Cap": mcap,
                                "Revenue (approx)": rev_ttm
                            })
                        except Exception:
                            rows.append({"Ticker": t.upper(), "P/S (TTM)": None, "Market Cap": None, "Revenue (approx)": None})
                    if rows:
                        dfp = pd.DataFrame(rows)
                        st.dataframe(dfp, use_container_width=True)
                        if "P/S (TTM)" in dfp.columns and dfp["P/S (TTM)"].notna().any():
                            figp = px.bar(
                                dfp.dropna(subset=["P/S (TTM)"]),
                                x="Ticker", y="P/S (TTM)", title="Peer Valuation (P/S, TTM)"
                            )
                            st.plotly_chart(figp, use_container_width=True)

        # Notes & Education
        cols_bottom = st.columns(2)

        if show_notes:
            with cols_bottom[0]:
                st.markdown("### 📝 Your Notes")
                note = st.text_area("Write your personal notes or strategy here:")
                if st.button("Save Note"):
                    st.session_state[f"note_{query}"] = note
                    st.success("Note saved for this session!")
                if f"note_{query}" in st.session_state and st.session_state[f"note_{query}"]:
                    st.info("📌 Saved Note:\n\n" + st.session_state[f"note_{query}"])

        if show_education:
            with cols_bottom[1]:
                st.markdown("### 📘 Investor Education")
                st.markdown("""
- **S‑1 / F‑1**: Registration statements for US (S‑1) or foreign private issuers (F‑1).  
- **S‑1/A**: An amendment to the S‑1, often updating price range, shares, or financials.  
- **Lock‑up Period**: Typically 90–180 days post‑IPO; insiders usually cannot sell.  
- **Quick screen**: Positive revenue growth + lower debt/equity often signals stronger profile.  
- **Always read**: Business model, **Risk Factors**, **MD&A**, and **Use of Proceeds** sections in the filing.
                """)
                st.caption("Data sources: SEC EDGAR free endpoints. Peer data (optional): Yahoo Finance via yfinance.")

    # Footer
    st.markdown("---")
    st.markdown("""
**IPO Intel Pro** — For educational use only. This dashboard surfaces public information to help retail investors
find and review IPOs. Always verify details on **sec.gov** and consider professional advice before investing.
""")

# --------------------------------------------------
# Run App
# --------------------------------------------------
if __name__ == "__main__":
    main()