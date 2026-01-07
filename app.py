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

# 2. BUDGET FISSI (FEBBRAIO)
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
        return pd.read_csv(file_input, sep=',', skip_blank_lines=True, encoding='utf-8-sig')
    if os.path.exists(nome_locale):
        df = pd.read_csv(nome_locale, sep=',', skip_blank_lines=True, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df.dropna(how='all')
    return None

# 4. CARICAMENTO DATI
st.sidebar.header("📂 Stato Database")
f_sc = carica_dati(st.sidebar.file_uploader("Scontri", type="csv"), "scontridiretti.csv")
f_pt = carica_dati(st.sidebar.file_uploader("Punti", type="csv"), "classificapunti.csv")
f_rs = carica_dati(st.sidebar.file_uploader("Rose", type="csv"), "rose_complete.csv")
f_vn = carica_dati(st.sidebar.file_uploader("Vincoli", type="csv"), "vincoli.csv")

# Feedback rapido in sidebar
st.sidebar.write("✅ Scontri" if f_sc is not None else "❌ Scontri")
st.sidebar.write("✅ Punti" if f_pt is not None else "❌ Punti")
st.sidebar.write("✅ Rose" if f_rs is not None else "❌ Rose")
st.sidebar.write("✅ Vincoli" if f_vn is not None else "❌ Vincoli")

# 5. LOGICA TAB
if any([f_sc is not None, f_pt is not None, f_rs is not None, f_vn is not None]):
    tabs = st.tabs(["🏆 Classifiche", "📊 Economia", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

    with tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            if f_sc is not None:
                st.subheader("🔥 Scontri Diretti")
                f_sc = pulisci_nomi(f_sc, 'Giocatore')
                st.dataframe(f_sc, hide_index=True, use_container_width=True)
        with c2:
            if f_pt is not None:
                st.subheader("🎯 Punti Totali")
                f_pt = pulisci_nomi(f_pt, 'Giocatore')
                for c in ['Punti Totali', 'Media']:
                    if c in f_pt.columns:
                        f_pt[c] = f_pt[c].astype(str).str.replace(',', '.').pipe(pd.to_numeric, errors='coerce').fillna(0)
                st.dataframe(f_pt[['Posizione', 'Giocatore', 'Punti Totali', 'Media']], hide_index=True, use_container_width=True)

    with tabs[1]:
        if f_rs is not None:
            st.subheader("💰 Bilancio Rose")
            f_col = next((c for c in f_rs.columns if 'fantasquadra' in c.lower()), f_rs.columns[0])
            p_col = next((c for c in f_rs.columns if 'prezzo' in c.lower()), f_rs.columns[-1])
            f_rs = pulisci_nomi(f_rs, f_col)
            f_rs[p_col] = pd.to_numeric(f_rs[p_col], errors='coerce').fillna(0)
            eco = f_rs.groupby(f_col)[p_col].sum().reset_index()
            eco.columns = ['Fantasquadra', 'Costo Rosa']
            eco['Extra'] = eco['Fantasquadra'].map(budgets_fisso).fillna(0)
            eco['Totale'] = (eco['Costo Rosa'] + eco['Extra']).astype(int)
            st.dataframe(eco.sort_values('Totale', ascending=False), hide_index=True, use_container_width=True)

    with tabs[2]:
        if f_rs is not None:
            st.subheader("📋 Analisi Strategica")
            cx, cy = st.columns([1.5, 1])
            f_col = next((c for c in f_rs.columns if 'fantasquadra' in c.lower()), f_rs.columns[0])
            n_col = next((c for c in f_rs.columns if 'nome' in c.lower()), f_rs.columns[1])
