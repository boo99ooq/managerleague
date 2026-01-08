import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# CSS STYLE (Bolder & Cleaner)
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .search-card { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; color: #1a1a1a !important; margin-bottom: 10px; }
    .card-header { border-bottom: 2px solid #eee; margin-bottom: 10px; padding-bottom: 5px; }
    .player-name { color: #1a73e8; font-size: 1.1em; }
    .player-card { padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 8px solid; color: black !important; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .card-blue { background-color: #e3f2fd; border-color: #1a73e8; }
    .card-red { background-color: #fbe9e7; border-color: #d32f2f; }
</style>
""", unsafe_allow_html=True)

# --- SUPER TRADUTTORE NOMI (Risolve tutto il box rosso) ---
def clean_name_logic(name):
    if not isinstance(name, str): return name
    # Fix encoding del file quotazioni (caratteri mangiati)
    name = name.replace('Åˆ', 'O').replace('Ä', 'E').replace('Ä›', 'I').replace('č', 'E').replace('ň', 'O')
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    name = name.upper().strip()
    
    # DIZIONARIO SINONIMI (Tuo File <-> Listone)
    synonyms = {
        # Portieri
        'MONTIPO': 'MONTIPA', 'MARTINELLI T.': 'MARTINELLI', 'RAVAGLIA F.': 'RAVAGLIA',
        # Difensori
        'NDICKA': 'NDICKA', 'LUCUMI': 'LUCUMA', 'DODO': 'DODA', 'DIMARCO': 'DIMARCO',
        'PEZZELLA GIU.': 'PEZZELLA', 'KRISTENSEN T.': 'KRISTENSEN', 'MIRANDA J.': 'MIRANDA',
        'KOSSOUNOU': 'KOSSOUNOU', 'TAVARES N.': 'NUNO TAVARES', 'KAMARA H.': 'KAMARA',
        'KELLY L.': 'KELLY', 'RANIERI L.': 'RANIERI', 'GASPAR K.': 'GASPAR', 'OSTIGARD': 'OSTIGAARD',
        # Centrocampisti
        'EDERSON D.S.': 'EDERSON', 'RICCI S.': 'RICCI', 'NICOLUSSI CAVIGLIA': 'NICOLUSSI CAVIGLIA',
        'LOFTUS-CHEEK': 'LOFTUS CHEEK', 'NICO PAZ': 'PAZ N.', 'ZAMBO ANGUISSA': 'ANGUISSA',
        'BERNABE': 'BERNABA', 'MKHITARYAN': 'MKHTARYAN', 'SUCIC P.': 'SUCIC', 'TOURE E.': 'TOURE',
        # Attaccanti
        'SOULE': 'SOULE K', 'SOULE K': 'SOULE K', 'SOULE': 'SOULE', 'SOULE': 'SOULE',
        'MARTINEZ L.': 'LAUTARO', 'THURAM M.': 'THURAM M', 'ZAPATA D.': 'ZAPATA',
        'ADAMS C.': 'ADAMS', 'CASTRO S.': 'CASTRO', 'LAURIENTE': 'LAURIENTA',
        'DOMINGUEZ B': 'DOMINGUEZ B.', 'PELLEGRINO M.': 'PELLEGRINO', 'RODRIGUEZ J.': 'RODRIGUEZ J',
        'VITINHA O.': 'VITINHA', 'ESPOSITO F.P.': 'PIO ESPOSITO', 'ESPOSITO SE.': 'ESPOSITO',
        'THIAGO GABRIEL': 'GABRIEL', 'NDRI': 'AKINSANMIRO'
    }
    
    # Rimuove iniziali finali tipo "PAZ N." -> "PAZ" o "RICCI S." -> "RICCI"
    simple_name = re.sub(r'\s[A-Z]\.$', '', name)
    
    if name in synonyms: return synonyms[name]
    if simple_name in synonyms: return synonyms[simple_name]
    return name

# --- CARICAMENTO DATI ---
def load_data(file, is_quot=False):
    if not os.path.exists(file): return None
    df = pd.read_csv(file, encoding='latin1')
    df.columns = [c.strip() for c in df.columns]
    if is_quot:
        df['Match_Name'] = df['Nome'].apply(clean_name_logic)
        return df
    return df

# LOAD
f_rs = load_data("rose_complete.csv")
f_vn = load_data("vincoli.csv")
f_pt = load_data("classificapunti.csv")
f_sc = load_data("scontridiretti.csv")
f_qt = load_data("quotazioni.csv", is_quot=True)

# PRE-PROCESS ROSE
if f_rs is not None:
    f_rs['Nome_Match'] = f_rs['Nome'].apply(lambda x: clean_name_logic(str(x).upper().strip()))
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt[['Match_Name', 'Qt.A']], left_on='Nome_Match', right_on='Match_Name', how='left').fillna({'Qt.A': 0})
        f_rs = f_rs.rename(columns={'Qt.A': 'Quotazione'})

# --- SIDEBAR & RICERCA ---
with st.sidebar:
    st.header("🔍 RICERCA GIOCATORE")
    if f_rs is not None:
        scelte = st.multiselect("SELEZIONA", sorted(f_rs['Nome'].unique()))
        for n in scelte:
            row = f_rs[f_rs['Nome'] == n].iloc[0]
            st.markdown(f"""<div class="search-card"><b>{n}</b> ({row['Fantasquadra']})<br>VAL: {row['Prezzo']} | QUOT: {row['Quotazione']}</div>""", unsafe_allow_html=True)

# --- TABS ---
t = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "✂️ TAGLI"])

with t[2]: # ROSE
    if f_rs is not None:
        mancanti = f_rs[f_rs['Quotazione'] == 0]['Nome'].unique()
        if len(mancanti) > 0:
            with st.expander(f"⚠️ {len(mancanti)} GIOCATORI DA SISTEMARE O GIOVANI"):
                st.write(", ".join(sorted(mancanti)))
        
        sq = st.selectbox("SQUADRA", sorted(f_rs['Fantasquadra'].unique()))
        df_display = f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo', 'Quotazione']]
        st.table(df_display)

# (Altre TAB come nelle versioni precedenti...)
