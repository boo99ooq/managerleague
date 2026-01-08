import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# --- SUPER CLEANER V8 (Forzatura Accenti e Decodifica) ---
def super_clean_v8(name):
    if not isinstance(name, str): return ""
    
    # 1. Correzione dei caratteri "rotti" dal file quotazioni (Mojibake)
    # Questa parte corregge i vari Ã’, Ãˆ, Soulč ecc.
    name = name.replace('Ã’', 'O').replace('Ãˆ', 'E').replace('Ã ', 'A')
    name = name.replace('ň', 'O').replace('č', 'E').replace('ř', 'I').replace('ć', 'C')
    
    # 2. Normalizzazione standard
    n = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper()
    
    # 3. Mappatura Specifica per i tuoi "0" rimasti
    hard_mapping = {
        'MONTIPO': 'MONTIPO',
        'SOULE': 'SOULE',
        'LAURIENTE': 'LAURIENTE',
        'BERNABE': 'BERNABE',
        'CASTELLANOS': 'CASTELLANOS',
        'NICO PAZ': 'PAZN',
        'PAZ N': 'PAZN',
        'VLAHOVIC ATA': 'VLAHOVICV', # L'altro Vlahovic nel listone
        'NDRI': 'AKINSANMIRO',
        'GABRIEL': 'TIAGOGABRIEL',
        'THURAM M': 'THURAM'
    }
    
    # Pulizia radicale (solo lettere e numeri)
    clean_raw = "".join(re.findall(r'[A-Z0-9]+', n))
    
    for k, v in hard_mapping.items():
        if k.replace(' ', '') in clean_raw: return v
    
    # 4. Fallback: parole ordinate
    words = re.findall(r'[A-Z0-9]+', n)
    words = [w for w in words if len(w) > 1] or words
    return "".join(sorted(words))

# --- CARICAMENTO ---
def load_data(f):
    if not os.path.exists(f): return None
    try:
        return pd.read_csv(f, engine='python', encoding='latin1')
    except:
        return None

f_rs = load_data("rose_complete.csv")
f_qt = load_data("quotazioni.csv")

# MAPPATURA RUOLI
map_r = {'Portiere': 'P', 'Difensore': 'D', 'Centrocampista': 'C', 'Attaccante': 'A', 'Giovani': 'A'}

if f_rs is not None and f_qt is not None:
    f_rs.columns = [c.strip() for c in f_rs.columns]
    f_qt.columns = [c.strip() for c in f_qt.columns]
    
    f_rs['MatchKey'] = f_rs['Nome'].apply(super_clean_v8)
    f_qt['MatchKey'] = f_qt['Nome'].apply(super_clean_v8)
    
    # Split Rose
    f_rs_std = f_rs[f_rs['Ruolo'] != 'Giovani'].copy()
    f_rs_gio = f_rs[f_rs['Ruolo'] == 'Giovani'].copy()
    
    # Matching Standard (Nome + Ruolo)
    f_rs_std['R_Match'] = f_rs_std['Ruolo'].map(map_r)
    f_qt_unique = f_qt.drop_duplicates(subset=['MatchKey', 'R'])
    f_rs_std = pd.merge(f_rs_std, f_qt_unique[['MatchKey', 'R', 'Qt.A']], 
                        left_on=['MatchKey', 'R_Match'], right_on=['MatchKey', 'R'], how='left')
    
    # Matching Giovani (Solo Nome)
    f_rs_gio = pd.merge(f_rs_gio, f_qt.drop_duplicates('MatchKey')[['MatchKey', 'Qt.A']], on='MatchKey', how='left')
    
    f_rs = pd.concat([f_rs_std, f_rs_gio], ignore_index=True).fillna({'Qt.A': 0})
    f_rs = f_rs.rename(columns={'Qt.A': 'Quotazione'})

# --- UI ---
st.title("⚽ MUYFANTAMANAGER GOLDEN V8.8")
tabs = st.tabs(["🏆 CLASSIFICHE", "🏃 ROSE", "🔄 SCAMBI", "🕵️ MERCATO"])

with tabs[1]: # ROSE
    if f_rs is not None:
        mancanti = f_rs[f_rs['Quotazione'] == 0]
        if not mancanti.empty:
            st.warning(f"⚠️ {len(mancanti)} Giocatori non trovati (Giovani o Errori): {', '.join(mancanti['Nome'].unique())}")
        
        sq = st.selectbox("SQUADRA", sorted(f_rs['Fantasquadra'].unique()))
        st.table(f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo', 'Quotazione']])
