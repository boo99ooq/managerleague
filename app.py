import streamlit as st
import pandas as pd
import os

# 1. SETUP E STILE
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("<style>.stApp{background-color:#f4f7f6;} .stTabs{background-color:white; border-radius:10px; padding:10px;}</style>", unsafe_allow_html=True)
st.title("⚽ MuyFantaManager")

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS"}

def cv(v):
    if pd.isna(v): return 0
    try: return float(str(v).replace('"', '').replace(',', '.'))
    except: return 0

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

f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")

# SIDEBAR RICERCA
if f_rs is not None:
    st.sidebar.header("🔍 Cerca Giocatore")
    s = st.sidebar.text_input("Nome:").upper()
    if s:
        res = f_rs[f_rs['Nome'].str.upper().str.contains(s, na=False)].copy()
        if not res.empty:
            res['Fantasquadra'] = res['Fantasquadra'].str.upper().str.strip().replace(map_n)
            st.sidebar.dataframe(res[['Nome', 'Fantasquadra', 'Prezzo']], hide_index=True)
        else: st.sidebar.warning("Nessuno trovato")

t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔥 Scontri")
        if f_sc is not None:
            f_sc['Giocatore'] = f_sc['Giocatore'].str.upper().str.strip().replace(map_n)
            st.dataframe(f_sc, hide_index=True, use_container_width=True)
    with c2:
        st.subheader("🎯 Punti")
        if f_pt is not None:
            f_pt['Giocatore'] = f_pt['Giocatore'].str.upper().str.strip().replace(map_n)
            f_pt['Punti Totali'] = f_pt['Punti Totali'].apply(cv)
            st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali','Media']].sort_values('Punti Totali', ascending=False), hide_index=True, use_container_width=True)

if f_rs is not None:
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)
    f_rs['Fantasquadra'] = f_rs['Fantasquadra'].str.upper().str.strip().replace(map_n)
    
    with t[1]: # BUDGET
        st.subheader("💰 Bilancio")
        eco = f_rs.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        eco['Extra'] = eco['Fantasquadra'].map(bg_ex).fillna(0)
        eco['Totale'] = (eco['Prezzo'] + eco['Extra']).astype(int)
        st.dataframe(eco.sort_values('Totale', ascending=False), hide_index=True, use_container_width=True)
    
    with t[2]: # STRATEGIA
        st.subheader("🧠 Strategia")
        cs1, cs2 = st.columns([1.5, 1])
        with cs1:
            st.write("**Distribuzione Ruoli**")
            piv = f_rs.pivot_table(index='Fantasquadra', columns='Ruolo', values='Nome', aggfunc='count').fillna(0).astype(int)
            # Ordinamento ruoli richiesto
            r_ord = ['Portiere', 'Difensore', 'Centrocampista', 'Attaccante', 'Giovani']
            col_esistenti = [r for r in r_ord if r in piv.columns]
            st.dataframe(piv[col_esistenti], use_container_width=True)
        with cs2:
            st.write("**💎 Top Player per Squadra**")
            idx = f_rs.groupby('Fantasquadra')['Prezzo'].idxmax()
            top = f_rs.loc[idx, ['Fantasquadra', 'Nome', 'Prezzo']].sort_values('Prezzo', ascending=False)
            st.dataframe(top, hide_index=True, use_container_width=True)

    with t[3]: # ROSE
        sq = st.selectbox("Squadra:", sorted(f_rs['Fantasquadra'].unique()))
        st.dataframe(f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo']].sort_values('Prezzo', ascending=False), hide_index=True, use_container_width=True)

with t[4]: # VINCOLI
    st.subheader("📅 Vincoli")
    if f_vn is not None:
        f_vn['Squadra'] = f_vn['Squadra'].str.upper().str.strip().replace(map_n)
        f_vn = f_vn[f_vn['Squadra'].isin(bg_ex.keys())].copy()
        f_vn['Costo 2026-27'] = f_vn['Costo 2026-27'].apply(cv)
        v1, v2 = st.columns([1, 2])
        with v1:
            st.dataframe(f_vn.groupby('Squadra')['Costo 2026-27'].sum().reset_index().sort_values('Costo 2026-27', ascending=False), hide_index=True, use_container_width=True)
        with v2:
            sv = st.selectbox("Squadra:", sorted(f_vn['Squadra'].unique()), key="v_sel")
            st.dataframe(f_vn[f_vn['Squadra'] == sv][['Giocatore', 'Costo 2026-27', 'Durata (anni)']], hide_index=True, use_container_width=True)
