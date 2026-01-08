import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide")

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .status-box { padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 2px solid; }
    .error-box { background-color: #ffebee; border-color: #c62828; color: #c62828; }
    .warning-box { background-color: #fff3e0; border-color: #ef6c00; color: #ef6c00; }
    .search-card { background-color: #ffffff; padding: 10px; border-radius: 8px; border: 1px solid #1a73e8; margin-bottom: 8px; color: black; }
</style>
""", unsafe_allow_html=True)

# --- SUPER CLEANER V9 (Traduttore Listone) ---
def super_clean_v9(name):
    if not isinstance(name, str): return ""
    
    # 1. Correzione manuale dei caratteri "est-europei" del tuo listone
    # ň -> o, č -> e (tipici del tuo file quotazioni.csv)
    name = name.replace('ň', 'O').replace('č', 'E').replace('Ã’', 'O').replace('Ãˆ', 'E').replace('Ã¨', 'E')
    
    # 2. Normalizzazione standard
    n = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper()
    
    # 3. Dizionario Mappatura Manuale (Tuo File -> Listone)
    mapping = {
        'NICO PAZ': 'PAZN', 'PAZ N': 'PAZN',
        'GABRIEL': 'TIAGOGABRIEL', 'THIAGO GABRIEL': 'TIAGOGABRIEL',
        'RODRIGUEZ J': 'RODRIGUEZJU', # Rodriguez Ju. (Difensore)
        'MARTINEZ L': 'LMARTINEZ', 'LAUTARO': 'LMARTINEZ',
        'THURAM M': 'THURAM', 'TOURE E': 'TOURE',
        'SULEMANA K': 'SULEMANAK'
    }
    
    clean_raw = "".join(re.findall(r'[A-Z0-9]+', n))
    for k, v in mapping.items():
        if k.replace(' ', '') in clean_raw: return v
    
    # 4. Fallback: parole ordinate per flessibilità (es: SULEMANA K. == K. SULEMANA)
    words = re.findall(r'[A-Z0-9]+', n)
    words = [w for w in words if len(w) > 1] or words
    return "".join(sorted(words))

# --- CARICAMENTO DATI ---
def load_data(f):
    if not os.path.exists(f): return None
    try:
        # Usiamo utf-8 per leggere correttamente i caratteri speciali
        df = pd.read_csv(f, engine='python', encoding='utf-8')
    except:
        df = pd.read_csv(f, engine='python', encoding='latin-1')
    df.columns = [c.strip() for c in df.columns]
    return df

f_rs = load_data("rose_complete.csv")
f_qt = load_data("quotazioni.csv")
map_r = {'Portiere': 'P', 'Difensore': 'D', 'Centrocampista': 'C', 'Attaccante': 'A', 'Giovani': 'A'}

if f_rs is not None and f_qt is not None:
    f_rs['MatchKey'] = f_rs['Nome'].apply(super_clean_v9)
    f_qt['MatchKey'] = f_qt['Nome'].apply(super_clean_v9)
    
    # Matching differenziato (Standard vs Giovani)
    f_rs_std = f_rs[f_rs['Ruolo'] != 'Giovani'].copy()
    f_rs_gio = f_rs[f_rs['Ruolo'] == 'Giovani'].copy()
    
    # Standard: Match su Nome + Ruolo (Risolve i doppioni Ferguson e Terracciano)
    f_rs_std['R_Match'] = f_rs_std['Ruolo'].map(map_r)
    f_qt_clean = f_qt.drop_duplicates(subset=['MatchKey', 'R'])
    f_rs_std = pd.merge(f_rs_std, f_qt_clean[['MatchKey', 'R', 'Qt.A']], 
                        left_on=['MatchKey', 'R_Match'], right_on=['MatchKey', 'R'], how='left')
    
    # Giovani: Match solo su Nome
    f_rs_gio = pd.merge(f_rs_gio, f_qt.drop_duplicates('MatchKey')[['MatchKey', 'Qt.A']], on='MatchKey', how='left')
    
    f_rs = pd.concat([f_rs_std, f_rs_gio], ignore_index=True).fillna({'Qt.A': 0})
    f_rs = f_rs.rename(columns={'Qt.A': 'Quotazione'})

# --- APP ---
st.title("⚽ MUYFANTAMANAGER GOLDEN V8.9")
tabs = st.tabs(["🏆 CLASSIFICHE", "🏃 ROSE", "🔄 SCAMBI", "🕵️ MERCATO"])

with tabs[1]: # TAB ROSE & TOOL DEGLI 0
    if f_rs is not None:
        # TOOL INDIVIDUAZIONE 0
        mancanti = f_rs[f_rs['Quotazione'] == 0]
        if not mancanti.empty:
            st.markdown(f'<div class="status-box error-box">⚠️ <b>{len(mancanti)} GIOCATORI A 0:</b> {", ".join(mancanti["Nome"].unique())}</div>', unsafe_allow_html=True)
            st.info("ℹ️ Castellanos e Martinelli non sono presenti nel listone ufficiale. I giovani appariranno a 0 se non ancora quotati.")

        # DOPPIONI
        dup = f_rs[f_rs.duplicated(subset=['MatchKey', 'Ruolo'], keep=False)]
        if not dup.empty:
            st.markdown(f'<div class="status-box warning-box">👯 <b>DOPPIONI RILEVATI:</b> {", ".join(dup["Nome"].unique())}</div>', unsafe_allow_html=True)

        sq = st.selectbox("SQUADRA", sorted(f_rs['Fantasquadra'].unique()))
        st.table(f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo', 'Quotazione']])

with tabs[2]: # VERBALE SCAMBI
    st.subheader("🔄 GENERATORE VERBALE SCAMBI")
    if f_rs is not None:
        c1, c2 = st.columns(2)
        with c1: sa = st.selectbox("SQUADRA A", sorted(f_rs['Fantasquadra'].unique()), key="sa")
        with c2: sb = st.selectbox("SQUADRA B", [s for s in sorted(f_rs['Fantasquadra'].unique()) if s != sa], key="sb")
        
        ga = st.multiselect("CEDUTI DA A", f_rs[f_rs['Fantasquadra']==sa]['Nome'].tolist())
        gb = st.multiselect("CEDUTI DA B", f_rs[f_rs['Fantasquadra']==sb]['Nome'].tolist())
        
        if ga and gb:
            if st.button("📋 GENERA TESTO VERBALE"):
                st.code(f"🔄 SCAMBIO CONFERMATO\n🤝 {sa} riceve: {', '.join(gb)}\n🤝 {sb} riceve: {', '.join(ga)}\n✅ Calcoli media e prezzi aggiornati a sistema.")

with tabs[3]: # MERCATO
    st.subheader("🕵️ SCOUTING SVINCOLATI")
    if f_qt is not None and f_rs is not None:
        occupati = f_rs['MatchKey'].tolist()
        liberi = f_qt[~f_qt['MatchKey'].isin(occupati)].sort_values('Qt.A', ascending=False)
        st.dataframe(liberi[['R', 'Nome', 'Qt.A']], use_container_width=True, hide_index=True)
