import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid; }
    .card-blue { background-color: #e3f2fd; border-color: #1a73e8; }
    .card-red { background-color: #fbe9e7; border-color: #d32f2f; }
    .card-grey { background-color: #f1f3f4; border-color: #9e9e9e; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONE MAPPING AVANZATA (V4) ---
def clean_quotazioni_name(name):
    if not isinstance(name, str): return name
    
    # Pulizia caratteri speciali CSV
    name = name.replace('č', 'E').replace('ň', 'O').replace('ř', 'I').replace('ć', 'C').replace('Č', 'E').replace('Ň', 'O')
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    name = name.upper().strip()
    
    # DIZIONARIO COMPLETO DELLE ECCEZIONI SEGNALATE
    mapping = {
        # PORTIERI / DIFENSORI
        'MARTINEZ JO.': 'MARTINEZ JO',
        'MILINKOVIC-SAVIC V.': 'MILINKOVIC SAVIC',
        'N\'DICKA': 'NDICKA',
        'TAVARES N.': 'NUNO TAVARES',
        'OSTIGARD': 'OSTIGAARD',
        'PEZZELLA GIU.': 'PEZZELLA',
        'RODRIGUEZ J.': 'RODRIGUEZ J',
        'DIMARCO': 'DIMARCO',
        'CARLOS AUGUSTO': 'CARLOS AUGU',
        'KOSSOUNOU': 'KOSSOUNOU',
        
        # CENTROCAMPISTI
        'THURAM K.': 'K THURAM',
        'KONE M.': 'KONE',
        'KONE M. (S)': 'KONE', # Caso Sassuolo
        'THIAGO MOTTA': 'THIAGO', # Se registrato così
        'KAMARA': 'KAMAA',
        'PELLEGRINI LO.': 'PELLEGRINI LORENZO',
        'THORSTVEDT': 'THORSVEDT',
        'BERNABE': 'BERNABE',
        'NORTON-CUFFY': 'NORTON CUFFY',
        'NICOLUSSI CAVIGLIA': 'NICOLUSSI CAVIGLIA',
        'DELE-BASHIRU': 'DELE BASHIRU',
        'AKINSANMIRO': 'NDRI AKINSAMIRO',
        'LOFTUS-CHEEK': 'LOFTUS CHEEK',
        'MKHITARYAN': 'MKHTARYAN',
        'SULEMANA I.': 'K SULEMANA',
        'SULEMANA K.': 'K SULEMANA',
        
        # ATTACCANTI
        'SOULE': 'SOULE K',
        'DAVIS K.': 'DAVIS',
        'DOUVIKAS': 'DOUVIKAS',
        'SAELEMAEKERS': 'SAELEMAKERS',
        'ESPOSITO F.P.': 'PIO ESPOSITO', # Solitamente Pio è F.P.
        'ESPOSITO SE.': 'ESPOSITO',
        'MARTINELLI': 'MARTINELLI',
        'GABRIEL': 'GABRIEL'
    }
    
    if name in mapping: return mapping[name]
    
    # Pulizia generica residua (es. "LUKAKU R." -> "LUKAKU")
    name = re.sub(r'\s[A-Z]\.$', '', name)
    name = re.sub(r'\s[A-Z]\.[A-Z]\.$', '', name)
    
    return name

# --- CARICAMENTO ---
def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True, encoding='latin1')
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Nome'] = df['Nome'].apply(clean_quotazioni_name)
            return df[['Nome', 'Qt.A']].rename(columns={'Qt.A': 'Quotazione'})
        return df.dropna(how='all')
    except: return None

def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str.upper()

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

# LOAD DATA
f_rs, f_vn, f_qt = ld("rose_complete.csv"), ld("vincoli.csv"), ld("quotazioni.csv", is_quot=True)
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Nome'] = f_rs['Nome'].apply(clean_string)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, on='Nome', how='left').fillna({'Quotazione': 0})

# --- INTERFACCIA ---
st.title("⚽ MUYFANTAMANAGER GOLDEN V4")
tabs = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "✂️ TAGLI"])

with tabs[2]: # TAB ROSE
    if f_rs is not None:
        sq = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="r_sel")
        df_sq = f_rs[f_rs['Squadra_N'] == sq][['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']]
        st.dataframe(df_sq.style.format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

# AGGIUNGI QUI LE ALTRE TAB (0, 1, 3, 4, 5) DAL CODICE PRECEDENTE
