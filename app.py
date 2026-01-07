import streamlit as st
import pandas as pd
import os

# 1. SETUP E STILE
st.set_page_config(page_title="Fantalega", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #e8f5e9; }
    h1, h2, h3, p, label { color: #1b5e20 !important; font-family: sans-serif; }
    .stTabs, .stDataFrame { background-color: white !important; padding: 10px; border-radius: 12px; }
    </style>
""", unsafe_allow_html=True)

st.title("⚽ Centro Direzionale Fantalega")

# 2. DATI FISSI
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
        df.columns = df.columns.str.strip()
        return df
    return None

# 4. CARICAMENTO
st.sidebar.header("📂 Database")
f_sc = get_df(st.sidebar.file_uploader("Scontri", type="csv"), "scontridiretti.csv")
f_pt = get_df(st.sidebar.file_uploader("Punti", type="csv"), "classificapunti.csv")
f_rs = get_df(st.sidebar.file_uploader("Rose", type="csv"), "rose_complete.csv")
f_vn = get_df(st.sidebar.file_uploader("Vincoli", type="csv"), "vincoli.csv")

# 5. LOGICA APPLICAZIONE
if any([f_sc is not None, f_pt is not None, f_rs is not None, f_vn is not None]):
    tabs = st.tabs(["🏆 Classifiche", "
