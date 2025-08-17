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

# Configure page

st.set_page_config(
page_title=“IPO Intel Pro”,
page_icon=“🎯”,
layout=“wide”,
initial_sidebar_state=“expanded”
)

# Custom CSS for better styling

st.markdown(”””

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

“””, unsafe_allow_html=True)

class AIIPOTracker:
def **init**(self):
self.ai_companies = self._load_ai_companies()
self.component_companies = self._load_component_companies()
self.investment_firms = self._load_investment_firms()

```
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
        "Company": [
            "NVIDIA", "AMD", "Intel", "Qualcomm", "Broadcom",
            "TSMC", "ASML", "Applied Materials", "Lam Research", "KLA Corporation",
            "Synopsys", "Cadence", "Marvell", "Xilinx", "Lattice Semi",
            "Super Micro Computer", "Pure Storage", "Snowflake", "MongoDB", "Palantir"
        ],
        "Sector": [
            "GPU/AI Chips", "CPU/GPU", "CPU/AI Chips", "Mobile AI", "Networking Chips",
            "Semiconductor Foundry", "Semiconductor Equipment", "Semiconductor Equipment", "Semiconductor Equipment", "Semiconductor Equipment",
            "EDA Software", "EDA Software", "Data Infrastructure", "FPGA", "FPGA",
            "AI Servers", "Data Storage", "Data Cloud", "Database", "Data Analytics"
        ],
        "Market_Cap_B": [
            3000, 240, 200, 190, 620,
            450, 380, 120, 90, 60,
            85, 75, 65, 0, 8,
            45, 12, 60, 24, 55
        ],
        "Stock_Symbol": [
            "NVDA", "AMD", "INTC", "QCOM", "AVGO",
            "TSM", "ASML", "AMAT", "LRCX", "KLAC",
            "SNPS", "CDNS", "MRVL", "XLNX", "LSCC",
            "SMCI", "PSTG", "SNOW", "MDB", "PLTR"
        ],
        "AI_Exposure": [
            "Very High", "High", "Medium", "High", "Medium",
            "Very High", "High", "Medium", "Medium", "Medium",
            "Medium", "Medium", "Medium", "High", "Medium",
            "Very High", "High", "High", "Medium", "High"
        ],
        "IPO_Status": [
            "Public", "Public", "Public", "Public", "Public",
            "Public", "Public", "Public", "Public", "Public",
            "Public", "Public", "Public", "Acquired by AMD", "Public",
            "Public", "Public", "Public", "Public", "Public"
        ]
    }
    return pd.DataFrame(data)

def _load_investment_firms(self) -> pd.DataFrame:
    """Load major investment firms active in AI"""
    data = {
        "Firm": [
            "Andreessen Horowitz", "Sequoia Capital", "Accel", "NEA", "Lightspeed",
            "General Catalyst", "Greylock Partners", "Benchmark", "Khosla Ventures", "Founders Fund",
            "Index Ventures", "Spark Capital", "Coatue", "Tiger Global", "Insight Partners",
            "General Atlantic", "Silver Lake", "KKR", "Blackstone", "Apollo"
        ],
        "Type": [
            "VC", "VC", "VC", "VC", "VC",
            "VC", "VC", "VC", "VC", "VC",
            "VC", "VC", "Hedge Fund/VC", "Hedge Fund/VC", "Growth Equity",
            "Growth Equity", "Private Equity", "Private Equity", "Private Equity", "Private Equity"
        ],
        "AI_Investments": [
            "OpenAI, Character.AI, Databricks", "Stripe, Notion, ByteDance", "Scale AI, Databricks, UiPath", "Perplexity, Character.AI, Databricks", "Stability AI, Midjourney, Epic Games",
            "Notion, Canva, Ramp", "Discord, Figma, Ramp", "Uber, Discord, Snapchat", "OpenAI, Anthropic, Scale AI", "Ramp, Stripe, SpaceX",
            "Notion, Scale AI, Canva", "Discord, Anthropic, Perplexity", "Stability AI, Runway, Character.AI", "Stripe, Notion, ByteDance", "Databricks, Scale AI, UiPath",
            "Snapchat, ByteDance, Epic Games", "Databricks, Snowflake, MongoDB", "Databricks, ByteDance, Epic Games", "Bumble, Ancestry, Thomson Reuters", "Yahoo, Verizon Media, Cox Automotive"
        ],
        "AUM_B": [
            35, 85, 25, 24, 18,
            12, 8, 3, 15, 12,
            8, 6, 25, 65, 80,
            85, 102, 504, 975, 548
        ],
        "Notable_AI_Exits": [
            "Instagram, Skype, GitHub", "WhatsApp, YouTube, PayPal", "Facebook, Spotify, Dropbox", "Salesforce, Workday, Tableau", "Snapchat, Epic Games, AppDynamics",
            "Stripe, Canva, Airbnb", "LinkedIn, Facebook, Instagram", "Uber, Twitter, Snapchat", "Tesla, SpaceX, Square", "Facebook, SpaceX, Stripe",
            "Skype, MySQL, Red Hat", "Twitter, Tumblr, Warby Parker", "ByteDance, Spotify, Uber", "Facebook, LinkedIn, Spotify", "Twitter, Shopify, Wix",
            "Uber, Airbnb, Snapchat", "Skype, Alibaba, Airbnb", "ByteDance, Epic Games, AppDynamics", "Bumble, Refinitiv, Ancestry", "Yahoo, Caesars, ADT"
        ]
    }
    return pd.DataFrame(data)

def calculate_ipo_readiness_score(self, company_data: Dict) -> Dict:
    """Calculate comprehensive IPO readiness score"""
    score = 0
    factors = {}
    
    # Revenue factor (30% weight)
    revenue = company_data.get("Revenue_Est_M", 0)
    if revenue >= 1000:
        revenue_score = 30
    elif revenue >= 500:
        revenue_score = 25
    elif revenue >= 100:
        revenue_score = 15
    else:
        revenue_score = 5
    
    score += revenue_score
    factors["Revenue"] = revenue_score
    
    # Valuation factor (25% weight)
    valuation = company_data.get("Last_Valuation_B", 0)
    if valuation >= 10:
        valuation_score = 25
    elif valuation >= 5:
        valuation_score = 20
    elif valuation >= 1:
        valuation_score = 15
    else:
        valuation_score = 5
    
    score += valuation_score
    factors["Valuation"] = valuation_score
    
    # Funding stage factor (20% weight)
    stage = company_data.get("Funding_Stage", "")
    if "Series D" in stage or "Series E" in stage or "Private" in stage:
        stage_score = 20
    elif "Series C" in stage:
        stage_score = 15
    elif "Series B" in stage:
        stage_score = 10
    else:
        stage_score = 5
    
    score += stage_score
    factors["Funding_Stage"] = stage_score
    
    # Company age factor (15% weight)
    founded = company_data.get("Founded_Year", 2023)
    age = 2025 - founded
    if age >= 10:
        age_score = 15
    elif age >= 5:
        age_score = 12
    elif age >= 3:
        age_score = 8
    else:
        age_score = 3
    
    score += age_score
    factors["Company_Age"] = age_score
    
    # Employee count factor (10% weight)
    employees = company_data.get("Employees", 0)
    if employees >= 2000:
        emp_score = 10
    elif employees >= 500:
        emp_score = 8
    elif employees >= 100:
        emp_score = 5
    else:
        emp_score = 2
    
    score += emp_score
    factors["Employees"] = emp_score
    
    return {"total_score": score, "factors": factors}
```

def main():
st.markdown(’<h1 class="main-header">🎯 IPO Intel Pro</h1>’, unsafe_allow_html=True)
st.markdown(’<p style="text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 2rem;">Advanced AI & Technology IPO Intelligence Platform</p>’, unsafe_allow_html=True)

```
# Initialize tracker
tracker = AIIPOTracker()

# Sidebar filters
st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
st.sidebar.header("🔍 Filters")

# Company type filter
company_types = st.sidebar.multiselect(
    "Company Types",
    ["AI Companies", "Component Companies", "Investment Firms"],
    default=["AI Companies"]
)

# IPO potential filter
ipo_potential = st.sidebar.slider(
    "Minimum IPO Potential Score",
    0, 100, 50
)

# Valuation filter
min_valuation = st.sidebar.number_input(
    "Minimum Valuation ($B)",
    0.0, 100.0, 0.0, 0.1
)

st.sidebar.markdown("</div>", unsafe_allow_html=True)

# Main dashboard tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🏢 AI Companies", "🔧 Components", "💰 Investors"])

with tab1:
    st.subheader("IPO Market Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    high_potential = tracker.ai_companies[tracker.ai_companies["IPO_Potential_Score"] >= 80]
    medium_potential = tracker.ai_companies[
        (tracker.ai_companies["IPO_Potential_Score"] >= 50) & 
        (tracker.ai_companies["IPO_Potential_Score"] < 80)
    ]
    
    with col1:
        st.markdown(
            f'<div class="metric-container"><h3>High IPO Potential</h3><h2>{len(high_potential)}</h2></div>',
            unsafe_allow_html=True
        )
    
    with col2:
        st.markdown(
            f'<div class="metric-container"><h3>Medium IPO Potential</h3><h2>{len(medium_potential)}</h2></div>',
            unsafe_allow_html=True
        )
    
    with col3:
        total_valuation = tracker.ai_companies["Last_Valuation_B"].sum()
        st.markdown(
            f'<div class="metric-container"><h3>Total Market Value</h3><h2>${total_valuation:.1f}B</h2></div>',
            unsafe_allow_html=True
        )
    
    with col4:
        avg_valuation = tracker.ai_companies["Last_Valuation_B"].mean()
        st.markdown(
            f'<div class="metric-container"><h3>Avg Valuation</h3><h2>${avg_valuation:.1f}B</h2></div>',
            unsafe_allow_html=True
        )
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # IPO Potential Distribution
        fig = px.histogram(
            tracker.ai_companies,
            x="IPO_Potential_Score",
            nbins=10,
            title="IPO Potential Score Distribution",
            labels={"count": "Number of Companies", "IPO_Potential_Score": "IPO Potential Score"}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Sector breakdown
        sector_counts = tracker.ai_companies["Sector"].value_counts()
        fig = px.pie(
            values=sector_counts.values,
            names=sector_counts.index,
            title="Companies by Sector"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Valuation vs IPO Potential Scatter
    fig = px.scatter(
        tracker.ai_companies,
        x="Last_Valuation_B",
        y="IPO_Potential_Score",
        size="Revenue_Est_M",
        color="Sector",
        hover_name="Company",
        title="Valuation vs IPO Potential",
        labels={
            "Last_Valuation_B": "Valuation ($B)",
            "IPO_Potential_Score": "IPO Potential Score"
        }
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("AI Companies Analysis")
    
    # Filter data
    filtered_companies = tracker.ai_companies[
        (tracker.ai_companies["IPO_Potential_Score"] >= ipo_potential) &
        (tracker.ai_companies["Last_Valuation_B"] >= min_valuation)
    ].sort_values("IPO_Potential_Score", ascending=False)
    
    # Display companies
    for idx, company in filtered_companies.iterrows():
        potential_class = ""
        if company["IPO_Potential_Score"] >= 80:
            potential_class = "high-potential"
        elif company["IPO_Potential_Score"] >= 50:
            potential_class = "medium-potential"
        
        st.markdown(f"""
        <div class="company-card {potential_class}">
            <h3>{company["Company"]} ({company["Sector"]})</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0;">
                <div><strong>Valuation:</strong> ${company["Last_Valuation_B"]:.1f}B</div>
                <div><strong>IPO Score:</strong> {company["IPO_Potential_Score"]}/100</div>
                <div><strong>Revenue Est:</strong> ${company["Revenue_Est_M"]}M</div>
                <div><strong>Employees:</strong> {company["Employees"]:,}</div>
                <div><strong>Stage:</strong> {company["Funding_Stage"]}</div>
                <div><strong>Founded:</strong> {company["Founded_Year"]}</div>
            </div>
            <div><strong>Key Investors:</strong> {company["Key_Investors"]}</div>
            <div style="margin-top: 0.5rem;"><strong>Recent News:</strong> {company["Recent_News"]}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed data table
    st.subheader("Detailed Company Data")
    st.dataframe(
        filtered_companies[["Company", "Sector", "Last_Valuation_B", "IPO_Potential_Score", 
                          "Revenue_Est_M", "Employees", "Funding_Stage"]],
        use_container_width=True
    )

with tab3:
    st.subheader("AI Component & Infrastructure Companies")
    
    # Component companies analysis
    st.write("These public companies provide critical infrastructure for AI:")
    
    # Filter by AI exposure
    ai_exposure_filter = st.selectbox(
        "Filter by AI Exposure",
        ["All", "Very High", "High", "Medium"]
    )
    
    if ai_exposure_filter != "All":
        filtered_components = tracker.component_companies[
            tracker.component_companies["AI_Exposure"] == ai_exposure_filter
        ]
    else:
        filtered_components = tracker.component_companies
    
    # Market cap analysis
    fig = px.bar(
        filtered_components.sort_values("Market_Cap_B", ascending=True),
        x="Market_Cap_B",
        y="Company",
        color="AI_Exposure",
        title="Market Capitalization by AI Exposure",
        labels={"Market_Cap_B": "Market Cap ($B)"},
        orientation="h"
    )
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)
    
    # Component companies table
    st.dataframe(filtered_components, use_container_width=True)

with tab4:
    st.subheader("Major Investment Firms in AI")
    
    # Investment firm analysis
    fig = px.scatter(
        tracker.investment_firms,
        x="AUM_B",
        y=tracker.investment_firms.index,
        size="AUM_B",
        color="Type",
        hover_name="Firm",
        title="Investment Firms by Assets Under Management",
        labels={"AUM_B": "Assets Under Management ($B)"}
    )
    fig.update_layout(height=600)
    st.plotly_chart(fig, use_container_width=True)
    
    # Investment firms table
    st.dataframe(tracker.investment_firms, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
**IPO Intel Pro** - Advanced AI & Technology IPO Intelligence Platform

**Disclaimer:** This dashboard provides estimated data for analysis purposes. 
Investment decisions should be based on official filings and professional advice.
Data sources include public filings, news reports, and industry estimates.

*Built for sophisticated investors tracking the next generation of public offerings.*
""")
```

if **name** == “**main**”:
main()