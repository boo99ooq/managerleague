import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI PRO
st.set_page_config(page_title="MuyFantaManager GOLD V10", layout="wide", initial_sidebar_state="expanded")

# CSS STYLE (Il ritorno del Grassetto e pulizia decimali)
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .stDataFrame { border: 2px solid #1a73e8; border-radius: 10px; }
    .search-card { background-color: #ffffff; padding: 12px; border-radius: 10px; border: 2px solid #1a73e8; color: #1a1a1a !important; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .status-box { padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 2px solid; }
    .error-box { background-color: #ffebee; border-color: #c62828; color: #c62828; }
</style>
""", unsafe_allow_html=True)

# --- MOTORE DI PULIZIA ANTI-ERRORE (Soulé, Montipò, Kone, ecc.) ---
def super_clean_v10(name):
    if not isinstance(name, str): return ""
    name = name.replace('ň', 'O').replace('č', 'E').replace('Ã’', 'O').replace('Ãˆ', 'E').replace('Ã¨', 'E')
    n = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper()
    if 'KONE' in n:
        if 'M' in n and '(S)' not in n: return 'KONEMANU'
        if 'I' in n or '(S)' in n: return 'KONEISMAEL'
    mapping = {
        'NICO PAZ': 'PAZN', 'PAZ N': 'PAZN', 'GABRIEL': 'TIAGOGABRIEL', 
        'MARTINEZ L': 'LMARTINEZ', 'LAUTARO': 'LMARTINEZ', 'THURAM M': 'THURAM',
        'RODRIGUEZ J': 'RODRIGUEZJU', 'SULEMANA K': 'SULEMANAK'
    }
    clean_raw = "".join(re.findall(r'[A-Z0-9]+', n))
    if clean_raw in mapping: return mapping[clean_raw]
    words = re.findall(r'[A-Z0-9]+', n)
    words = [w for w in words if len(w) > 1] or words
    return "".join(sorted(words))

# --- CARICAMENTO DATI ---
def ld(f):
    if not os.path.exists(f): return None
    try: return pd.read_csv(f, engine='python', encoding='latin1').applymap(lambda x: x.strip() if isinstance(x, str) else x)
    except: return None

f_rs = ld("rose_complete.csv")
f_qt = ld("quotazioni.csv")
f_vn = ld("vincoli.csv")
f_pt = ld("classificapunti.csv")
f_sc = ld("scontridiretti.csv")

# MATCHING & CLEANING DECIMAL
if f_rs is not None and f_qt is not None:
    f_rs['MatchKey'] = f_rs['Nome'].apply(super_clean_v10)
    f_qt['MatchKey'] = f_qt['Nome'].apply(super_clean_v10)
    f_qt_unique = f_qt.drop_duplicates(subset=['MatchKey', 'R'])
    map_r = {'Portiere': 'P', 'Difensore': 'D', 'Centrocampista': 'C', 'Attaccante': 'A', 'Giovani': 'A'}
    
    f_rs_std = f_rs[f_rs['Ruolo'] != 'Giovani'].copy()
    f_rs_gio = f_rs[f_rs['Ruolo'] == 'Giovani'].copy()
    
    f_rs_std['R_Match'] = f_rs_std['Ruolo'].map(map_r)
    f_rs_std = pd.merge(f_rs_std, f_qt_unique[['MatchKey', 'R', 'Qt.A']], left_on=['MatchKey', 'R_Match'], right_on=['MatchKey', 'R'], how='left')
    f_rs_gio = pd.merge(f_rs_gio, f_qt.drop_duplicates('MatchKey')[['MatchKey', 'Qt.A']], on='MatchKey', how='left')
    
    f_rs = pd.concat([f_rs_std, f_rs_gio], ignore_index=True).fillna({'Qt.A': 0})
    f_rs['Quotazione'] = f_rs['Qt.A'].astype(int)
    f_rs['Prezzo'] = pd.to_numeric(f_rs['Prezzo']).astype(int)

# --- SIDEBAR (IL RITORNO) ---
with st.sidebar:
    st.title("🕵️ RICERCA")
    if f_rs is not None:
        cerca = st.multiselect("CERCA GIOCATORE", sorted(f_rs['Nome'].unique()))
        for n in cerca:
            r = f_rs[f_rs['Nome'] == n].iloc[0]
            st.markdown(f"""<div class="search-card">
                <b>{n}</b> ({r['Fantasquadra']})<br>
                💰 ASTA: {r['Prezzo']} | 📈 QUOT: {r['Quotazione']}
                </div>""", unsafe_allow_html=True)

# --- MAIN UI ---
st.title("⚽ MUYFANTAMANAGER GOLDEN V10")
tabs = st.tabs(["🏆 CLASSIFICHE", "🏃 ROSE", "🔄 SCAMBI", "✂️ TAGLI", "📅 VINCOLI", "🕵️ MERCATO"])

with tabs[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    with c1: 
        st.subheader("📊 Punti")
        if f_pt is not None: st.table(f_pt)
    with c2: 
        st.subheader("⚔️ Scontri")
        if f_sc is not None: st.table(f_sc)

with tabs[1]: # ROSE
    if f_rs is not None:
        mancanti = f_rs[f_rs['Quotazione'] == 0]
        if not mancanti.empty:
            st.markdown(f'<div class="status-box error-box">⚠️ {len(mancanti)} Giocatori a Quotazione 0</div>', unsafe_allow_html=True)
        sq = st.selectbox("SQUADRA", sorted(f_rs['Fantasquadra'].unique()))
        st.dataframe(f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo', 'Quotazione']], use_container_width=True, hide_index=True)

with tabs[2]: # SCAMBI
    st.subheader("🔄 Simulatore Scambi")
    if f_rs is not None:
        sq_list = sorted(f_rs['Fantasquadra'].unique())
        c1, c2 = st.columns(2)
        with c1:
            sa = st.selectbox("SQUADRA A", sq_list, key="sa")
            ga = st.multiselect("CEDE DA A", f_rs[f_rs['Fantasquadra']==sa]['Nome'].tolist())
        with c2:
            sb = st.selectbox("SQUADRA B", [s for s in sq_list if s != sa], key="sb")
            gb = st.multiselect("CEDE DA B", f_rs[f_rs['Fantasquadra']==sb]['Nome'].tolist())
        if ga and gb:
            val_a = f_rs[f_rs['Nome'].isin(ga)]['Prezzo'].sum()
            val_b = f_rs[f_rs['Nome'].isin(gb)]['Prezzo'].sum()
            st.write(f"⚖️ Bilancio Crediti: {sa} ({val_a}) ↔️ {sb} ({val_b})")
            if st.button("GENERA VERBALE"):
                st.code(f"SCAMBIO: {sa} riceve {', '.join(gb)} | {sb} riceve {', '.join(ga)}")

with tabs[3]: # TAGLI
    st.subheader("✂️ Calcolo Recupero Crediti")
    if f_rs is not None:
        sq_t = st.selectbox("SQUADRA", sorted(f_rs['Fantasquadra'].unique()), key="sq_t")
        tagli = st.multiselect("GIOCATORI DA TAGLIARE", f_rs[f_rs['Fantasquadra']==sq_t]['Nome'].tolist())
        if tagli:
            recupero = f_rs[f_rs['Nome'].isin(tagli)]['Prezzo'].sum() / 2
            st.success(f"💰 Crediti recuperati (50%): {int(recupero)}")

with tabs[4]: # VINCOLI
    if f_vn is not None: st.table(f_vn)

with tabs[5]: # MERCATO
    if f_qt is not None and f_rs is not None:
        occupati = f_rs['MatchKey'].tolist()
        liberi = f_qt[~f_qt['MatchKey'].isin(occupati)].sort_values('Qt.A', ascending=False)
        st.dataframe(liberi[['R', 'Nome', 'Qt.A']].head(50), use_container_width=True, hide_index=True)
