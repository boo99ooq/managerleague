import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# CSS STYLE
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .status-box { padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 2px solid; }
    .search-card { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; color: #1a1a1a !important; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .stDataFrame { border: 1px solid #e6e9ef; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONE DI PULIZIA ---
def super_clean(name):
    if not isinstance(name, str): return ""
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    name = name.upper().strip()
    mapping = {
        'LAUTARO': 'MARTINEZ L', 'MARTINEZ L': 'MARTINEZ L',
        'THURAM M': 'THURAM', 'NICO PAZ': 'PAZ N',
        'PIO ESPOSITO': 'ESPOSITO FP', 'ZAMBO ANGUISSA': 'ANGUISSA'
    }
    clean = re.sub(r'[^A-Z0-9]', '', name)
    for k, v in mapping.items():
        if k.replace(' ','') in clean: return re.sub(r'[^A-Z0-9]', '', v)
    return clean

# --- CARICAMENTO DATI ---
def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        # Carichiamo con encoding flessibile
        df = pd.read_csv(f, engine='python', encoding='latin1', on_bad_lines='skip')
        df.columns = [c.strip() for c in df.columns] # Pulizia spazi nei nomi colonne
        if is_quot: 
            df['Key'] = df['Nome'].apply(super_clean)
        return df
    except: return None

f_rs, f_vn, f_pt, f_sc = ld("rose_complete.csv"), ld("vincoli.csv"), ld("classificapunti.csv"), ld("scontridiretti.csv")
f_qt = ld("quotazioni.csv", is_quot=True)

# LOGICA DI MATCHING
if f_rs is not None and f_qt is not None:
    f_rs['Key'] = f_rs['Nome'].apply(super_clean)
    # Evitiamo duplicati nelle quotazioni durante il merge
    f_qt_unique = f_qt.drop_duplicates(subset=['Key'])
    f_rs = pd.merge(f_rs, f_qt_unique[['Key', 'Qt.A']], on='Key', how='left').fillna({'Qt.A': 0})
    f_rs = f_rs.rename(columns={'Qt.A': 'Quotazione'})

# --- MAIN APP ---
st.title("⚽ MUYFANTAMANAGER GOLDEN V8.2")
t = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "✂️ TAGLI", "🕵️ MERCATO", "🛠️ DATA CHECK"])

# --- TAB 2: ROSE (RIATTAUATA E CORRETTA) ---
with t[2]:
    st.subheader("🏃 GESTIONE ROSE")
    if f_rs is not None:
        # Cerchiamo la colonna corretta per la squadra (gestisce minuscole/maiuscole)
        col_sq = next((c for c in f_rs.columns if c.lower() in ['fantasquadra', 'squadra']), f_rs.columns[1])
        
        lista_squadre = sorted(f_rs[col_sq].unique())
        sq_scelta = st.selectbox("SELEZIONA FANTASQUADRA", lista_squadre, key="select_sq_rose")
        
        # Filtro dati
        df_view = f_rs[f_rs[col_sq] == sq_scelta].copy()
        
        # Formattazione per ruolo
        def color_ruolo(val):
            color = '#ffffff'
            if str(val).startswith('P'): color = '#FCE4EC'
            elif str(val).startswith('D'): color = '#E8F5E9'
            elif str(val).startswith('C'): color = '#E3F2FD'
            elif str(val).startswith('A'): color = '#FFFDE7'
            return f'background-color: {color}'

        # Mostriamo le colonne principali
        cols_to_show = ['Ruolo', 'Nome', 'Prezzo', 'Quotazione']
        # Verifichiamo che le colonne esistano prima di mostrarle
        available_cols = [c for c in cols_to_show if c in df_view.columns]
        
        st.dataframe(
            df_view[available_cols].style.applymap(color_ruolo, subset=['Ruolo'] if 'Ruolo' in available_cols else []),
            use_container_width=True, 
            hide_index=True
        )
        
        # Riassunto rapido
        st.markdown(f"**Totale Giocatori:** {len(df_view)} | **Costo Rosa:** {int(df_view['Prezzo'].sum())} cr")
    else:
        st.error("File 'rose_complete.csv' non trovato o vuoto.")

# --- TAB 7: DATA CHECK (UTILE PER CAPIRE COSA NON VA) ---
with t[7]:
    st.subheader("🛠️ DATA CHECK")
    if f_rs is not None:
        c1, c2 = st.columns(2)
        with c1:
            st.write("🔍 **Nomi Colonne Rilevati:**")
            st.write(list(f_rs.columns))
            mancanti = f_rs[f_rs['Quotazione'] == 0]
            st.warning(f"Giocatori con quotazione 0: {len(mancanti)}")
            st.dataframe(mancanti[['Nome', col_sq]], hide_index=True)
        with c2:
            st.write("👯 **Doppioni:**")
            dup = f_rs[f_rs.duplicated(subset=['Nome'], keep=False)]
            st.dataframe(dup[['Nome', col_sq]], hide_index=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 RICERCA")
    if f_rs is not None:
        p_cerca = st.multiselect("GIOCATORE", sorted(f_rs['Nome'].astype(str).unique()))
        for p in p_cerca:
            row = f_rs[f_rs['Nome'] == p].iloc[0]
            st.markdown(f'<div class="search-card"><b>{p}</b><br>VAL: {int(row["Prezzo"])} | QUOT: {int(row["Quotazione"])}</div>', unsafe_allow_html=True)
