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

# 2. DATI FISSI
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
    """Cerca il file nella cartella locale e lo carica"""
    if os.path.exists(nome_file):
        try:
            # Prova vari separatori per sicurezza
            df = pd.read_csv(nome_file, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            return df.dropna(how='all')
        except: return None
    return None

# Caricamento Automatico dei file (assicurati che i nomi siano esatti su GitHub)
d_sc = carica_auto("scontridiretti.csv")
d_pt = carica_auto("classificapunti.csv")
d_rs = carica_auto("rose_complete.csv")
d_vn = carica_auto("vincoli.csv")

# Sidebar Status
st.sidebar.header("📂 Stato Database")
st.sidebar.write("Scontri:", "✅" if d_sc is not None else "❌")
st.sidebar.write("Punti:", "✅" if d_pt is not None else "❌")
st.sidebar.write("Rose:", "✅" if d_rs is not None else "❌")
st.sidebar.write("Vincoli:", "✅" if d_vn is not None else "❌")

# 4. LOGICA TAB
if any([d_sc is not None, d_pt is not None, d_rs is not None, d_vn is not None]):
    tabs = st.tabs(["🏆 Classifiche", "📊 Economia", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

    # --- TAB CLASSIFICHE ---
    with tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🔥 Scontri Diretti")
            if d_sc is not None:
                d_sc = pulisci_nomi(d_sc, 'Giocatore')
                st.dataframe(d_sc, hide_index=True, use_container_width=True)
            else: st.info("File 'scontridiretti.csv' non trovato.")
        with c2:
            st.subheader("🎯 Punti Totali")
            if d_pt is not None:
                d_pt = pulisci_nomi(d_pt, 'Giocatore')
                for c in ['Punti Totali', 'Media']:
                    if c in d_pt.columns:
                        d_pt[c] = d_pt[c].astype(str).str.replace(',', '.').pipe(pd.to_numeric, errors='coerce').fillna(0)
                st.dataframe(d_pt[['Posizione', 'Giocatore', 'Punti Totali', 'Media']], hide_index=True, use_container_width=True)
            else: st.info("File 'classificapunti.csv' non trovato.")

    # --- TAB ECONOMIA ---
    with tabs[1]:
        st.subheader("💰 Bilancio Rose")
        if d_rs is not None:
            f_col = next((c for c in d_rs.columns if 'fantasquadra' in c.lower() or 'squadra' in c.lower()), d_rs.columns[0])
            p_col = next((c for c in d_rs.columns if 'prezzo' in c.lower() or 'costo' in c.lower()), d_rs.columns[-1])
            d_rs = pulisci_nomi(d_rs, f_col)
            d_rs[p_col] = pd.to_numeric(d_rs[p_col].astype(str).str.replace(',','.'), errors='coerce').fillna(0)
            
            eco = d_rs.groupby(f_col)[p_col].sum().reset_index()
            eco.columns = ['Fantasquadra', 'Costo Rosa']
            eco['Extra'] = eco['Fantasquadra'].str.upper().map(budgets_fisso).fillna(0)
            eco['Totale'] = (eco['Costo Rosa'] + eco['Extra']).astype(int)
            st.dataframe(eco.sort_values('Totale', ascending=False), hide_index=True, use_
