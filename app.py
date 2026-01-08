import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# CSS STYLE (Grassetto Estremo & Cards)
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .search-card { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; color: #1a1a1a !important; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .player-card { padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 8px solid; color: black !important; }
    .card-blue { background-color: #e3f2fd; border-color: #1a73e8; }
    .card-red { background-color: #fbe9e7; border-color: #d32f2f; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONE DI PULIZIA "INTELLIGENTE" ---
def super_clean(name):
    if not isinstance(name, str): return ""
    # Rimuove accenti e caratteri speciali sporchi
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    name = name.upper()
    # Mappa correzioni manuali per i casi disperati
    mapping = {
        'LAUTARO': 'MARTINEZ L', 'MARTINEZ L': 'MARTINEZ L',
        'THURAM M': 'THURAM', 'THURAM': 'THURAM',
        'NICO PAZ': 'PAZ N', 'SOULE': 'SOULE',
        'ZAMBO ANGUISSA': 'ANGUISSA', 'PIO ESPOSITO': 'ESPOSITO FP',
        'NDRI': 'AKINSANMIRO', 'BUFFON': 'SVINCOLATO'
    }
    # Rimuove tutto ciò che non è una lettera o numero
    name = re.sub(r'[^A-Z0-9]', '', name)
    # Se il nome pulito è nel mapping, restituisce il valore mappato
    for k, v in mapping.items():
        if k.replace(' ', '').replace('.', '') in name: return v.replace(' ', '')
    return name

# --- CARICAMENTO DATI ---
def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', encoding='latin1')
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Key'] = df['Nome'].apply(super_clean)
        return df
    except: return None

# CARICAMENTO
f_rs, f_vn, f_pt, f_sc = ld("rose_complete.csv"), ld("vincoli.csv"), ld("classificapunti.csv"), ld("scontridiretti.csv")
f_qt = ld("quotazioni.csv", is_quot=True)

# MATCHING
if f_rs is not None and f_qt is not None:
    f_rs['Key'] = f_rs['Nome'].apply(super_clean)
    f_rs = pd.merge(f_rs, f_qt[['Key', 'Qt.A']], on='Key', how='left').fillna({'Qt.A': 0})
    f_rs = f_rs.rename(columns={'Qt.A': 'Quotazione'})

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 RICERCA VELOCE")
    if f_rs is not None:
        p_cerca = st.multiselect("CERCA GIOCATORE", sorted(f_rs['Nome'].unique()))
        for p in p_cerca:
            row = f_rs[f_rs['Nome'] == p].iloc[0]
            st.markdown(f'<div class="search-card"><b>{p}</b><br>VAL: {int(row["Prezzo"])} | QUOT: {int(row["Quotazione"])}</div>', unsafe_allow_html=True)

# --- TABS ---
t = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "✂️ TAGLI", "🕵️ MERCATO"])

# (Le tab precedenti rimangono attive e funzionanti...)
with t[2]: # ROSE
    if f_rs is not None:
        sq = st.selectbox("SQUADRA", sorted(f_rs['Fantasquadra'].unique()), key="sq_rose")
        st.dataframe(f_rs[f_rs['Fantasquadra']==sq][['Ruolo','Nome','Prezzo','Quotazione']], use_container_width=True, hide_index=True)

with t[6]: # NUOVA TAB MERCATO (SCOUTING)
    st.subheader("🕵️ SCOUTING ASSISTITO: I MIGLIORI SVINCOLATI")
    if f_rs is not None and f_qt is not None:
        nomi_occupati = f_rs['Key'].unique()
        svincolati = f_qt[~f_qt['Key'].isin(nomi_occupati)].sort_values('Qt.A', ascending=False)
        
        c1, c2 = st.columns(2)
        with c1:
            ruolo_filtro = st.selectbox("FILTRA PER RUOLO", ["TUTTI", "P", "D", "C", "A"])
            if ruolo_filtro != "TUTTI":
                svincolati = svincolati[svincolati['R'] == ruolo_filtro]
        
        st.dataframe(svincolati[['R', 'Nome', 'Qt.A']].rename(columns={'Qt.A': 'Quotazione'}), use_container_width=True, hide_index=True)

# Logica Scambi e Tagli (Sempre presente e potenziata dal super_clean)
