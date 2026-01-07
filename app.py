import streamlit as st
import pandas as pd
import os

# 1. SETUP E STILE
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #e8f5e9; }
    [data-testid="stSidebar"] { background-color: #c8e6c9 !important; }
    h1, h2, h3, h4, h5, p, label, span { color: #1b5e20 !important; font-family: 'Segoe UI', sans-serif; }
    h1 { text-align: center; font-weight: 800; color: #2e7d32 !important; }
    .stTabs, .stDataFrame, .stTable {
        background-color: #ffffff !important; padding: 10px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ Centro Direzionale Fantalega")

# 2. BUDGET FISSI
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5,
    "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113.0
}

# 3. FUNZIONI
def clean_n(df, c):
    if df is None or c not in df.columns: return df
    m = {"NICO FABIO": "NICHOLAS", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI", "MATTEO STEFANO": "MATTEO"}
    df[c] = df[c].astype(str).str.strip().str.upper().replace(m)
    return df

def get_df(up, loc):
    if up: return pd.read_csv(up, sep=',', encoding='utf-8-sig').dropna(how='all')
    if os.path.exists(loc):
        df = pd.read_csv(loc, sep=',', encoding='utf-8-sig').dropna(how='all')
        df.
