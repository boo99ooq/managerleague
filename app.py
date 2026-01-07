import streamlit as st
import pandas as pd
import os

# 1. CONFIGURAZIONE E STILE
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

def apply_style():
    st.markdown("""
        <style>
        .stApp { background-color: #e8f5e9; }
        [data-testid="stSidebar"] { background-color: #c8e6c9 !important; }
        h1, h2, h3, h4, h5, p, label, span { color: #1b5e20 !important; font-family: 'Segoe UI', sans-serif; }
        h1 { text-align: center; font-weight: 800; color: #2e7d32 !important; padding-bottom: 20px; }
        .stTabs, .stDataFrame, .stTable {
            background-color: #ffffff !important;
            padding: 10px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        </style>
    """, unsafe_allow_html=True)

apply_style()
st.title("⚽ Centro Direzionale Fantalega")

# 2. BUDGET FISSI
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5,
    "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113.0
}

# 3. FUNZIONI DI SUPPORTO
def pulisci_nomi(df, col):
    if df is None or col not in df.columns: return df
    mappa = {"NICO FABIO": "NICHOLAS", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI", "MATTEO STEFANO": "MATTEO"}
    df[col] = df[col].astype(str).str.strip().str.upper().replace(mappa)
    return df

def carica_dati(file_input, nomi_possibili):
    if file_input is not None:
        return pd.read_csv(file_input, sep=',', skip_blank_lines=True, encoding='utf-8-sig')
    for nome in nomi_possibili:
        if os.path.exists(nome):
            df = pd.read_csv(nome, sep=',', skip_blank_lines=True, encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            return df.dropna(how='all')
    return None

# 4. CARICAMENTO DATI
f_sc_up = st.sidebar.file_uploader("Aggiorna Scontri", type="csv")
d_sc = carica_dati(f_sc_up, ["s
