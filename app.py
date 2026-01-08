import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# CSS TOTALE (GRASSETTO E CARD)
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .search-card { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; color: #1a1a1a !important; }
    .card-header { border-bottom: 2px solid #eee; margin-bottom: 10px; padding-bottom: 5px; }
    .player-name { color: #1a73e8; font-size: 1.1em; }
    .stat-row { display: block; width: 100%; margin-bottom: 4px; }
    .label { float: left; color: #555; font-size: 0.85em; }
    .valore { float: right; }
    .clearfix { clear: both; }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid; color: black !important; }
    .card-blue { background-color: #e3f2fd; border-color: #1a73e8; }
    .card-red { background-color: #fbe9e7; border-color: #d32f2f; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; text-align: center; margin-top:10px; }
    .cut-info-box { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #ddd; color: black; }
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

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 RICERCA GIOCATORE")
    if f_rs is not None:
        scelte = st.multiselect("SELEZIONA", sorted(f_rs['Nome_N'].unique()))
        for n in scelte:
            dr = f_rs[f_rs['Nome_N'] == n].iloc[0]
            v_info = f_vn[f_vn['Giocatore_N'] == n] if f_vn is not None else None
            val_vinc = v_info['Tot_Vincolo'].iloc[0] if (v_info is not None and not v_info.empty) else 0
            durata_vinc = v_info['Anni_T'].iloc[0] if (v_info is not None and not v_info.empty) else "NO"
            st.markdown(f"""<div class="search-card"><div class="card-header"><span class="player-name"><b>{n}</b></span><br><span class="team-name">{dr['Squadra_N']}</span></div><div class="stat-row"><span class="label">Acquisto:</span> <span class="valore"><b>{int(dr['Prezzo_N'])}</b></span><div class="clearfix"></div></div><div class="stat-row"><span class="label">Vincolo:</span> <span class="valore"><b>{int(val_vinc)}</b> ({durata_vinc})</span><div class="clearfix"></div></div><div class="quot-box"><span class="label" style="color:#2e7d32;">Quot:</span> <span class="valore"><b>{int(dr['Quotazione'])}</b></span><div class="clearfix"></div></div></div>""", unsafe_allow_html=True)

# --- MAIN APP ---
t = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "✂️ TAGLI"])

# ... (Tab 0, 1, 2, 3 omesse per brevità, sono identiche a prima)

with t[4]: # TAB 4: SCAMBI (RIPRISTINATA LOGICA NUOVI VALORI)
    st.subheader("🔄 SIMULATORE SCAMBI PROPORZIONALE")
    if f_rs is not None:
        c1, c2 = st.columns(2)
        l_sq = sorted([s for s in f_rs['Squadra_N'].unique() if s])
        with c1:
            sa = st.selectbox("SQUADRA A", l_sq, key="sa_69")
            ga = st.multiselect("GIOCATORI CEDUTI DA A", f_rs[f_rs['Squadra_N']==sa]['Nome_N'].tolist(), key="ga_69")
        with c2:
            sb = st.selectbox("SQUADRA B", [s for s in l_sq if s != sa], key="sb_69")
            gb = st.multiselect("GIOCATORI CEDUTI DA B", f_rs[f_rs['Squadra_N']==sb]['Nome_N'].tolist(), key="gb_69")
        
        if ga and gb:
            def get_valori(nome):
                p = f_rs[f_rs['Nome_N']==nome]['Prezzo_N'].iloc[0]
                v = f_vn[f_vn['Giocatore_N']==nome]['Tot_Vincolo'].iloc[0] if (f_vn is not None and nome in f_vn['Giocatore_N'].values) else 0
                return p, v, p + v

            # Calcolo Totali
            tot_ceduto_a = sum(get_valori(n)[2] for n in ga)
            tot_ceduto_b = sum(get_valori(n)[2] for n in gb)
            media_scambio = round((tot_ceduto_a + tot_ceduto_b) / 2)
            
            st.divider()
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric(f"Totale {sa}", f"{int(tot_ceduto_a)} cr")
            col_m2.metric(f"Totale {sb}", f"{int(tot_ceduto_b)} cr")
            col_m3.metric("Media Scambio", f"{media_scambio} cr")

            res_a, res_b = st.columns(2)
            with res_a:
                st.markdown(f"### 📥 {sa} RICEVE")
                for n in gb:
                    p_orig, v_orig, t_orig = get_valori(n)
                    # Proporzione: (Valore Tot Giocatore / Totale Ceduto da B) * Media Scambio
                    nuovo_valore_tot = (t_orig / tot_ceduto_b) * media_scambio
                    nuovo_prezzo = max(0, round(nuovo_valore_tot - v_orig))
                    st.markdown(f"""<div class="player-card card-blue"><b>{n}</b><br>NUOVO PREZZO: <b>{nuovo_prezzo}</b><br><small>VINCOLO: {int(v_orig)} | TOT: {int(nuovo_prezzo + v_orig)}</small></div>""", unsafe_allow_html=True)
            
            with res_b:
                st.markdown(f"### 📥 {sb} RICEVE")
                for n in ga:
                    p_orig, v_orig, t_orig = get_valori(n)
                    nuovo_valore_tot = (t_orig / tot_ceduto_a) * media_scambio
                    nuovo_prezzo = max(0, round(nuovo_valore_tot - v_orig))
                    st.markdown(f"""<div class="player-card card-red"><b>{n}</b><br>NUOVO PREZZO: <b>{nuovo_prezzo}</b><br><small>VINCOLO: {int(v_orig)} | TOT: {int(nuovo_prezzo + v_orig)}</small></div>""", unsafe_allow_html=True)
            
            # Impatto Patrimonio
            diff = media_scambio - tot_ceduto_a
            p_a_attuale = f_rs[f_rs['Squadra_N']==sa]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sa]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sa, 0)
            p_b_attuale = f_rs[f_rs['Squadra_N']==sb]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sb]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sb, 0)
            
            c_p1, c_p2 = st.columns(2)
            c_p1.markdown(f"""<div class="patrimonio-box">NUOVO PATRIMONIO {sa}<br><h2>{int(p_a_attuale + diff)}</h2><small>PRIMA: {int(p_a_attuale)}</small></div>""", unsafe_allow_html=True)
            c_p2.markdown(f"""<div class="patrimonio-box">NUOVO PATRIMONIO {sb}<br><h2>{int(p_b_attuale - diff)}</h2><small>PRIMA: {int(p_b_attuale)}</small></div>""", unsafe_allow_html=True)

with t[5]: # TAB 5: TAGLI
    st.subheader("✂️ SIMULATORE TAGLI")
    # ... (Stessa logica potenziata di prima)
