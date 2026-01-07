import streamlit as st
import pandas as pd
import os

# 1. SETUP
st.set_page_config(page_title="Lega", layout="wide")
st.markdown("<style>.stApp{background-color:#e8f5e9;} .stTabs, .stDataFrame{background-color:white; border-radius:10px; padding:5px;}</style>", unsafe_allow_html=True)

st.title("⚽ Centro Direzionale Fantalega")

# 2. BUDGET
budgets = {"GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5, "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5, "MATTEO": 166.5, "NICHOLAS": 113.0}

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
        df.columns = df.columns.str.strip()
        return df
    return None

# 4. DATI
st.sidebar.header("📂 Menu")
f_sc = get_df(st.sidebar.file_uploader("Scontri", type="csv"), "scontridiretti.csv")
f_pt = get_df(st.sidebar.file_uploader("Punti", type="csv"), "classificapunti.csv")
f_rs = get_df(st.sidebar.file_uploader("Rose", type="csv"), "rose_complete.csv")
f_vn = get_df(st.sidebar.file_uploader("Vincoli", type="csv"), "vincoli.csv")

# 5. APP
if any([f_sc is not None, f_pt is not None, f_rs is not None, f_vn is not None]):
    t = st.tabs(["🏆 Classifica", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])
