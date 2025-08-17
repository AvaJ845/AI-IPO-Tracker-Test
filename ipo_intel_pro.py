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

try:
import yfinance as yf
YF_AVAILABLE = True
except Exception:
YF_AVAILABLE = False

st.set_page_config(
page_title=‘IPO Intel Pro’,
page_icon=‘🎯’,
layout=‘wide’,
initial_sidebar_state=‘expanded’
)

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
    .small-muted { 
        color: #666; 
        font-size: 0.9rem; 
    }
    .filing-alert {
        background: #e7f3ff;
        padding: 0.8rem;
        border-radius: 6px;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
    .unavailable {
        color: #999;
        font-style: italic;
    }
</style>

“””, unsafe_allow_html=True)

SEC_HEADERS = {
‘User-Agent’: ‘IPOIntelPro/1.0 (contact: your.email@example.com)’
}

@st.cache_data(ttl=60 * 60)
def fetch_sec_company_map() -> pd.DataFrame:
try:
url = ‘https://www.sec.gov/files/company_tickers.json’
r = requests.get(url, headers=SEC_HEADERS, timeout=20)
r.raise_for_status()
raw = r.json()
rows = []
for _, v in raw.items():
rows.append({
‘ticker’: v.get(‘ticker’, ‘’),
‘name’: v.get(‘title’, ‘’),
‘cik_str’: int(v.get(‘cik_str’, 0))
})
df = pd.DataFrame(rows)
df[‘cik’] = df[‘cik_str’].apply(lambda x: str(x).zfill(10))
return df
except Exception as e:
st.error(f’Failed to load SEC company mapping: {e}’)
return pd.DataFrame()

def find_cik(query: str, company_map: pd.DataFrame) -> Optional[str]:
q = (query or ‘’).strip().upper()
if not q or company_map is None or company_map.empty:
return None

```
hit = company_map[company_map['ticker'].str.upper() == q]
if not hit.empty:
    return hit.iloc[0]['cik']

hit = company_map[company_map['name'].str.upper().str.contains(q, na=False)]
if not hit.empty:
    return hit.iloc[0]['cik']

return None
```

@st.cache_data(ttl=15 * 60)
def fetch_company_filings(cik10: str, form_types: List[str]) -> pd.DataFrame:
try:
url = f’https://data.sec.gov/submissions/CIK{cik10}.json’
r = requests.get(url, headers=SEC_HEADERS, timeout=20)
if r.status_code != 200:
return pd.DataFrame()
data = r.json()
filings = data.get(‘filings’, {}).get(‘recent’, {})
if not filings:
return pd.DataFrame()

```
    df = pd.DataFrame(filings)
    if df.empty:
        return df

    df = df[df['form'].isin(form_types)].copy()
    if df.empty:
        return df

    df['filingDate'] = pd.to_datetime(df['filingDate'], errors='coerce')
    df['cik'] = str(data.get('cik', '')).zfill(10)
    df['company_name'] = data.get('name', '')
    
    def _archive_link(row):
        cik_no_zeros = str(int(row['cik'])) if re.match(r'^\d+$', str(row['cik'])) else row['cik'].lstrip('0')
        acc_no = str(row['accessionNumber']).replace('-', '')
        primary_doc = row.get('primaryDocument', '')
        if primary_doc:
            return f'https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/{acc_no}/{primary_doc}'
        return f'https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/{acc_no}/{row["accessionNumber"]}-index.html'

    if 'primaryDocument' not in df.columns:
        df['primaryDocument'] = ''

    df['Link'] = df.apply(_archive_link, axis=1)
    cols = ['form', 'filingDate', 'accessionNumber', 'primaryDocument', 'Link', 'company_name', 'cik']
    return df[cols].sort_values('filingDate', ascending=False)
except Exception as e:
    st.warning(f'Could not fetch filings for CIK {cik10}: {e}')
    return pd.DataFrame()
```

@st.cache_data(ttl=5 * 60)
def fetch_sec_current_ipo_feed() -> pd.DataFrame:
def _parse_atom(url: str) -> List[dict]:
try:
res = requests.get(url, headers=SEC_HEADERS, timeout=20)
res.raise_for_status()
root = ET.fromstring(res.content)
ns = {‘atom’: ‘http://www.w3.org/2005/Atom’}
items = []
for entry in root.findall(‘atom:entry’, ns):
title = entry.findtext(‘atom:title’, default=’’, namespaces=ns)
link_el = entry.find(‘atom:link’, ns)
link = link_el.get(‘href’) if link_el is not None else ‘’
updated = entry.findtext(‘atom:updated’, default=’’, namespaces=ns)
summary = entry.findtext(‘atom:summary’, default=’’, namespaces=ns)
items.append({
‘Title’: title,
‘Updated’: updated,
‘Link’: link,
‘Summary’: summary
})
return items
except Exception:
return []

```
feeds = []
base = 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&owner=exclude&count=100&output=atom&type='
for f in ['S-1', 'S-1/A', 'F-1']:
    try:
        feeds.extend(_parse_atom(base + requests.utils.quote(f)))
    except Exception:
        pass

if not feeds:
    return pd.DataFrame()

df = pd.DataFrame(feeds)
df['Form'] = df['Title'].str.extract(r'(S-1\/A|S-1|F-1)', expand=False)
df['Company'] = df['Title'].str.replace(r'Form (S-1\/A|S-1|F-1)\s*[-–]\s*', '', regex=True)
df['Updated'] = pd.to_datetime(df['Updated'], errors='coerce')
df = df.sort_values('Updated', ascending=False).reset_index(drop=True)
return df
```

def get_live_ipo_metrics() -> Dict:
feed_df = fetch_sec_current_ipo_feed()

```
if feed_df.empty:
    return {
        'total_filings_30d': 0,
        's1_filings': 0,
        's1a_amendments': 0,
        'f1_filings': 0,
        'recent_companies': [],
        'filing_trend': 'Unavailable'
    }

thirty_days_ago = datetime.now() - timedelta(days=30)
recent_filings = feed_df[feed_df['Updated'] >= thirty_days_ago]

form_counts = recent_filings['Form'].value_counts()

recent_companies = recent_filings['Company'].unique()[:10].tolist()

if len(recent_filings) > 20:
    trend = 'High Activity'
elif len(recent_filings) > 10:
    trend = 'Moderate Activity'
elif len(recent_filings) > 0:
    trend = 'Low Activity'
else:
    trend = 'No Recent Activity'

return {
    'total_filings_30d': len(recent_filings),
    's1_filings': form_counts.get('S-1', 0),
    's1a_amendments': form_counts.get('S-1/A', 0),
    'f1_filings': form_counts.get('F-1', 0),
    'recent_companies': recent_companies,
    'filing_trend': trend
}
```

def get_company_sec_status(company_name: str, company_map: pd.DataFrame) -> Dict:
cik = find_cik(company_name, company_map)
if not cik:
return {‘status’: ‘No CIK found’, ‘filings’: [], ‘has_recent_filing’: False}

```
filings = fetch_company_filings(cik, ['S-1', 'S-1/A', 'F-1'])

if filings.empty:
    return {'status': 'No IPO filings', 'filings': [], 'has_recent_filing': False}

one_year_ago = datetime.now() - timedelta(days=365)
recent = filings[filings['filingDate'] >= one_year_ago]

return {
    'status': 'IPO filings found',
    'filings': filings,
    'has_recent_filing': not recent.empty,
    'latest_filing': filings.iloc[0] if not filings.empty else None
}
```

class AIIPOTracker:
def **init**(self):
self.company_map = fetch_sec_company_map()
self.ai_companies = self._load_ai_companies_with_sec()
self.component_companies = self._load_component_companies()
self.investment_firms = self._load_investment_firms()
self.live_metrics = get_live_ipo_metrics()

```
def _load_ai_companies_with_sec(self) -> pd.DataFrame:
    base_companies = [
        'Lambda Labs', 'OpenAI', 'Anthropic', 'Databricks', 'Scale AI',
        'CoreWeave', 'Hugging Face', 'Cohere', 'Stability AI', 'Runway',
        'Character.AI', 'Perplexity', 'Midjourney', 'Notion', 'Canva',
        'Discord', 'Reddit', 'Stripe', 'Epic Games', 'Ramp'
    ]
    
    sectors = [
        'AI Infrastructure', 'AI Foundation Models', 'AI Foundation Models', 'Data & Analytics', 'AI Training Data',
        'AI Infrastructure', 'AI Platform', 'AI Foundation Models', 'AI Content Generation', 'AI Content Generation',
        'AI Consumer Apps', 'AI Search', 'AI Content Generation', 'Productivity AI', 'Design AI',
        'Communication AI', 'Social Platform', 'Payments AI', 'Gaming AI', 'Fintech AI'
    ]
    
    sec_status_data = []
    for company in base_companies:
        status = get_company_sec_status(company, self.company_map)
        sec_status_data.append({
            'Company': company,
            'SEC_Status': status['status'],
            'Has_Recent_Filing': status['has_recent_filing'],
            'Latest_Filing_Date': status['latest_filing']['filingDate'].strftime('%Y-%m-%d') if status.get('latest_filing') is not None else 'None'
        })
    
    sec_df = pd.DataFrame(sec_status_data)
    
    data = {
        'Company': base_companies,
        'Sector': sectors,
        'Public_Status': ['Private'] * len(base_companies)
    }
    
    df = pd.DataFrame(data)
    df = df.merge(sec_df, on='Company', how='left')
    
    def calc_ipo_score(row):
        if row['Has_Recent_Filing']:
            return 90
        elif row['SEC_Status'] == 'IPO filings found':
            return 60
        else:
            return 30
    
    df['IPO_Potential_Score'] = df.apply(calc_ipo_score, axis=1)
    return df

def _load_component_companies(self) -> pd.DataFrame:
    data = {
        'Company': ['NVIDIA', 'AMD', 'Intel', 'Qualcomm', 'Broadcom', 'TSMC', 'ASML', 'Applied Materials'],
        'Sector': ['GPU/AI Chips', 'CPU/GPU', 'CPU/AI Chips', 'Mobile AI', 'Networking Chips', 'Semiconductor Foundry', 'Semiconductor Equipment', 'Semiconductor Equipment'],
        'Stock_Symbol': ['NVDA', 'AMD', 'INTC', 'QCOM', 'AVGO', 'TSM', 'ASML', 'AMAT'],
        'AI_Exposure': ['Very High', 'High', 'Medium', 'High', 'Medium', 'Very High', 'High', 'Medium']
    }
    
    df = pd.DataFrame(data)
    
    if YF_AVAILABLE:
        market_caps = []
        for ticker in df['Stock_Symbol']:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                market_cap = info.get('marketCap', 0)
                market_caps.append(market_cap / 1e9)
            except:
                market_caps.append(0)
        df['Market_Cap_B'] = market_caps
    else:
        df['Market_Cap_B'] = [0] * len(df)
    
    return df

def _load_investment_firms(self) -> pd.DataFrame:
    data = {
        'Firm': ['Andreessen Horowitz', 'Sequoia Capital', 'Accel', 'NEA', 'Lightspeed', 'General Catalyst', 'Greylock Partners'],
        'Type': ['VC', 'VC', 'VC', 'VC', 'VC', 'VC', 'VC'],
        'AI_Focus_Companies': [
            'OpenAI, Character.AI, Databricks',
            'Stripe, Notion, ByteDance', 
            'Scale AI, Databricks, UiPath',
            'Perplexity, Character.AI, Databricks',
            'Stability AI, Midjourney, Epic Games',
            'Notion, Canva, Ramp',
            'Discord, Figma, Ramp'
        ],
        'Est_AUM_B': [35, 85, 25, 24, 18, 12, 8]
    }
    return pd.DataFrame(data)
```

def get_peer_data(ticker: str) -> Dict:
if not YF_AVAILABLE or not ticker.strip():
return {
‘price’: ‘Unavailable’,
‘market_cap’: ‘Unavailable’,
‘pe_ratio’: ‘Unavailable’,
‘revenue_growth’: ‘Unavailable’
}

```
try:
    stock = yf.Ticker(ticker.strip().upper())
    info = stock.info
    
    return {
        'price': f'${info.get("currentPrice", 0):.2f}' if info.get('currentPrice') else 'Unavailable',
        'market_cap': f'${info.get("marketCap", 0)/1e9:.1f}B' if info.get('marketCap') else 'Unavailable',
        'pe_ratio': f'{info.get("trailingPE", 0):.1f}' if info.get('trailingPE') else 'Unavailable',
        'revenue_growth': f'{info.get("revenueGrowth", 0)*100:.1f}%' if info.get('revenueGrowth') else 'Unavailable'
    }
except:
    return {
        'price': 'Unavailable',
        'market_cap': 'Unavailable',
        'pe_ratio': 'Unavailable', 
        'revenue_growth': 'Unavailable'
    }
```

def main():
st.markdown(’<h1 class="main-header">🎯 IPO Intel Pro</h1>’, unsafe_allow_html=True)
st.markdown(’<p style="text-align: center; font-size: 1.2rem; color: #666; margin-bottom: 2rem;">Live SEC EDGAR IPO Intelligence Platform</p>’, unsafe_allow_html=True)

```
with st.spinner('Loading live SEC data...'):
    tracker = AIIPOTracker()

st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
st.sidebar.header('🔍 Company Lookup')
query = st.sidebar.text_input('Ticker or Company Name', placeholder='e.g., AAPL or Apple')

if query:
    cik = find_cik(query, tracker.company_map)
    if cik:
        st.sidebar.success(f'✅ Found CIK: {cik}')
    else:
        st.sidebar.warning('❌ Company not found in SEC database')

st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
st.sidebar.header('🚨 Live IPO Alerts')
if tracker.live_metrics['recent_companies']:
    st.sidebar.write('**Recent Filers:**')
    for company in tracker.live_metrics['recent_companies'][:5]:
        st.sidebar.markdown(f'• {company}')
else:
    st.sidebar.write('No recent IPO activity')
st.sidebar.markdown('</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    '📊 Live Dashboard',
    '🏢 AI Companies', 
    '🔧 Components',
    '💰 Investors',
    '📑 SEC Filings'
])

with tab1:
    st.subheader('Live IPO Market Intelligence')
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'''
        <div class="metric-container">
            <h3>Filings (30d)</h3>
            <h2>{tracker.live_metrics["total_filings_30d"]}</h2>
            <div class="small-muted">Live SEC data</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="metric-container">
            <h3>S-1 Forms</h3>
            <h2>{tracker.live_metrics["s1_filings"]}</h2>
            <div class="small-muted">New IPO registrations</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="metric-container">
            <h3>Amendments</h3>
            <h2>{tracker.live_metrics["s1a_amendments"]}</h2>
            <div class="small-muted">S-1/A updates</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'''
        <div class="metric-container">
            <h3>Market Activity</h3>
            <h2>{tracker.live_metrics["filing_trend"]}</h2>
            <div class="small-muted">Filing trend</div>
        </div>
        ''', unsafe_allow_html=True)

    st.subheader('AI Companies SEC Filing Status')
    
    status_counts = tracker.ai_companies['SEC_Status'].value_counts()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title='Companies by SEC Filing Status'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig2 = px.scatter(
            tracker.ai_companies,
            x='Company',
            y='IPO_Potential_Score', 
            color='Has_Recent_Filing',
            title='IPO Potential vs Recent SEC Filings',
            color_discrete_map={True: 'red', False: 'lightblue'}
        )
        fig2.update_layout(height=400, xaxis_tickangle=45)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader('Latest SEC IPO Filings (All Companies)')
    live_feed = fetch_sec_current_ipo_feed()
    if not live_feed.empty:
        recent_feed = live_feed.head(10)[['Updated', 'Form', 'Company', 'Link']]
        recent_feed['Updated'] = recent_feed['Updated'].dt.strftime('%Y-%m-%d %H:%M')
        st.dataframe(recent_feed, use_container_width=True)
    else:
        st.info('No recent IPO filings available')

with tab2:
    st.subheader('AI Companies with Live SEC Data')
    
    col1, col2 = st.columns(2)
    with col1:
        show_only_filers = st.checkbox('Show only companies with SEC filings')
    with col2:
        min_score = st.slider('Minimum IPO Potential Score', 0, 100, 0)
    
    filtered_df = tracker.ai_companies.copy()
    if show_only_filers:
        filtered_df = filtered_df[filtered_df['SEC_Status'] != 'No CIK found']
    filtered_df = filtered_df[filtered_df['IPO_Potential_Score'] >= min_score]
    
    for idx, company in filtered_df.iterrows():
        status_color = '🟢' if company['Has_Recent_Filing'] else '🟡' if company['SEC_Status'] == 'IPO filings found' else '🔴'
        
        st.markdown(f'''
        <div class="company-card">
            <h3>{status_color} {company["Company"]} ({company["Sector"]})</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0;">
                <div><strong>IPO Score:</strong> {company["IPO_Potential_Score"]}/100</div>
                <div><strong>SEC Status:</strong> {company["SEC_Status"]}</div>
                <div><strong>Recent Filing:</strong> {"Yes" if company["Has_Recent_Filing"] else "No"}</div>
                <div><strong>Latest Filing:</strong> {company["Latest_Filing_Date"]}</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.subheader('Complete AI Companies Data')
    display_cols = ['Company', 'Sector', 'IPO_Potential_Score', 'SEC_Status', 'Has_Recent_Filing', 'Latest_Filing_Date']
    st.dataframe(filtered_df[display_cols], use_container_width=True)

with tab3:
    st.subheader('AI Component & Infrastructure Companies')
    
    if YF_AVAILABLE and tracker.component_companies['Market_Cap_B'].sum() > 0:
        fig = px.bar(
            tracker.component_companies.sort_values('Market_Cap_B', ascending=True),
            x='Market_Cap_B',
            y='Company',
            color='AI_Exposure', 
            title='Live Market Capitalization by AI Exposure',
            orientation='h',
            labels={'Market_Cap_B': 'Market Cap ($B)'}
        )
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info('Live market cap data unavailable (install yfinance for live data)')
    
    st.dataframe(tracker.component_companies, use_container_width=True)

with tab4:
    st.subheader('Major AI Investment Firms')
    
    fig = px.bar(
        tracker.investment_firms,
        x='Firm',
        y='Est_AUM_B',
        color='Type',
        title='Estimated Assets Under Management',
        labels={'Est_AUM_B': 'AUM ($B)'}
    )
    fig.update_layout(height=500, xaxis_tickangle=45)
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(tracker.investment_firms, use_container_width=True)

with tab5:
    st.subheader('SEC EDGAR Filing Tools')

    st.markdown('### Company Filing Lookup')
    
    if query:
        cik = find_cik(query, tracker.company_map)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric('Query', query)
        with col2:
            st.metric('CIK', cik or 'Not found')
        with col3:
            st.metric('Status', '✅ Found' if cik else '❌ Not found')
        
        if cik:
            filings = fetch_company_filings(cik, ['S-1', 'S-1/A', 'F-1'])
            
            if not filings.empty:
```