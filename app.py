import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Lega Manager", layout="wide")
st.markdown("<style>.stApp{background-color:#f4f7f6;} .stTabs{background-color:white; border-radius:10px; padding:10px;}</style>", unsafe_allow_html=True)
st.title("⚽ Centro Direzionale Fantalega")

# 1. DIZIONARIO BUDGET & MAPPATURA NOMI
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_nomi = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS"}

def clean_val(v):
    """Sana i numeri con virgole o virgolette"""
    if pd.isna(v): return 0
    s = str(v).replace('"', '').replace(',', '.')
    try: return float(s)
    except: return 0

def ld(f_name):
    """Caricamento e pulizia nomi colonne"""
    if not os.path.exists(f_name): return None
    try:
        df = pd.read_csv(f_name, sep=None, engine='python', encoding='utf-8-sig').dropna(how='all')
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return None

# 2. CARICAMENTO
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")

t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

# --- TAB 1: CLASSIFICHE ---
with t[0]:
    c1, c2 = st.columns(2)
    if f_sc is not None:
        with c1:
            st.subheader("🔥 Scontri Diretti")
            f_sc['Giocatore'] = f_sc['Giocatore'].replace(map_nomi)
            st.dataframe(f_sc, hide_index=True)
    if f_pt is not None:
        with c2:
            st.subheader("🎯 Classifica Punti")
            f_pt['Giocatore'] = f_pt['Giocatore'].replace(map_nomi)
            f_pt['Punti Totali'] = f_pt['Punti Totali'].apply(clean_val)
            st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali','Media']].sort_values('Punti Totali', ascending=False), hide_index=True)

# --- LOGICA ROSE (Budget, Strategia, Rose) ---
if f_rs is not None:
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(clean_val)
    f_rs['Fantasquadra'] = f_rs['Fantasquadra'].str.upper().strip().replace(map_nomi)
    
    with t[1]: # BUDGET
        st.subheader("💰 Bilancio Crediti")
        eco = f_rs.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        eco['Extra'] = eco['Fantasquadra'].map(bg_ex).fillna(0)
        eco['Totale'] = (eco['Prezzo'] + eco['Extra']).astype(int)
        st.dataframe(eco.sort_values('Totale', ascending=False), hide_index=True)
    
    with t[2]: # STRATEGIA
        st.subheader("🧠 Distribuzione Ruoli")
        piv = f_rs.pivot_table(index='Fantasquadra', columns='Ruolo', values='Nome', aggfunc='count').fillna(0).astype(int)
        st.dataframe(piv)

    with t[3]: # ROSE
        sq = st.selectbox("Squadra:", sorted(f_rs['Fantasquadra'].unique()))
        df_sq = f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo']].sort_values('Prezzo', ascending=False)
        st.dataframe(df_sq, hide_index=True)

# --- TAB 5: VINCOLI ---
if f_vn is not None:
    with t[4]:
        st.subheader("📅 Gestione Vincoli")
        # Filtra via le righe di testo descrittivo
        f_vn = f_vn[f_vn['Squadra'].isin(bg_ex.keys()) | f_vn['Squadra'].str.upper().isin(map_nomi.keys())].copy()
        f_vn['Squadra'] = f_vn['Squadra'].str.upper().replace(map_nomi)
        f_vn['Costo 2026-27'] = f_vn['Costo 2026-27'].apply(clean_val)
        
        v1, v2 = st.columns([1, 2])
        with v1:
            st.write("**Crediti Impegnati**")
            deb = f_vn.groupby('Squadra')['Costo 2026-27'].sum().reset_index().sort_values('Costo 2026-27', ascending=False)
            st.dataframe(deb, hide_index=True)
        with v2:
            st.write("**Dettaglio Giocatori**")
            sq_v = st.selectbox("Seleziona Squadra:", sorted(f_vn['Squadra'].unique()), key="v_sel")
            det = f_vn[f_vn['Squadra'] == sq_v][['Giocatore', 'Costo 2026-27', 'Durata (anni)']]
            st.dataframe(det, hide_index=True)
