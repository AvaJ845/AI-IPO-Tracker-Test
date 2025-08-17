import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
from typing import Dict, List, Optional
import time

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
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Main Tracker Class
# --------------------------------------------------
class AIIPOTracker:
    def __init__(self):
        self.ai_companies = self._load_ai_companies()
        self.component_companies = self._load_component_companies()
        self.investment_firms = self._load_investment_firms()

    def _load_ai_companies(self) -> pd.DataFrame:
        """Load AI companies data with IPO potential indicators"""
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
        """Load AI component and infrastructure companies"""
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
        """Load major investment firms active in AI"""
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
# SEC EDGAR API Integration
# --------------------------------------------------
def fetch_recent_ipo_filings(limit: int = 20) -> pd.DataFrame:
    """
    Fetch recent IPO (S-1, F-1) filings from SEC EDGAR
    """
    url = "https://data.sec.gov/submissions/CIK0000320193.json"  # Example: Apple CIK
    headers = {"User-Agent": "IPOIntelProApp/1.0 (contact@example.com)"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        filings = data.get("filings", {}).get("recent", {})
        df = pd.DataFrame(filings)
        if not df.empty:
            df = df[df["form"].isin(["S-1", "F-1"])]
            df = df[["accessionNumber", "form", "filingDate", "primaryDocDescription"]]
            df["Filing Link"] = df["accessionNumber"].apply(
                lambda x: f"https://www.sec.gov/Archives/edgar/data/{data['cik']}/{x.replace('-', '')}/{x}-index.htm"
            )
            return df.head(limit)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching SEC data: {e}")
        return pd.DataFrame()

# --------------------------------------------------
# Main App
# --------------------------------------------------
def main():
    st.markdown('<h1 class="main-header">🎯 IPO Intel Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 2rem;">Advanced AI & Technology IPO Intelligence Platform</p>', unsafe_allow_html=True)

    tracker = AIIPOTracker()

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "🏢 AI Companies", "🔧 Components", "💰 Investors", "📑 SEC Filings"])

    with tab1:
        st.subheader("IPO Market Overview")
        st.write("Key metrics and market trends...")

    with tab2:
        st.subheader("AI Companies Analysis")
        st.dataframe(tracker.ai_companies, use_container_width=True)

    with tab3:
        st.subheader("AI Component & Infrastructure Companies")
        st.dataframe(tracker.component_companies, use_container_width=True)

    with tab4:
        st.subheader("Major Investment Firms in AI")
        st.dataframe(tracker.investment_firms, use_container_width=True)

    with tab5:
        st.subheader("Latest SEC IPO Filings (S-1, F-1)")
        filings_df = fetch_recent_ipo_filings()
        if not filings_df.empty:
            st.dataframe(filings_df, use_container_width=True)
        else:
            st.info("No recent IPO filings found.")

    st.markdown("---")
    st.markdown("""
    **IPO Intel Pro** - Advanced AI & Technology IPO Intelligence Platform  
    **Disclaimer:** Data is for informational purposes only. Use official SEC sources before making investment decisions.  
    """)

# --------------------------------------------------
# Run App
# --------------------------------------------------
if __name__ == "__main__":
    main()