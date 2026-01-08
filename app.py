import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide")

st.markdown("""<style>html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }</style>""", unsafe_allow_html=True)

# FUNZIONE PULIZIA AUTOMATICA
def clean_quotazioni_name(name):
    if not isinstance(name, str): return name
    name = name.replace('č', 'e').replace('ň', 'o').replace('ř', 'i').replace('ć', 'c').replace('Č', 'E').replace('Ň', 'O').replace('ň', 'o').replace('ň', 'o')
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    name = name.upper().strip()
    mapping = {
        'ESPOSITO F.P.': 'PIO ESPOSITO', 'ESPOSITO SE.': 'S ESPOSITO',
        'DAVIS K.': 'DAVIS K', 'MARTINEZ L.': 'LAUTARO',
        'MARTINEZ JO.': 'MARTINEZ JO', 'PELLEGRINO M.': 'PELLEGRINO',
        'ADAMS C.': 'ADAMS', 'DYBALA P.': 'DYBALA', 'VLAHOVIC D.': 'VLAHOVIC',
        'SOULC': 'SOULE', 'LAURIENTC': 'LAURIENTE', 'MONTIPN': 'MONTIPO'
    }
    if name in mapping: return mapping[name]
    name = re.sub(r'\s[A-Z]\.$', '', name)
    name = re.sub(r'\s[A-Z]\.[A-Z]\.$', '', name)
    return name

# CARICAMENTO FILE
def ld(f, is_quot=False):
    if not os.path.exists(f): 
        if is_quot: st.error(f"⚠️ FILE {f} NON TROVATO! Caricalo su GitHub.")
        return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True)
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Nome'] = df['Nome'].apply(clean_quotazioni_name)
            return df[['Nome', 'Qt.A']].rename(columns={'Qt.A': 'Quotazione'})
        return df.dropna(how='all')
    except Exception as e:
        st.error(f"Errore caricamento {f}: {e}")
        return None

def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str.upper()

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

# LOAD
f_rs = ld("rose_complete.csv")
f_vn = ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Nome'] = f_rs['Nome'].apply(clean_string)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, on='Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_string)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# MAIN APP
st.title("⚽ MUYFANTAMANAGER GOLDEN V2")
t = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "✂️ TAGLI"])

with t[2]: # ROSE
    if f_rs is not None:
        sq = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="rose_sel")
        cols = ['Ruolo', 'Nome', 'Prezzo_N']
        if 'Quotazione' in f_rs.columns: cols.append('Quotazione')
        df_sq = f_rs[f_rs['Squadra_N'] == sq][cols]
        
        def color_ruoli(row):
            r = str(row['Ruolo']).upper()
            if 'POR' in r: bg = '#FCE4EC' 
            elif 'DIF' in r: bg = '#E8F5E9' 
            elif 'CEN' in r: bg = '#E3F2FD' 
            elif 'ATT' in r: bg = '#FFFDE7' 
            else: bg = '#FFFFFF'
            return [f'background-color: {bg}; color: black; font-weight: 900;'] * len(row)
        
        st.dataframe(df_sq.style.apply(color_ruoli, axis=1).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)
    else:
        st.warning("File rose_complete.csv non trovato.")

# AGGIUNGI QUI IL RESTO DELLE TAB (0, 1, 3, 4, 5) DEL MESSAGGIO PRECEDENTE
