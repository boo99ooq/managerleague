import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Lega Manager", layout="wide")
st.markdown("<style>.stApp{background-color:#f4f7f6;} .stTabs{background-color:white; border-radius:10px; padding:10px;}</style>", unsafe_allow_html=True)
st.title("⚽ MuyFantaManager")

# 1. SETUP DATI E MAPPATURA
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_nomi = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

def clean_val(v):
    if pd.isna(v): return 0
    s = str(v).replace('"', '').replace(',', '.')
    try: return float(s)
    except: return 0

def ld(f_name):
    if not os.path.exists(f_name): return None
    try:
        # skiprows=1 serve per saltare la riga vuota all'inizio di rose_complete.csv
        df = pd.read_csv(f_name, sep=',', engine='python', encoding='utf-8-sig', skip_blank_lines=True)
        # Se la prima colonna è innominata o il file ha iniziato male, riproviamo senza skip
        if df.columns[0].startswith('Unnamed'):
             df = pd.read_csv(f_name, sep=',', engine='python', encoding='utf-8-sig')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# 2. CARICAMENTO
f_sc = ld("scontridiretti.csv")
f_pt = ld("classificapunti.csv")
f_rs = ld("rose_complete.csv")
f_vn = ld("vincoli.csv")

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
    # Pulizia specifica per rose_complete
    if 'Prezzo' in f_rs.columns:
        f_rs['Prezzo'] = f_rs['Prezzo'].apply(clean_val)
    if 'Fantasquadra' in f_rs.columns:
        f_rs['Fantasquadra'] = f_rs['Fantasquadra'].str.upper().str.strip().replace(map_nomi)
    
    with t[1]: # BUDGET
        st.subheader("💰 Bilancio Crediti")
        if 'Fantasquadra' in f_rs.columns and 'Prezzo' in f_rs.columns:
            eco = f_rs.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
            eco['Extra'] = eco['Fantasquadra'].map(bg_ex).fillna(0)
            eco['Totale'] = (eco['Prezzo'] + eco['Extra']).astype(int)
            st.dataframe(eco.sort_values('Totale', ascending=False), hide_index=True, use_container_width=True)
    
    with t[2]: # STRATEGIA
        st.subheader("🧠 Distribuzione Ruoli")
        if all(x in f_rs.columns for x in ['Fantasquadra', 'Ruolo', 'Nome']):
            piv = f_rs.pivot_table(index='Fantasquadra', columns='Ruolo', values='Nome', aggfunc='count').fillna(0).astype(int)
            st.dataframe(piv, use_container_width=True)

    with t[3]: # ROSE
        st.subheader("🏃 Dettaglio Rose")
        if 'Fantasquadra' in f_rs.columns:
            sq = st.selectbox("Seleziona Squadra:", sorted(f_rs['Fantasquadra'].unique()))
            df_sq = f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo']].sort_values('Prezzo', ascending=False)
            st.dataframe(df_sq, hide_index=True, use_container_width=True)
else:
    for i in [1,2,3]:
        with t[i]: st.error("⚠️ Errore di lettura in 'rose_complete.csv'. Controlla che il file non sia vuoto.")

# --- TAB 5: VINCOLI ---
with t[4]:
    st.subheader("📅 Gestione Vincoli")
    if f_vn is not None:
        f_vn['Squadra'] = f_vn['Squadra'].str.upper().str.strip().replace(map_nomi)
        # Filtro per tenere solo le squadre valide
        f_vn = f_vn[f_vn['Squadra'].isin(bg_ex.keys())].copy()
        f_vn['Costo 2026-27'] = f_vn['Costo 2026-27'].apply(clean_val)
        
        v1, v2 = st.columns([1, 2])
        with v1:
            st.write("**Crediti Impegnati**")
            deb = f_vn.groupby('Squadra')['Costo 2026-27'].sum().reset_index().sort_values('Costo 2026-27', ascending=False)
            st.dataframe(deb, hide_index=True, use_container_width=True)
        with v2:
            sq_v = st.selectbox("Dettaglio:", sorted(f_vn['Squadra'].unique()), key="v_sel")
            st.dataframe(f_vn[f_vn['Squadra'] == sq_v][['Giocatore', 'Costo 2026-27', 'Durata (anni)']], hide_index=True, use_container_width=True)

