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
    .status-box { padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 2px solid; }
    .error-box { background-color: #ffebee; border-color: #c62828; color: #c62828; }
    .warning-box { background-color: #fff3e0; border-color: #ef6c00; color: #ef6c00; }
</style>
""", unsafe_allow_html=True)

# --- SUPER CLEANER V6 (Correzione Caratteri e Omonimie) ---
def super_clean_v6(name):
    if not isinstance(name, str): return ""
    # Traduzione caratteri specifici del tuo listone (ň->O, č->E)
    name = name.replace('ň', 'O').replace('č', 'E')
    # Normalizzazione unicode (accenti italiani)
    n = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper()
    
    # Dizionario Traduzioni Manuali
    mapping = {
        'LAUTARO': 'MARTINEZ L', 'NICO PAZ': 'PAZ N', 'THURAM M': 'THURAM',
        'MARTINELLI T': 'MARTINELLI', 'GUDMUNDSSON': 'GUDMUNDSSON A',
        'SUCIC': 'SUCIC P', 'KONE M': 'KONE M', 'KONE M (S)': 'KONE I',
        'BERNABE': 'BERNABE', 'LAURIENTE': 'LAURIENTE', 'SOULE': 'SOULE',
        'CASTELLANOS': 'CASTELLANOS', 'SULEMANA K': 'SULEMANA K',
        'NDRI': 'NDRI', 'AKINSANMIRO': 'AKINSANMIRO'
    }
    
    # Pulizia: solo lettere e numeri
    clean_raw = "".join(re.findall(r'[A-Z0-9]+', n))
    for k, v in mapping.items():
        if k.replace(' ', '') in clean_raw: return v.replace(' ', '')
    
    # Se non mappato, pulizia standard delle parole
    words = re.findall(r'[A-Z0-9]+', n)
    # Rimuove iniziali singole se non strettamente necessario (es. "PAZ N" -> "PAZ")
    words = [w for w in words if len(w) > 1] or words
    return "".join(sorted(words))

# --- CARICAMENTO DATI ---
def load_data(f, enc='utf-8'):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', encoding=enc)
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return pd.read_csv(f, engine='python', encoding='latin1') if enc == 'utf-8' else None

f_rs = load_data("rose_complete.csv")
f_qt = load_data("quotazioni.csv")

# MAPPATURA RUOLI
map_r = {'Portiere': 'P', 'Difensore': 'D', 'Centrocampista': 'C', 'Attaccante': 'A'}

if f_rs is not None and f_qt is not None:
    f_rs['MatchKey'] = f_rs['Nome'].apply(super_clean_v6)
    f_qt['MatchKey'] = f_qt['Nome'].apply(super_clean_v6)
    
    # Divisione Rose: Standard vs Giovani
    f_rs_std = f_rs[f_rs['Ruolo'] != 'Giovani'].copy()
    f_rs_gio = f_rs[f_rs['Ruolo'] == 'Giovani'].copy()
    
    # Merge Standard (Nome + Ruolo per Ferguson/Terracciano)
    f_rs_std['R_Match'] = f_rs_std['Ruolo'].map(map_r)
    f_rs_std = pd.merge(f_rs_std, f_qt[['MatchKey', 'R', 'Qt.A']], 
                        left_on=['MatchKey', 'R_Match'], right_on=['MatchKey', 'R'], how='left')
    
    # Merge Giovani (Solo Nome, ignora Ruolo per Baldanzi/Miretti)
    f_rs_gio = pd.merge(f_rs_gio, f_qt.drop_duplicates('MatchKey')[['MatchKey', 'Qt.A']], on='MatchKey', how='left')
    
    # Ricongiungimento
    f_rs = pd.concat([f_rs_std, f_rs_gio], ignore_index=True).fillna({'Qt.A': 0})
    f_rs = f_rs.rename(columns={'Qt.A': 'Quotazione'})

# --- APP TABS ---
st.title("⚽ MUYFANTAMANAGER GOLDEN V8.6")
t = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "🕵️ MERCATO"])

with t[2]: # ROSE
    if f_rs is not None:
        mancanti = f_rs[f_rs['Quotazione'] == 0]
        if not mancanti.empty:
            st.error(f"⚠️ {len(mancanti)} GIOCATORI CON VALORE 0. Tra cui: {', '.join(mancanti['Nome'].unique())}")
            st.info("💡 Nota: Castellanos e Martinelli sembrano mancare proprio dal file quotazioni.csv originale.")
        
        sq = st.selectbox("SQUADRA", sorted(f_rs['Fantasquadra'].unique()))
        df_sq = f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo', 'Quotazione']]
        st.table(df_sq)
