import streamlit as st
import pandas as pd

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

# 2. DATI FISSI
budgets_fisso = {
    "GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5,
    "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5,
    "MATTEO": 166.5, "NICHOLAS": 113.0
}

# 3. CARICAMENTO SIDEBAR
st.sidebar.header("📂 Database Lega")
f_scontri = st.sidebar.file_uploader("1. Scontri Diretti", type="csv")
f_punti = st.sidebar.file_uploader("2. Punti Totali", type="csv")
f_rose = st.sidebar.file_uploader("3. Rose Attuali", type="csv")
f_vinc = st.sidebar.file_uploader("4. Vincoli 26/27", type="csv")

def pulisci_nomi(df, col):
    if df is None or col not in df.columns: return df
    mappa = {"NICO FABIO": "NICHOLAS", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI", "MATTEO STEFANO": "MATTEO"}
    df[col] = df[col].astype(str).str.strip().str.upper().replace(mappa)
    return df

def carica(f):
    if f is None: return None
    try:
        df = pd.read_csv(f, sep=',', skip_blank_lines=True, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df.dropna(how='all')
    except:
        return None

d_sc = carica(f_scontri)
d_pt = carica(f_punti)
d_rs = carica(f_rose)
d_vn = carica(f_vinc)

# 4. LOGICA TAB
if any([d_sc is not None, d_pt is not None, d_rs is not None, d_vn is not None]):
    tabs = st.tabs(["🏆 Classifiche", "📊 Economia", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

    # TAB 0: CLASSIFICHE
    with tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🔥 Scontri Diretti")
            if d_sc is not None:
                d_sc = pulisci_nomi(d_sc, 'Giocatore')
                st.dataframe(d_sc, hide_index=True, use_container_width=True)
            else: st.info("Carica 'scontridiretti.csv'")
        with c2:
            st.subheader("🎯 Punti Totali")
            if d_pt is not None:
                d_pt = pulisci_nomi(d_pt, 'Giocatore')
                for c in ['Punti Totali', 'Media', 'Distacco']:
                    if c in d_pt.columns:
                        d_pt[c] = d_pt[c].astype(str).str.replace(',', '.').pipe(pd.to_numeric, errors='coerce').fillna(0)
                st.dataframe(d_pt[['Posizione', 'Giocatore', 'Punti Totali', 'Media']], hide_index=True, use_container_width=True)
            else: st.info("Carica 'classificapunti.csv'")

    # TAB 1: ECONOMIA
    with tabs[1]:
        st.subheader("💰 Bilancio Rose")
        if d_rs is not None:
            f_col = [c for c in d_rs.
