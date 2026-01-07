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

# 2. DATI FISSI BUDGET
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

def carica_auto(nome_file):
    if os.path.exists(nome_file):
        try:
            # Carica file gestendo separatori diversi (, o ;)
            df = pd.read_csv(nome_file, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            return df.dropna(how='all')
        except: return None
    return None

# Caricamento Automatico dei file da GitHub
d_sc = carica_auto("scontridiretti.csv")
d_pt = carica_auto("classificapunti.csv")
d_rs = carica_auto("rose_complete.csv")
d_vn = carica_auto("vincoli.csv")

# Sidebar Status
st.sidebar.header("📂 Database Lega")
st.sidebar.write("1. Scontri:", "✅" if d_sc is not None else "❌")
st.sidebar.write("2. Punti:", "✅" if d_pt is not None else "❌")
st.sidebar.write("3. Rose:", "✅" if d_rs is not None else "❌")
st.sidebar.write("4. Vincoli:", "✅" if d_vn is not None else "❌")

# 4. LOGICA TAB
if any(
