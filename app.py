import streamlit as st
import pandas as pd
import os

# 1. SETUP E STILE
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("<style>.stApp{background-color:#f4f7f6;} .stTabs{background-color:white; border-radius:10px; padding:10px;}</style>", unsafe_allow_html=True)
st.title("⚽ MuyFantaManager")

# Configurazione Budget e Mappatura nomi (estesa per accorpare tutto)
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {
    "NICO FABIO": "NICHOLAS", 
    "MATTEO STEFANO": "MATTEO", 
    "NICHO": "NICHOLAS", 
    "NICHO:79": "NICHOLAS",
    "NICHOLAS": "NICHOLAS",
    "MATTEO": "MATTEO",
    "DANI ROBI": "DANI ROBI"
}

def cv(v):
    if pd.isna(v): return 0
    try: return float(str(v).replace('"', '').replace(',', '.'))
    except: return 0

def clean_name(s):
    """Pulizia totale: rimuove asterischi, numeri dopo i due punti e spazi"""
    if pd.isna(s): return ""
    # Rimuove tutto ciò che viene dopo un eventuale ':' (es. NICHO:79 -> NICHO)
    s = str(s).split(':')[0]
    # Toglie asterischi e spazi bianchi
    s = s.replace('*', '').replace('"', '').strip().upper()
    # Applica mappatura finale
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

# --- TABELLE ---

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
        eco['Extra'] = eco['Fantasquadra'].map(bg_ex).fillna(0)
        if f_vn is not None:
            f_vn['Costo 2026-27'] = f_vn['Costo 2026-27'].apply(cv)
            vin_sum = f_vn.groupby('Squadra')['Costo 2026-27'].sum().reset_index()
            vin_sum.columns = ['Fantasquadra', 'Vincoli']
            eco = pd.merge(eco, vin_sum, on='Fantasquadra', how='left').fillna(0)
        else: eco['Vincoli'] = 0
        eco['Totale'] = eco['Prezzo'] + eco['Extra'] + eco['Vincoli']
        st.dataframe(eco.sort_values('Totale', ascending=False).style.background_gradient(subset=['Totale'], cmap='RdYlGn').format({"Prezzo": "{:g}", "Extra": "{:g}", "Vincoli": "{:g}", "Totale": "{:g}"}), hide_index=True, use_container_width=True)
    
    with t[2]: # STRATEGIA
        st.subheader("🧠 Strategia")
        cs1, cs2 = st.columns([1.5, 1])
        with cs1:
            piv = f_rs.pivot_table(index='Fantasquadra', columns='Ruolo', values='Nome', aggfunc='count').fillna(0).astype(int)
            r_ord = ['Portiere', 'Difensore', 'Centrocampista', 'Attaccante', 'Giovani']
            st.dataframe(piv[[r for r in r_ord if r in piv.columns]], use_container_width=True)
        with cs2:
            st.write("**💎 Top Player**")
            idx = f_rs.groupby('Fantasquadra')['Prezzo'].idxmax()
            st.dataframe(f_rs.loc[idx, ['Fantasquadra', 'Nome', 'Prezzo']].sort_values('Prezzo', ascending=False).style.format({"Prezzo": "{:g}"}), hide_index=True, use_container_width=True)

    with t[3]: # ROSE
        # Fix duplicati menu Rose
        sq_list = sorted(list(set(f_rs['Fantasquadra'].unique())))
        sq = st.selectbox("Seleziona Squadra:", sq_list)
        st.dataframe(f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo']].sort_values('Prezzo', ascending=False).style.format({"Prezzo": "{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # VINCOLI
    st.subheader("📅 Gestione Vincoli")
    if f_vn is not None:
        if 'Durata (anni)' in f_vn.columns:
            f_vn['Durata (anni)'] = f_vn['Durata (anni)'].apply(cv)
            
        v1, v2 = st.columns([1, 2])
        with v1:
            st.write("**Riepilogo Investimenti**")
            deb = f_vn.groupby('Squadra')['Costo 2026-27'].sum().reset_index().sort_values('Costo 2026-27', ascending=False)
            st.dataframe(deb.style.format({"Costo 2026-27": "{:g}"}), hide_index=True, use_container_width=True)
        with v2:
            # Fix duplicati menu Vincoli: set() rimuove i duplicati, sorted() li ordina
            lista_sq = sorted(list(set(f_vn['Squadra'].unique())))
            sv = st.selectbox("Seleziona Squadra per Dettaglio:", lista_sq, key="v_sel")
            det = f_vn[f_vn['Squadra'] == sv][['Giocatore', 'Costo 2026-27', 'Durata (anni)']]
            st.dataframe(det.style.format({"Costo 2026-27": "{:g}", "Durata (anni)": "{:g}"}), hide_index=True, use_container_width=True)
