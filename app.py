import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# CSS PER GRASSETTO ESTREMO
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid; }
    .card-blue { background-color: #e3f2fd; border-color: #1a73e8; }
    .card-red { background-color: #fbe9e7; border-color: #d32f2f; }
    .card-grey { background-color: #f1f3f4; border-color: #9e9e9e; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; text-align: center; }
    .cut-info-box { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #ddd; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); color: black; }
    .stat-label { color: #666; font-size: 0.8em; text-transform: uppercase; }
    .stat-value { font-size: 1.2em; color: #1a1a1a; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO ---
def clean_quotazioni_name(name):
    if not isinstance(name, str): return name
    name = name.replace('č', 'E').replace('ň', 'O').replace('ř', 'I').replace('ć', 'C').replace('Č', 'E').replace('Ň', 'O')
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    name = name.upper().strip()
    mapping = {
        'MARTINEZ JO.': 'MARTINEZ JO', 'MILINKOVIC-SAVIC V.': 'MILINKOVIC SAVIC', 'N\'DICKA': 'NDICKA',
        'TAVARES N.': 'NUNO TAVARES', 'OSTIGARD': 'OSTIGAARD', 'PEZZELLA GIU.': 'PEZZELLA',
        'RODRIGUEZ J.': 'RODRIGUEZ J', 'DIMARCO': 'DIMARCO', 'CARLOS AUGUSTO': 'CARLOS AUGU',
        'KOSSOUNOU': 'KOSSOUNOU', 'THURAM K.': 'K THURAM', 'KONE M.': 'KONE', 'KONE M. (S)': 'KONE',
        'KAMARA': 'KAMAA', 'PELLEGRINI LO.': 'PELLEGRINI LORENZO', 'THORSTVEDT': 'THORSVEDT',
        'BERNABE': 'BERNABE', 'NORTON-CUFFY': 'NORTON CUFFY', 'NICOLUSSI CAVIGLIA': 'NICOLUSSI CAVIGLIA',
        'DELE-BASHIRU': 'DELE BASHIRU', 'AKINSANMIRO': 'NDRI AKINSAMIRO', 'LOFTUS-CHEEK': 'LOFTUS CHEEK',
        'MKHITARYAN': 'MKHTARYAN', 'SULEMANA I.': 'K SULEMANA', 'SULEMANA K.': 'K SULEMANA',
        'SOULE': 'SOULE K', 'DAVIS K.': 'DAVIS', 'DOUVIKAS': 'DOUVIKAS', 'SAELEMAEKERS': 'SAELEMAKERS',
        'ESPOSITO F.P.': 'PIO ESPOSITO', 'ESPOSITO SE.': 'ESPOSITO', 'MARTINELLI': 'MARTINELLI',
        'GABRIEL': 'GABRIEL', 'ZAMBO ANGUISSA': 'ANGUISSA', 'THURAM M.': 'THURAM M', 'MARTINEZ L.': 'LAUTARO'
    }
    if name in mapping: return mapping[name]
    name = re.sub(r'\s[A-Z]\.$', '', name)
    name = re.sub(r'\s[A-Z]\.[A-Z]\.$', '', name)
    return name

def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True, encoding='latin1')
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Nome_Match'] = df['Nome'].apply(clean_quotazioni_name)
            return df[['Nome_Match', 'Qt.A']].rename(columns={'Qt.A': 'Quotazione', 'Nome_Match': 'Nome'})
        return df.dropna(how='all')
    except: return None

def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip().upper()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

# --- CARICAMENTO DATI ---
f_rs, f_vn, f_pt, f_sc = ld("rose_complete.csv"), ld("vincoli.csv"), ld("classificapunti.csv"), ld("scontridiretti.csv")
f_qt = ld("quotazioni.csv", is_quot=True)

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Nome_N'] = f_rs['Nome'].apply(clean_string)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, left_on='Nome_N', right_on='Nome', how='left', suffixes=('', '_qt')).fillna({'Quotazione': 0})

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore_N'] = f_vn['Giocatore'].apply(clean_string)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- SIDEBAR POTENZIATA ---
with st.sidebar:
    st.header("🔍 **RICERCA GIOCATORE**")
    if f_rs is not None:
        scelte = st.multiselect("**CERCA NELLA LEGA**", sorted(f_rs['Nome_N'].unique()))
        for n in scelte:
            dr = f_rs[f_rs['Nome_N'] == n].iloc[0]
            # Recupero dati vincolo
            v_info = f_vn[f_vn['Giocatore_N'] == n] if f_vn is not None else None
            val_vinc = v_info['Tot_Vincolo'].iloc[0] if (v_info is not None and not v_info.empty) else 0
            durata_vinc = v_info['Anni_T'].iloc[0] if (v_info is not None and not v_info.empty) else "NO"
            
            st.markdown(f"""
            <div class="player-card card-grey">
                <span style="font-size:1.1em; color:#1a73e8;"><b>{n}</b></span> <small>({dr['Squadra_N']})</small><br>
                <hr style="margin:5px 0; border:0; border-top:1px solid #ccc;">
                ACQUISTO: <b>{int(dr['Prezzo_N'])}</b><br>
                VINCOLO: <b>{int(val_vinc)}</b> ({durata_vinc})<br>
                QUOT. ATTUALE: <b style="color:#2e7d32;">{int(dr['Quotazione'])}</b><br>
                <span style="font-size:0.9em; color:#666;">VALORE REALE: {int(dr['Prezzo_N'] + val_vinc)}</span>
            </div>
            """, unsafe_allow_html=True)

# --- MAIN APP ---
st.title("⚽ **MUYFANTAMANAGER GOLDEN V6.4**")
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**"])

# ... (Il resto delle tab rimane invariato rispetto alla v6.3)
