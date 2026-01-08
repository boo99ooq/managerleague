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

# --- SUPER CLEANER V10 (The Kone & Accents Master) ---
def super_clean_v10(name):
    if not isinstance(name, str): return ""
    
    # 1. Traduzione caratteri speciali e mojibake
    name = name.replace('ň', 'O').replace('č', 'E').replace('Ã’', 'O').replace('Ãˆ', 'E').replace('Ã¨', 'E')
    name = name.replace('Ò', 'O').replace('È', 'E').replace('È', 'E').replace('É', 'E')
    
    # 2. Normalizzazione unicode
    n = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper()
    
    # 3. Gestione SPECIFICA KONE
    if 'KONE' in n:
        if 'M' in n and 'SASSUOLO' not in n and '(S)' not in n: return 'KONEMANU'
        if 'I' in n or 'SASSUOLO' in n or '(S)' in n: return 'KONEISMAEL'

    # 4. Mappatura Manuale Altri
    mapping = {
        'NICO PAZ': 'PAZN', 'PAZ N': 'PAZN',
        'GABRIEL': 'TIAGOGABRIEL', 'THIAGO GABRIEL': 'TIAGOGABRIEL',
        'RODRIGUEZ J': 'RODRIGUEZJU',
        'MARTINEZ L': 'LMARTINEZ', 'LAUTARO': 'LMARTINEZ',
        'SULEMANA K': 'SULEMANAK', 'SOULE': 'SOULE', 'MONTIPO': 'MONTIPO',
        'LAURIENTE': 'LAURIENTE', 'BERNABE': 'BERNABE'
    }
    
    clean_raw = "".join(re.findall(r'[A-Z0-9]+', n))
    if clean_raw in mapping: return mapping[clean_raw]
    
    # 5. Fallback parole ordinate
    words = re.findall(r'[A-Z0-9]+', n)
    if len(words) > 1:
        words = [w for w in words if len(w) > 1] or words
    res = "".join(sorted(words))
    return mapping.get(res, res)

# --- CARICAMENTO ---
def load_data(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', encoding='utf-8')
    except:
        df = pd.read_csv(f, engine='python', encoding='latin-1')
    df.columns = [c.strip() for c in df.columns]
    return df

f_rs = load_data("rose_complete.csv")
f_qt = load_data("quotazioni.csv")
map_r = {'Portiere': 'P', 'Difensore': 'D', 'Centrocampista': 'C', 'Attaccante': 'A', 'Giovani': 'A'}

if f_rs is not None and f_qt is not None:
    f_rs['MatchKey'] = f_rs['Nome'].apply(super_clean_v10)
    f_qt['MatchKey'] = f_qt['Nome'].apply(super_clean_v10)
    
    f_rs_std = f_rs[f_rs['Ruolo'] != 'Giovani'].copy()
    f_rs_gio = f_rs[f_rs['Ruolo'] == 'Giovani'].copy()
    
    f_rs_std['R_Match'] = f_rs_std['Ruolo'].map(map_r)
    # Merge su Nome + Ruolo
    f_qt_clean = f_qt.drop_duplicates(subset=['MatchKey', 'R'])
    f_rs_std = pd.merge(f_rs_std, f_qt_clean[['MatchKey', 'R', 'Qt.A']], 
                        left_on=['MatchKey', 'R_Match'], right_on=['MatchKey', 'R'], how='left')
    
    f_rs_gio = pd.merge(f_rs_gio, f_qt.drop_duplicates('MatchKey')[['MatchKey', 'Qt.A']], on='MatchKey', how='left')
    f_rs = pd.concat([f_rs_std, f_rs_gio], ignore_index=True).fillna({'Qt.A': 0})
    f_rs = f_rs.rename(columns={'Qt.A': 'Quotazione'})

# --- UI APP ---
st.title("⚽ MUYFANTAMANAGER GOLDEN V9.0")
tabs = st.tabs(["🏆 CLASSIFICHE", "🏃 ROSE", "🔄 SCAMBI", "🕵️ MERCATO"])

with tabs[1]: # ROSE
    if f_rs is not None:
        mancanti = f_rs[f_rs['Quotazione'] == 0]
        if not mancanti.empty:
            st.markdown(f'<div class="status-box error-box">⚠️ <b>GIOCATORI A 0:</b> {", ".join(mancanti["Nome"].unique())}</div>', unsafe_allow_html=True)
            st.info("💡 Nota: Castellanos e Martinelli hanno lasciato la Serie A (Quotazione 0 corretta).")

        # Doppioni (Controllo Nome + Ruolo)
        dup = f_rs[f_rs.duplicated(subset=['MatchKey', 'Ruolo'], keep=False)]
        if not dup.empty:
            st.markdown(f'<div class="status-box warning-box">👯 <b>DOPPIONI RILEVATI:</b> {", ".join(dup["Nome"].unique())}</div>', unsafe_allow_html=True)

        sq = st.selectbox("SQUADRA", sorted(f_rs['Fantasquadra'].unique()))
        st.table(f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo', 'Quotazione']])

# (Tab Scambi e Mercato rimangono attive...)
