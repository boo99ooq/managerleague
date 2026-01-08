import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# CSS AGGIORNATO E CORRETTO
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    
    /* Card Ricerca Sidebar */
    .search-card { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        margin-bottom: 15px; 
        border: 2px solid #1a73e8;
        color: #1a1a1a !important;
    }
    
    .card-header { border-bottom: 2px solid #eee; margin-bottom: 10px; padding-bottom: 5px; }
    .player-name { color: #1a73e8; font-size: 1.1em; }
    .team-name { color: #666; font-size: 0.8em; }
    
    .stat-row { display: block; width: 100%; margin-bottom: 4px; }
    .label { float: left; color: #555; font-size: 0.85em; }
    .valore { float: right; }
    .clearfix { clear: both; }
    
    .quot-box { 
        margin-top: 10px; 
        padding-top: 5px; 
        border-top: 1px dashed #ccc; 
        color: #2e7d32; 
    }
    
    .tot-reale {
        background-color: #f8f9fa;
        padding: 5px;
        margin-top: 8px;
        border-radius: 5px;
        text-align: center;
    }
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

# --- SIDEBAR CORRETTA ---
with st.sidebar:
    st.header("🔍 RICERCA GIOCATORE")
    if f_rs is not None:
        scelte = st.multiselect("SELEZIONA", sorted(f_rs['Nome_N'].unique()))
        st.write("---")
        for n in scelte:
            dr = f_rs[f_rs['Nome_N'] == n].iloc[0]
            v_info = f_vn[f_vn['Giocatore_N'] == n] if f_vn is not None else None
            val_vinc = v_info['Tot_Vincolo'].iloc[0] if (v_info is not None and not v_info.empty) else 0
            durata_vinc = v_info['Anni_T'].iloc[0] if (v_info is not None and not v_info.empty) else "NO"
            
            # HTML Card con clearfix e float per stabilità
            st.markdown(f"""
            <div class="search-card">
                <div class="card-header">
                    <span class="player-name"><b>{n}</b></span><br>
                    <span class="team-name">{dr['Squadra_N']} - {dr['Ruolo']}</span>
                </div>
                <div class="stat-row">
                    <span class="label">Acquisto:</span> <span class="valore"><b>{int(dr['Prezzo_N'])}</b></span>
                    <div class="clearfix"></div>
                </div>
                <div class="stat-row">
                    <span class="label">Vincolo:</span> <span class="valore"><b>{int(val_vinc)}</b> ({durata_vinc})</span>
                    <div class="clearfix"></div>
                </div>
                <div class="quot-box">
                    <span class="label" style="color:#2e7d32;">Quot. Attuale:</span> <span class="valore"><b>{int(dr['Quotazione'])}</b></span>
                    <div class="clearfix"></div>
                </div>
                <div class="tot-reale">
                    <span class="label">TOTALE REALE:</span> <span class="valore"><b>{int(dr['Prezzo_N'] + val_vinc)}</b></span>
                    <div class="clearfix"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# --- RESTO DELL'APP ---
st.title("⚽ MUYFANTAMANAGER GOLDEN V6.6")
t = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "✂️ TAGLI"])

with t[2]: # ROSE
    if f_rs is not None:
        sq = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="rs_v66")
        df_sq = f_rs[f_rs['Squadra_N'] == sq][['Ruolo', 'Nome_N', 'Prezzo_N', 'Quotazione']]
        def color_ruoli(row):
            bg = {'POR': '#FCE4EC', 'DIF': '#E8F5E9', 'CEN': '#E3F2FD', 'ATT': '#FFFDE7'}.get(str(row['Ruolo']).upper()[:3], '#FFFFFF')
            return [f'background-color: {bg}; color: black; font-weight: 900;'] * len(row)
        st.dataframe(df_sq.style.apply(color_ruoli, axis=1).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

# [Aggiungi qui le altre Tab 0, 1, 3, 4, 5 delle versioni precedenti]
