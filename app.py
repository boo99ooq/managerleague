import streamlit as st
import pandas as pd
import os
import altair as alt

# 1. SETUP E STILE
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

# Configurazione Crediti Extra e Mappature
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- FUNZIONI DI PULIZIA ---
def cv(v):
    if pd.isna(v) or str(v).strip() == "": return 0.0
    try:
        s = str(v).replace('"', '').replace('.', '').replace(',', '.').strip()
        return float(s)
    except: return 0.0

def clean_s(s):
    if pd.isna(s): return ""
    # Rimuove asterischi e spazi
    return str(s).replace('*', '').strip().upper()

def ld(f):
    if not os.path.exists(f): return None
    try:
        # Legge saltando righe vuote e corregge l'errore del file rose
        df = pd.read_csv(f, engine='python', skip_blank_lines=True)
        if df.columns[0].startswith('Unnamed') or df.empty:
            df = pd.read_csv(f, skiprows=1, engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# --- CARICAMENTO DATI ---
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")

# --- PRE-ELABORAZIONE ---
if f_rs is not None:
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(cv)
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_s).replace(map_n)

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_s).replace(map_n)
    v_cols = [c for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29'] if c in f_vn.columns]
    for c in v_cols: f_vn[c] = f_vn[c].apply(cv)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)

# --- TABS ---
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli"])

# --- TAB 1: CLASSIFICHE ---
with t[0]:
    c1, c2 = st.columns(2)
    with c1:
        if f_pt is not None:
            st.subheader("🎯 Classifica Punti")
            f_pt['Punti'] = f_pt['Punti Totali'].apply(cv)
            f_pt['FM'] = f_pt['Media'].apply(cv)
            # Gradiente su Punti e FM
            st.dataframe(f_pt[['Posizione','Giocatore','Punti','FM']].sort_values('Posizione')
                         .style.background_gradient(subset=['Punti'], cmap='Greens')
                         .background_gradient(subset=['FM'], cmap='YlGn')
                         .format({"Punti": "{:g}", "FM": "{:.2f}"}), hide_index=True, use_container_width=True)
    with c2:
        if f_sc is not None:
            st.subheader("⚔️ Scontri Diretti")
            f_sc['Punti_S'] = f_sc['Punti'].apply(cv)
            st.dataframe(f_sc[['Posizione','Giocatore','Punti_S','Gol Fatti','Gol Subiti']]
                         .style.background_gradient(subset=['Punti_S'], cmap='Blues')
                         .format({"Punti_S": "{:g}"}), hide_index=True, use_container_width=True)

# --- TAB 2: BUDGET (CON GRADIENTI SU TUTTO) ---
with t[1]:
    if f_rs is not None:
        st.subheader("💰 Bilancio Globale (Valore Reale)")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index()
        bu.columns = ['Squadra', 'Spesa Rose']
        
        if f_vn is not None:
            v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index()
            bu = pd.merge(bu, v_sum, left_on='Squadra', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1)
            bu.rename(columns={'Tot_Vincolo': 'Spesa Vincoli'}, inplace=True)
        else: bu['Spesa Vincoli'] = 0
        
        bu['Crediti Disponibili'] = bu['Squadra'].map(bg_ex).fillna(0)
        bu['Patrimonio Reale'] = bu['Spesa Rose'] + bu['Spesa Vincoli'] + bu['Crediti Disponibili']
        
        # Applichiamo gradienti a tutte le colonne numeriche
        num_cols = bu.select_dtypes('number').columns
        st.dataframe(bu.sort_values('Patrimonio Reale', ascending=False)
                     .style.background_gradient(cmap='YlOrRd', subset=num_cols)
                     .format({c: "{:g}" for c in num_cols}), hide_index=True, use_container_width=True)

# --- TAB 3: ROSE ---
with t[2]:
    if f_rs is not None:
        # Pulizia menu a tendina: rimuove nomi con asterischi o vuoti
        lista_sq = sorted([s for s in f_rs['Squadra_N'].unique() if s and '*' not in s])
        sq = st.selectbox("Seleziona Squadra:", lista_sq)
        df_sq = f_rs[f_rs['Squadra_N'] == sq].copy()
        
        def color_ruoli(row):
            r = str(row['Ruolo']).upper()
            bg = '#E3F2FD' if 'PORT' in r else '#E8F5E9' if 'DIF' in r else '#FFFDE7' if 'CEN' in r else '#FFEBEE' if 'ATT' in r else '#FFFFFF'
            return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
        
        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo_N']].style.apply(color_ruoli, axis=1)
                     .format({"Prezzo_N": "{:g}"}), hide_index=True, use_container_width=True)

# --- TAB 4: VINCOLI ---
with t[3]:
    if f_vn is not None:
        st.subheader("📅 Contratti Pluriennali")
        lista_sq_v = sorted([s for s in f_vn['Sq_N'].unique() if s and
