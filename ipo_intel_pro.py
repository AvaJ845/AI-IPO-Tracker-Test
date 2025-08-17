import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
from datetime import datetime, timedelta
import json

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="IPO Intel Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# CUSTOM STYLING
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
    .high-potential { border-left-color: #dc3545 !important; }
    .medium-potential { border-left-color: #ffc107 !important; }
    .sidebar-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# SEC EDGAR HELPER FUNCTIONS
# --------------------------------------------------
SEC_HEADERS = {
    "User-Agent": "IPOIntelPro (dwayne.jackson@example.com)"
}

def search_sec_filings(ticker_or_name: str, form_types: list = ["S-1", "S-1/A", "F-1"]) -> pd.DataFrame:
    """
    Search SEC EDGAR for IPO-related filings for a company by ticker or name.
    """
    try:
        url = f"https://data.sec.gov/submissions/CIK{ticker_or_name}.json"
        r = requests.get(url, headers=SEC_HEADERS, timeout=10)
        if r.status_code != 200:
            return pd.DataFrame()

        data = r.json()
        filings = data.get("filings", {}).get("recent", {})
        df = pd.DataFrame(filings)
        if df.empty:
            return df

        # Filter only IPO-related filings
        df = df[df["form"].isin(form_types)]
        df["filingDate"] = pd.to_datetime(df["filingDate"])
        return df[["form", "filingDate", "accessionNumber"]].sort_values("filingDate", ascending=False)

    except Exception as e:
        st.error(f"Error fetching SEC filings: {e}")
        return pd.DataFrame()

# --------------------------------------------------
# IPO TRACKER CLASS
# --------------------------------------------------
class AIIPOTracker:
    def __init__(self):
        self.notes = {}

    def risk_score(self, revenue_growth, debt_ratio):
        """
        Simplified scoring model: revenue growth (higher better), debt ratio (lower better).
        """
        score = (revenue_growth * 0.6) - (debt_ratio * 0.4)
        if score > 20:
            return "Low Risk", "🟢"
        elif score > 0:
            return "Medium Risk", "🟡"
        else:
            return "High Risk", "🔴"

# --------------------------------------------------
# MAIN APP
# --------------------------------------------------
def main():
    st.markdown('<div class="main-header">📈 IPO Intel Pro</div>', unsafe_allow_html=True)

    tracker = AIIPOTracker()

    st.sidebar.markdown("### 🔎 Search IPO")
    company = st.sidebar.text_input("Enter company name or ticker", "ARM")
    show_sec = st.sidebar.checkbox("Show SEC Filings", True)

    # Demo company metrics (replace with real financial API later)
    revenue_growth = np.random.randint(-10, 40)  # %
    debt_ratio = np.random.uniform(0.1, 1.5)    # debt/equity

    risk, symbol = tracker.risk_score(revenue_growth, debt_ratio)

    # --------------------------------------------------
    # COMPANY SNAPSHOT
    # --------------------------------------------------
    st.subheader(f"Company Overview: {company}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Revenue Growth (YoY)", f"{revenue_growth}%")
    col2.metric("Debt/Equity Ratio", f"{debt_ratio:.2f}")
    col3.metric("Risk Score", f"{symbol} {risk}")

    # --------------------------------------------------
    # SEC FILINGS
    # --------------------------------------------------
    if show_sec:
        st.subheader("📑 SEC IPO Filings")
        filings = search_sec_filings("0000320193")  # Example: Apple CIK for demo
        if not filings.empty:
            st.dataframe(filings)
        else:
            st.info("No IPO-related filings found yet.")

    # --------------------------------------------------
    # IPO CALENDAR (Mock Example)
    # --------------------------------------------------
    st.subheader("🗓️ Upcoming IPO Calendar")
    ipo_data = pd.DataFrame({
        "Company": ["Company A", "Company B", "Company C"],
        "Expected Date": [
            datetime.now() + timedelta(days=5),
            datetime.now() + timedelta(days=14),
            datetime.now() + timedelta(days=30),
        ],
        "Expected Range": ["$20-$25", "$12-$15", "$40-$45"]
    })
    st.table(ipo_data)

    # --------------------------------------------------
    # PEER COMPARISON (Mock Example)
    # --------------------------------------------------
    st.subheader("📊 Peer Comparison (Price-to-Sales Ratio)")
    peers = pd.DataFrame({
        "Company": ["IPO Target", "Competitor 1", "Competitor 2"],
        "P/S Ratio": [12, 8, 15]
    })
    fig = px.bar(peers, x="Company", y="P/S Ratio", color="Company", title="Peer Valuation")
    st.plotly_chart(fig, use_container_width=True)

    # --------------------------------------------------
    # NOTES
    # --------------------------------------------------
    st.subheader("📝 Your Notes")
    note = st.text_area("Write your personal thoughts or strategy here:")
    if st.button("Save Note"):
        tracker.notes[company] = note
        st.success("Note saved for this session!")

    # --------------------------------------------------
    # EDUCATIONAL INSIGHT
    # --------------------------------------------------
    with st.expander("📘 Investor Education"):
        st.markdown("""
        - **S-1 Form**: The official IPO filing with the SEC, includes business model, risks, and financials.  
        - **Lock-up Period**: Usually 90–180 days when insiders cannot sell their shares after IPO.  
        - **Pricing Range**: Indicates what bankers expect the shares to sell for, but can change.  
        - **Risk Tip**: High revenue growth with low debt often signals a stronger IPO candidate.  
        """)

# --------------------------------------------------
# RUN APP
# --------------------------------------------------
if __name__ == "__main__":
    main()