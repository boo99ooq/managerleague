import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")

# 2. STILE: SFONDO VERDE CHIARO E TESTI SCURI
def apply_custom_style():
    st.markdown(
        """
        <style>
        .stApp { background-color: #e8f5e9; }
        [data-testid="stSidebar"] { background-color: #c8e6c9 !important; }
        h1, h2, h3, h4, h5, p, label, span { color: #1b5e20 !important; }
        h1 { text-align: center; font-weight: 800; padding-bottom: 20px; }
        .stTabs, .stDataFrame, .stTable {
            background-color: #ffffff !important;
            padding: 10px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

apply_custom_style()

st.title("⚽ Centro Direzionale Fantalega")

# 3. BUDGET FISSI
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5,
    "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113.0
}

# 4. SIDEBAR PER INSERIMENTO FILE
st.sidebar.header("📂 Caricamento Dati")
f_scontri = st.sidebar.file_uploader("Classifica Scontri", type="csv")
f_punti = st.sidebar.file_uploader("Classifica Punti", type="csv")
f_rose = st.sidebar.file_uploader("Rose Attuali", type="csv")
f_vinc = st.sidebar.file_uploader("Vincoli 2026/27", type="csv")

# Funzioni di pulizia
def pulisci_nomi(df, col):
    mappa = {
        "NICO FABIO": "NICHOLAS", "NICHO": "NICHOLAS", 
        "DANI ROBI": "DANI ROBI", "MATTEO STEFANO": "MATTEO"
    }
    df[col] = df[col].astype(str).str.strip().str.upper().replace(mappa)
    return df

def carica_csv(file):
    if file is None: return None
    file.seek(0)
    df = pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    return df

df_scontri = carica_csv(f_scontri)
df_punti_tot = carica_csv(f_punti)
df_rose = carica_csv(f_rose)
df_vincoli = carica_csv(f_vinc)

# 5. LOGICA APPLICAZIONE
if df_rose is not None:
    df_rose = df_rose.dropna(subset=['Fantasquadra', 'Nome'])
    df_rose = pulisci_nomi(df_rose, 'Fantasquadra')
    # Prezzi interi senza decimali
    df_rose['Prezzo'] = pd.to_numeric(df_rose['Prezzo'], errors='coerce').fillna(0).astype(int)

    tabs = st.tabs(["🏆 Class
