import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# --- SUPER CLEANER V5 (Gestisce caratteri speciali del listone) ---
def super_clean_v5(name):
    if not isinstance(name, str): return ""
    # Traduzione caratteri speciali specifici del tuo listone (ň -> O, č -> E)
    name = name.replace('ň', 'O').replace('č', 'E').replace('Ã’', 'O').replace('Ãˆ', 'E')
    # Normalizzazione standard (rimuove accenti italiani)
    n = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper()
    
    # Mappatura manuale per nomi che cambiano ordine o iniziali
    mapping = {
        'LAUTARO': 'MARTINEZ L',
        'NICO PAZ': 'PAZN', 
        'PAZ N': 'PAZN',
        'ONDREJKA': 'ONDREJKA',
        'KONE M': 'KONEM',
        'KONE M (S)': 'KONEI', # Ismael Kone nel listone è Kone I.
        'SULEMANA K': 'SULEMANAK',
        'CASTELLANOS': 'CASTELLANOS',
        'BERNABE': 'BERNABE',
        'LAURIENTE': 'LAURIENTE',
        'SOULE': 'SOULE'
    }
    
    # Pulizia totale: solo lettere e numeri
    clean_raw = "".join(re.findall(r'[A-Z0-9]+', n))
    
    # Controllo se il nome pulito è nel mapping
    for k, v in mapping.items():
        if k.replace(' ', '') in clean_raw: return v
    
    # Ritorna le parole ordinate (gestisce "MARTINELLI T." -> "MARTINELLI")
    words = re.findall(r'[A-Z0-9]+', n)
    return "".join(sorted(words))

# --- CARICAMENTO DATI ---
def load_data(f):
    if not os.path.exists(f): return None
    try:
        return pd.read_csv(f, engine='python', encoding='latin1').applymap(lambda x: x.strip() if isinstance(x, str) else x)
    except: return None

# Caricamento
f_rs = load_data("rose_complete.csv")
f_qt = load_data("quotazioni.csv") # Caricato come UTF-8 o Latin1 a seconda del sistema

# Mappatura Ruoli per il match perfetto
map_r = {'Portiere': 'P', 'Difensore': 'D', 'Centrocampista': 'C', 'Attaccante': 'A', 'Giovani': 'A'}

if f_rs is not None and f_qt is not None:
    # Pulizia nomi colonne
    f_rs.columns = [c.strip() for c in f_rs.columns]
    f_qt.columns = [c.strip() for c in f_qt.columns]
    
    # Applichiamo la MatchKey
    f_rs['MatchKey'] = f_rs['Nome'].apply(super_clean_v5)
    f_qt['MatchKey'] = f_qt['Nome'].apply(super_clean_v5)
    
    # Special Fix: Ondrejka è C nel listone ma Giovane (A) nelle rose
    # Forza il ruolo C per Ondrejka nelle rose per il matching
    f_rs.loc[f_rs['MatchKey'] == 'ONDREJKA', 'Ruolo_Match'] = 'C'
    f_rs['Ruolo_Match'] = f_rs['Ruolo_Match'].fillna(f_rs['Ruolo'].map(map_r))
    
    # Merge basato su Chiave + Ruolo (Risolve i doppioni Ferguson e Terracciano)
    f_qt_clean = f_qt.drop_duplicates(subset=['MatchKey', 'R'])
    f_rs = pd.merge(f_rs, f_qt_clean[['MatchKey', 'R', 'Qt.A']], 
                    left_on=['MatchKey', 'Ruolo_Match'], 
                    right_on=['MatchKey', 'R'], 
                    how='left').fillna({'Qt.A': 0})
    f_rs = f_rs.rename(columns={'Qt.A': 'Quotazione'})

# --- UI APP ---
st.title("⚽ MUYFANTAMANAGER GOLDEN V8.5")
tabs = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "✂️ TAGLI", "🕵️ MERCATO"])

with tabs[2]: # ROSE
    if f_rs is not None:
        mancanti = f_rs[f_rs['Quotazione'] == 0]
        if not mancanti.empty:
            st.error(f"⚠️ {len(mancanti)} GIOCATORI CON VALORE 0. Controlla: {', '.join(mancanti['Nome'].unique())}")
            st.info("Nota: Castellanos e Martinelli non sono stati trovati nel tuo file quotazioni.csv")
        
        sq = st.selectbox("SQUADRA", sorted(f_rs['Fantasquadra'].unique()))
        st.dataframe(f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo', 'Quotazione']], use_container_width=True, hide_index=True)
    else: st.error("File rose_complete.csv non trovato.")

# ... (Le altre Tab rimangono invariate)
