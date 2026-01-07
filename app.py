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

def carica_dati(file_input, nome_locale):
    if file_input is not None:
        df = pd.read_csv(file_input, sep=',', skip_blank_lines=True, encoding='utf-8-sig')
    elif os.path.exists(nome_locale):
        df = pd.read_csv(nome_locale, sep=',', skip_blank_lines=True, encoding='utf-8-sig')
    else: return None
    df.columns = df.columns.str.strip()
    return df.dropna(how='all')

# 4. CARICAMENTO DATI
st.sidebar.header("📂 Stato File")
f_sc = carica_dati(st.sidebar.file_uploader("Scontri", type="csv"), "scontridiretti.csv")
f_pt = carica_dati(st.sidebar.file_uploader("Punti", type="csv"), "classificapunti.csv")
f_rs = carica_dati(st.sidebar.file_uploader("Rose", type="csv"), "rose_complete.csv")
f_vn = carica_dati(st.sidebar.file_uploader("Vincoli", type="csv"), "vincoli.csv")

# Indicatori sidebar
st.sidebar.write("✅ Scontri" if f_sc is not None else "❌ scontridiretti.csv")
st.sidebar.write("✅ Punti" if f_pt is not None else "❌ classificapunti.csv")
st.sidebar.write("✅ Rose" if f_rs is not None else "❌ rose_complete.csv")
st.sidebar.write("✅ Vincoli" if f_vn is not None else "❌ vin
