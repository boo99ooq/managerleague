import streamlit as st
import pandas as pd
import os

# 1. SETUP E STILE
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("<style>.stApp{background-color:#f4f7f6;} .stTabs{background-color:white; border-radius:10px; padding:10px;}</style>", unsafe_allow_html=True)
st.title("⚽ MuyFantaManager")

# Configurazione Budget e Mappatura nomi
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_nomi = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS"}

def clean_val(v):
    if pd.isna(v): return 0
    s = str(v).replace('"', '').replace(',', '.')
    try: return float(s)
    except: return 0

def ld(f_name):
    if not os.path.exists(f_name): return None
    try:
        df = pd.read_csv(f_name, sep=',', engine='python', encoding='utf-8-sig', skip_blank_lines=True)
        df.columns = [c.strip() for c in df.columns]
        if df.columns[0].startswith('Unnamed'):
            df = pd.read_csv(f_name, sep=',', engine='python', encoding='utf-8-sig', skiprows=1)
            df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# 2. CARICAMENTO DATI
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")

# --- NUOVA FUNZIONE: RICERCA GIOCATORE NELLA SIDEBAR ---
if f_rs is not None:
    st.sidebar.header("🔍 Cerca Giocatore")
    search = st.sidebar.text_input("Inserisci nome:", "").upper()
    if search:
        # Filtra per nome (contiene la stringa cercata)
        risultati = f_rs[f_rs['Nome'].str.upper().str.contains(search, na=False)].copy()
        if not risultati.empty:
            st.sidebar.success(f"Trovati {len(risultati)} giocatori:")
            # Pulizia per la visualizzazione in sidebar
            risultati['Fantasquadra'] = risultati['Fantasquadra'].str.upper().replace(map_nomi)
            st.sidebar.dataframe(risultati[['Nome', 'Fantasquadra', 'Prezzo']], hide_index=True)
        else:
            st.sidebar.warning("Nessun giocatore trovato.")

# 3. CREAZIONE TAB
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

# --- TAB 1: CLASSIFICHE ---
with t[0]:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔥 Scontri")
        if f_sc is not None:
            f_sc['Giocatore'] = f_sc['Giocatore'].str.upper().replace(map_nomi)
            st.dataframe(f_sc, hide_index=True, use_container_width=True)
    with c2:
        st.subheader("🎯 Punti")
        if f_pt is not None:
            f_pt['Giocatore'] = f_pt['Giocatore'].str.upper().replace(map_nomi)
            f_pt['Punti Totali'] = f_pt['Punti Totali'].apply(clean_val)
            st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali','Media']].sort_values('Punti Totali', ascending=False), hide_index=True, use_container_width=True)

# --- TAB BUDGET / STRATEGIA / ROSE ---
if f_rs is not None:
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(clean_val)
    f_rs['Fantasquadra'] = f_rs['Fantasquadra'].str.upper().str.strip().replace(map_nomi)
    
    with t[1]: # BUDGET
        st.subheader("💰 Bilancio Crediti")
        eco = f_rs.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        eco['Extra'] = eco['Fantasquadra'].map(bg_ex).fillna(
