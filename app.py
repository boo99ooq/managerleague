import streamlit as st
import pandas as pd
import os

# 1. SETUP
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

# Configurazione Crediti
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- FUNZIONI DI PULIZIA ---
def clean_name_only(s):
    """Rimuove asterischi, numeri dopo i due punti e spazi (es: ANDREA:49 -> ANDREA)"""
    if pd.isna(s): return ""
    text = str(s).split(':')[0] # Prende tutto quello che c'è prima di eventuali ":"
    return text.replace('*', '').strip().upper()

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True)
        if df.columns[0].startswith('Unnamed') or df.empty:
            df = pd.read_csv(f, skiprows=1, engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# CARICAMENTO
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")

# ELABORAZIONE
if f_rs is not None:
    f_rs['Prezzo_N'] = pd.to_numeric(f_rs['Prezzo'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_name_only).replace(map_n)

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_name_only).replace(map_n)
    v_cols = [c for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29'] if c in f_vn.columns]
    for c in v_cols: 
        f_vn[c] = pd.to_numeric(f_vn[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn = f_vn.drop_duplicates(subset=['Sq_N', 'Giocatore'])

t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    with c1:
        if f_pt is not None:
            st.subheader("🎯 Punti")
            f_pt['Punti'] = pd.to_numeric(f_pt['Punti Totali'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            f_pt['FM'] = pd.to_numeric(f_pt['Media'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            st.dataframe(f_pt[['Posizione','Giocatore','Punti','FM']].sort_values('Posizione')
                         .style.background_gradient(subset=['Punti', 'FM'], cmap='YlGn')
                         .format({"Punti": "{:g}", "FM": "{:.2f}"}), hide_index=True, use_container_width=True)
    with c2:
        if f_sc is not None:
            st.subheader("⚔️ Scontri Diretti")
            f_sc['Punti_S'] = pd.to_numeric(f_sc['Punti'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            st.dataframe(f_sc[['Posizione','Giocatore','Punti_S','Gol Fatti','Gol Subiti']]
                         .style.background_gradient(subset=['Punti_S'], cmap='Blues')
                         .format({"Punti_S": "{:g}"}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        st.subheader("💰 Bilancio Globale")
        bu = f_rs.groupby
