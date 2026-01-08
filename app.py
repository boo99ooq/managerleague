import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# --- SUPER CLEANER V7 (Mappatura Finale) ---
def super_clean_v7(name):
    if not isinstance(name, str): return ""
    name = name.replace('ň', 'O').replace('č', 'E').replace('Ã’', 'O').replace('Ãˆ', 'E')
    n = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper()
    
    # DIZIONARIO DEFINITIVO
    mapping = {
        'NICO PAZ': 'PAZN', 'PAZ N': 'PAZN',
        'GABRIEL': 'TIAGOGABRIEL', 'THIAGO GABRIEL': 'TIAGOGABRIEL',
        'RODRIGUEZ J': 'RODRIGUEZJU', # Difensore
        'MARTINEZ L': 'LMARTINEZ', 'LAUTARO': 'LMARTINEZ',
        'THURAM M': 'THURAM', 'THURAM': 'THURAM',
        'SULEMANA K': 'SULEMANAK'
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
    try: return pd.read_csv(f, engine='python', encoding='latin1').applymap(lambda x: x.strip() if isinstance(x, str) else x)
    except: return None

f_rs = load_data("rose_complete.csv")
f_qt = load_data("quotazioni.csv")
map_r = {'Portiere': 'P', 'Difensore': 'D', 'Centrocampista': 'C', 'Attaccante': 'A', 'Giovani': 'A'}

if f_rs is not None and f_qt is not None:
    f_rs['MatchKey'] = f_rs['Nome'].apply(super_clean_v7)
    f_qt['MatchKey'] = f_qt['Nome'].apply(super_clean_v7)
    
    f_rs_std = f_rs[f_rs['Ruolo'] != 'Giovani'].copy()
    f_rs_gio = f_rs[f_rs['Ruolo'] == 'Giovani'].copy()
    
    f_rs_std['R_Match'] = f_rs_std['Ruolo'].map(map_r)
    f_qt_clean = f_qt.drop_duplicates(subset=['MatchKey', 'R'])
    f_rs_std = pd.merge(f_rs_std, f_qt_clean[['MatchKey', 'R', 'Qt.A']], left_on=['MatchKey', 'R_Match'], right_on=['MatchKey', 'R'], how='left')
    
    f_rs_gio = pd.merge(f_rs_gio, f_qt.drop_duplicates('MatchKey')[['MatchKey', 'Qt.A']], on='MatchKey', how='left')
    f_rs = pd.concat([f_rs_std, f_rs_gio], ignore_index=True).fillna({'Qt.A': 0})
    f_rs = f_rs.rename(columns={'Qt.A': 'Quotazione'})

# --- UI APP ---
st.title("⚽ MUYFANTAMANAGER GOLDEN V8.7")
tabs = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "🔄 SCAMBI", "🕵️ MERCATO"])

with tabs[2]: # ROSE
    if f_rs is not None:
        mancanti = f_rs[f_rs['Quotazione'] == 0]
        if not mancanti.empty:
            with st.expander(f"ℹ️ Nota su {len(mancanti)} giocatori (Quotazione 0)"):
                st.write("Questi giocatori sono giovani o hanno lasciato la Serie A: " + ", ".join(mancanti['Nome'].unique()))
        
        sq = st.selectbox("SQUADRA", sorted(f_rs['Fantasquadra'].unique()))
        st.table(f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo', 'Quotazione']])
