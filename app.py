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

# 4. SIDEBAR PER STATO DATABASE
st.sidebar.header("📂 Stato Database")
f_sc_up = st.sidebar.file_uploader("Aggiorna Scontri", type="csv")
d_sc = carica_dati(f_sc_up, ["scontridiretti.csv"])
st.sidebar.write("✅ Scontri" if d_sc is not None else "❌ scontridiretti.csv")

f_pt_up = st.sidebar.file_uploader("Aggiorna Punti", type="csv")
d_pt = carica_dati(f_pt_up, ["classificapunti.csv"])
st.sidebar.write("✅ Punti" if d_pt is not None else "❌ classificapunti.csv")

f_rs_up = st.sidebar.file_uploader("Aggiorna Rose", type="csv")
d_rs = carica_dati(f_rs_up, ["rose_complete.csv"])
st.sidebar.write("✅ Rose" if d_rs is not None else "❌ rose_complete.csv")

f_vn_up = st.sidebar.file_uploader("Aggiorna Vincoli", type="csv")
d_vn = carica_dati(f_vn_up, ["vincoli.csv"])
st.sidebar.write("✅ Vincoli" if d_vn is not None else "❌ vincoli.csv")

# 5. LOGICA TAB
if any([d_sc is not None, d_pt is not None, d_rs is not None, d_vn is not None]):
    tabs = st.tabs(["🏆 Classifiche", "📊 Economia", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

    # TAB CLASSIFICHE
    with tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🔥 Scontri Diretti")
            if d_sc is not None:
                d_sc = pulisci_nomi(d_sc, 'Giocatore')
                st.dataframe(d_sc, hide_index=True, use_container_width=True)
        with c2:
            st.subheader("🎯 Punti Totali")
            if d_pt is not None:
                d_pt = pulisci_nomi(d_pt, 'Giocatore')
                for c in ['Punti Totali', 'Media', 'Distacco']:
                    if c in d_pt.columns:
                        d_pt[c] = d_pt[c].astype(str).str.replace(',', '.').pipe(pd.to_numeric, errors='coerce').fillna(0)
                st.dataframe(d_pt[['Posizione', 'Giocatore', 'Punti Totali', 'Media']], hide_index=True, use_container_width=True)

    # TAB ECONOMIA
    with tabs[1]:
        st.subheader("💰 Bilancio Rose")
        if d_rs is not None:
            f_col = next((c for c in d_rs.columns if 'fantasquadra' in c.lower()), d_rs.columns[0])
            p_col = next((c for c in d_rs.columns if 'prezzo' in c.lower()), d_rs.columns[-1])
            d_rs = pulisci_nomi(d_rs, f_col)
            d_rs[p_col] = pd.to_numeric(d_rs[p_col], errors='coerce').fillna(0)
            eco = d_rs.groupby(f_col)[p_col].sum().reset_index()
            eco.columns = ['Fantasquadra', 'Costo Rosa']
            eco['Extra'] = eco['Fantasquadra'].map(budgets_fisso).fillna(0)
            eco['Totale'] = (eco['Costo Rosa'] + eco['Extra']).astype(int)
            st.dataframe(eco.sort_values('Totale', ascending=False), hide_index=True, use_container_width=True)

    # TAB STRATEGIA
    with tabs[2]:
        st.subheader("📋 Analisi Strategica")
        if d_rs is not None:
            cx, cy = st.columns([1.5, 1])
            f_col = next((c for c in d_rs.columns if 'fantasquadra' in c.lower()), d_rs.columns[0])
            n_col = next((c for c in d_rs.columns if 'nome' in c.lower()), d_rs.columns[1])
            p_col = next((c for c in d_rs.columns if 'prezzo' in c.lower()), d_rs.columns[-1])
            r_col = next((c for c in d_rs.columns if 'ruolo' in c.lower()), 'Ruolo')
            with cx:
                ord_r = ['Portiere', 'Difensore', 'Centrocampista', 'Attaccante', 'Giovani']
                piv = d_rs.pivot_table(index=f_col, columns=r_col, values=n_col, aggfunc='count').fillna(0).astype(int)
                st.dataframe(piv[[r for r in ord_r if r in piv.columns]], use_container_width=True)
            with cy:
                st.write("**💎 Top Player:**")
                idx = d_rs.groupby(f_col)[p_col].idxmax()
                st.dataframe(d_rs.loc[idx, [f_col, n_col, p_col]].sort_values(p_col, ascending=False), hide_index=True)

    # TAB ROSE
    with tabs[3]:
        st.subheader("🏃 Dettaglio Rose")
        if d_rs is not None:
            f_col = next((c for c in d_rs.columns if 'fantasquadra' in c.lower()), d_rs.columns[0])
            n_col = next((c for c in
