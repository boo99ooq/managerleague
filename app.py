import streamlit as st
import pandas as pd
import os

# 1. SETUP E STILE
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("<style>.stApp{background-color:#f4f7f6;} .stTabs{background-color:white; border-radius:10px; padding:10px;}</style>", unsafe_allow_html=True)
st.title("⚽ MuyFantaManager")

# Configurazione Budget e Mappatura nomi
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {
    "NICO FABIO": "NICHOLAS", 
    "MATTEO STEFANO": "MATTEO", 
    "NICHO": "NICHOLAS", 
    "NICHO:79": "NICHOLAS",
    "DANI ROBI": "DANI ROBI"
}

def cv(v):
    if pd.isna(v): return 0
    try: return float(str(v).replace('"', '').replace(',', '.'))
    except: return 0

def clean_name(s):
    if pd.isna(s): return ""
    s = str(s).replace('*', '').replace('"', '').strip().upper()
    return map_n.get(s, s)

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, sep=',', engine='python', encoding='utf-8-sig', skip_blank_lines=True)
        df.columns = [c.strip() for c in df.columns]
        if df.columns[0].startswith('Unnamed'):
            df = pd.read_csv(f, sep=',', engine='python', encoding='utf-8-sig', skiprows=1)
            df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# 2. CARICAMENTO E PULIZIA
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")

if f_sc is not None: f_sc['Giocatore'] = f_sc['Giocatore'].apply(clean_name)
if f_pt is not None: f_pt['Giocatore'] = f_pt['Giocatore'].apply(clean_name)
if f_rs is not None: f_rs['Fantasquadra'] = f_rs['Fantasquadra'].apply(clean_name)
if f_vn is not None: f_vn['Squadra'] = f_vn['Squadra'].apply(clean_name)

# SIDEBAR RICERCA
if f_rs is not None:
    st.sidebar.header("🔍 Cerca Giocatore")
    s = st.sidebar.text_input("Nome:").upper()
    if s:
        res = f_rs[f_rs['Nome'].str.upper().str.contains(s, na=False)].copy()
        if not res.empty:
            st.sidebar.dataframe(res[['Nome', 'Fantasquadra', 'Prezzo']].style.format({"Prezzo": "{:g}"}), hide_index=True)
        else: st.sidebar.warning("Nessuno trovato")

t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔥 Scontri")
        if f_sc is not None: st.dataframe(f_sc, hide_index=True, use_container_width=True)
    with c2:
        st.subheader("🎯 Punti")
        if f_pt is not None:
            f_pt['Punti Totali'] = f_pt['Punti Totali'].apply(cv)
            st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali','Media']].sort_values('Punti Totali', ascending=False).style.format({"Punti Totali": "{:g}", "Media": "{:.2f}"}), hide_index=True, use_container_width=True)

if f_rs is not None:
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)
    with t[1]: # BUDGET
        st.subheader("💰 Bilancio Globale")
        eco = f_rs.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        eco['Extra'] = eco['Fantasquadra'].map(bg_ex).fillna(
