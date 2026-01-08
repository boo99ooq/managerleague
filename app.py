import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI E STILE
st.set_page_config(page_title="MuyFantaManager PRO", layout="wide")

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .status-box { padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 2px solid; }
    .error-box { background-color: #ffebee; border-color: #c62828; color: #c62828; }
    .stTable { background-color: white; border-radius: 10px; }
    .main-header { color: #1a73e8; font-size: 2.5em; text-align: center; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- MOTORE DI PULIZIA (IL CUORE DELL'APP) ---
def super_clean_engine(name):
    if not isinstance(name, str): return ""
    name = name.replace('ň', 'O').replace('č', 'E').replace('Ã’', 'O').replace('Ãˆ', 'E').replace('Ã¨', 'E')
    n = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper()
    mapping = {
        'NICO PAZ': 'PAZN', 'PAZ N': 'PAZN', 'GABRIEL': 'TIAGOGABRIEL', 
        'MARTINEZ L': 'LMARTINEZ', 'LAUTARO': 'LMARTINEZ', 'THURAM M': 'THURAM'
    }
    clean_raw = "".join(re.findall(r'[A-Z0-9]+', n))
    for k, v in mapping.items():
        if k.replace(' ', '') in clean_raw: return v.replace(' ', '')
    words = re.findall(r'[A-Z0-9]+', n)
    words = [w for w in words if len(w) > 1] or words
    return "".join(sorted(words))

# --- CARICAMENTO DATI ---
def load_data(f):
    if not os.path.exists(f): return None
    try: return pd.read_csv(f, engine='python', encoding='utf-8').applymap(lambda x: x.strip() if isinstance(x, str) else x)
    except: return pd.read_csv(f, engine='python', encoding='latin-1').applymap(lambda x: x.strip() if isinstance(x, str) else x)

# Caricamento file storici
f_rs = load_data("rose_complete.csv")
f_qt = load_data("quotazioni.csv")
f_vn = load_data("vincoli.csv")
f_pt = load_data("classificapunti.csv")
f_sc = load_data("scontridiretti.csv")

# LOGICA DI MATCHING (Standard e Giovani)
map_r = {'Portiere': 'P', 'Difensore': 'D', 'Centrocampista': 'C', 'Attaccante': 'A', 'Giovani': 'A'}
if f_rs is not None and f_qt is not None:
    f_rs['MatchKey'] = f_rs['Nome'].apply(super_clean_engine)
    f_qt['MatchKey'] = f_qt['Nome'].apply(super_clean_engine)
    f_qt_unique = f_qt.drop_duplicates(subset=['MatchKey', 'R'])
    
    # Merge Standard (Ruolo + Nome)
    f_rs_std = f_rs[f_rs['Ruolo'] != 'Giovani'].copy()
    f_rs_std['R_Match'] = f_rs_std['Ruolo'].map(map_r)
    f_rs_std = pd.merge(f_rs_std, f_qt_unique[['MatchKey', 'R', 'Qt.A']], left_on=['MatchKey', 'R_Match'], right_on=['MatchKey', 'R'], how='left')
    
    # Merge Giovani (Solo Nome)
    f_rs_gio = f_rs[f_rs['Ruolo'] == 'Giovani'].copy()
    f_rs_gio = pd.merge(f_rs_gio, f_qt.drop_duplicates('MatchKey')[['MatchKey', 'Qt.A']], on='MatchKey', how='left')
    
    f_rs = pd.concat([f_rs_std, f_rs_gio], ignore_index=True).fillna({'Qt.A': 0})
    f_rs = f_rs.rename(columns={'Qt.A': 'Quotazione'})

# --- INTERFACCIA APP ---
st.markdown('<div class="main-header">⚽ MUYFANTAMANAGER PRO V9.1</div>', unsafe_allow_html=True)

tabs = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET & VALORE", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI & TAGLI", "🕵️ MERCATO"])

# --- TAB 1: CLASSIFICHE ---
with tabs[0]:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Classifica Punti")
        if f_pt is not None: st.table(f_pt)
    with c2:
        st.subheader("⚔️ Scontri Diretti")
        if f_sc is not None: st.table(f_sc)

# --- TAB 2: BUDGET & VALORE ---
with tabs[1]:
    if f_rs is not None:
        st.subheader("💰 Analisi Economica Rose")
        budget = f_rs.groupby('Fantasquadra').agg({'Prezzo': 'sum', 'Quotazione': 'sum'}).reset_index()
        budget['Valore Totale'] = budget['Prezzo'] + budget['Quotazione']
        st.dataframe(budget.sort_values('Valore Totale', ascending=False), use_container_width=True, hide_index=True)

# --- TAB 3: ROSE ---
with tabs[2]:
    if f_rs is not None:
        mancanti = f_rs[f_rs['Quotazione'] == 0]
        if not mancanti.empty:
            st.markdown(f'<div class="status-box error-box">⚠️ {len(mancanti)} Giocatori a 0 (Controlla Tab Mercato)</div>', unsafe_allow_html=True)
        
        sq = st.selectbox("SQUADRA", sorted(f_rs['Fantasquadra'].unique()))
        df_sq = f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo', 'Quotazione']]
        st.table(df_sq)

# --- TAB 4: VINCOLI ---
with tabs[3]:
    st.subheader("📅 Giocatori Vincolati")
    if f_vn is not None: st.table(f_vn)

# --- TAB 5: SCAMBI & TAGLI ---
with tabs[4]:
    st.subheader("🔄 Simulatore Operazioni")
    if f_rs is not None:
        col1, col2 = st.columns(2)
        with col1:
            sa = st.selectbox("SQUADRA A", sorted(f_rs['Fantasquadra'].unique()), key="sa")
            ga = st.multiselect("CEDE DA A", f_rs[f_rs['Fantasquadra']==sa]['Nome'].tolist())
        with col2:
            sb = st.selectbox("SQUADRA B", [s for s in sorted(f_rs['Fantasquadra'].unique()) if s != sa], key="sb")
            gb = st.multiselect("CEDE DA B", f_rs[f_rs['Fantasquadra']==sb]['Nome'].tolist())
        
        if ga and gb:
            if st.button("📋 GENERA VERBALE"):
                st.code(f"SCAMBIO: {sa} riceve {', '.join(gb)} | {sb} riceve {', '.join(ga)}")

# --- TAB 6: MERCATO (SCOUTING) ---
with tabs[5]:
    st.subheader("🕵️ Scouting Svincolati")
    if f_qt is not None and f_rs is not None:
        occupati = f_rs['MatchKey'].tolist()
        liberi = f_qt[~f_qt['MatchKey'].isin(occupati)].sort_values('Qt.A', ascending=False)
        st.dataframe(liberi[['R', 'Nome', 'Qt.A']].head(50), use_container_width=True, hide_index=True)
