import streamlit as st
import pandas as pd
import os
import altair as alt

# 1. SETUP UI E STILE
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

# Configurazioni Fisse
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- FUNZIONI DI PULIZIA ---
def cv(v):
    if pd.isna(v) or str(v).strip() == "": return 0.0
    s = str(v).replace('"', '').strip()
    if "." in s and "," in s: s = s.replace(".", "")
    s = s.replace(",", ".")
    try: return float(s)
    except: return 0.0

def ld(f):
    if not os.path.exists(f): return None
    try:
        # Legge il file e controlla se la prima riga è vuota (Unnamed)
        df = pd.read_csv(f, engine='python', skip_blank_lines=True)
        if df.columns[0].startswith('Unnamed') or df.empty:
            df = pd.read_csv(f, skiprows=1, engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# --- CARICAMENTO DATI ---
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")

# --- ELABORAZIONE BUDGET E VINCOLI ---
if f_rs is not None:
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(cv)
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].astype(str).str.upper().str.strip().replace(map_n)

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].astype(str).str.upper().str.strip().replace(map_n)
    v_cols = [c for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29'] if c in f_vn.columns]
    for c in v_cols: f_vn[c] = f_vn[c].apply(cv)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)

# --- CREAZIONE TAB ---
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli"])

# --- TAB 1: CLASSIFICHE ---
with t[0]:
    c1, c2 = st.columns(2)
    with c1:
        if f_pt is not None:
            st.subheader("🎯 Classifica Punti")
            f_pt['Punti_N'] = f_pt['Punti Totali'].apply(cv)
            st.dataframe(f_pt[['Posizione','Giocatore','Punti_N']].sort_values('Posizione').style.background_gradient(subset=['Punti_N'], cmap='Greens').format({"Punti_N": "{:g}"}), hide_index=True, use_container_width=True)
    with c2:
        if f_sc is not None:
            st.subheader("⚔️ Scontri Diretti")
            f_sc['Punti'] = f_sc['Punti'].apply(cv)
            st.dataframe(f_sc.style.background_gradient(subset=['Punti'], cmap='Blues').format({"Punti": "{:g}"}), hide_index=True, use_container_width=True)

# --- TAB 2: BUDGET (SOMMA COMPLESSIVA) ---
with t[1]:
    if f_rs is not None:
        st.subheader("💰 Bilancio Globale Crediti")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index()
        bu.columns = ['Squadra', 'Spesa Rose']
        
        if f_vn is not None:
            v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index()
            bu = pd.merge(bu, v_sum, left_on='Squadra', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1)
            bu.rename(columns={'Tot_Vincolo': 'Impegno Vincoli'}, inplace=True)
        else: bu['Impegno Vincoli'] = 0
        
        bu['Extra'] = bu['Squadra'].map(bg_ex).fillna(0)
        bu['Patrimonio Totale'] = bu['Spesa Rose'] + bu['Impegno Vincoli'] + bu['Extra']
        
        # Formattazione sicura per evitare ValueError
        num_cols = bu.select_dtypes(include=['number']).columns
        st.dataframe(bu.sort_values('Patrimonio Totale', ascending=False).style.background_gradient(subset=['Patrimonio Totale'], cmap='YlOrRd').format({c: "{:g}" for c in num_cols}), hide_index=True, use_container_width=True)

# --- TAB 3: ROSE ---
with t[2]:
    if f_rs is not None:
        sq = st.selectbox("Seleziona Squadra:", sorted(f_rs['Squadra_N'].unique()))
        df_sq = f_rs[f_rs['Squadra_N'] == sq].copy()
        
        def color_ruoli(row):
            r = str(row['Ruolo']).upper()
            bg = '#E3F2FD' if 'PORT' in r else '#E8F5E9' if 'DIF' in r else '#FFFDE7' if 'CEN' in r else '#FFEBEE' if 'ATT' in r else '#FFFFFF'
            return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
        
        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo_N']].style.apply(color_ruoli, axis=1).format({"Prezzo_N": "{:g}"}), hide_index=True, use_container_width=True)

# --- TAB 4: VINCOLI ---
with t[3]:
    if f_vn is not None:
        st.subheader("📅 Contratti Pluriennali")
        sq_v = st.selectbox("Filtra per Squadra:", ["TUTTE"] + sorted(f_vn['Sq_N'].unique()))
        df_v_display = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        
        num_cols_v = df_v_display.select_dtypes(include=['number']).columns
        st.dataframe(df_v_display[['Squadra', 'Giocatore', 'Tot_Vincolo'] + [c for c in v_cols if c in df_v_display.columns]].style.background_gradient(subset=['Tot_Vincolo'], cmap='Purples').format({c: "{:g}" for c in num_cols_v}), hide_index=True, use_container_width=True)
        
        if sq_v != "TUTTE":
            st.metric(f"Totale Impegno {sq_v}", f"{df_v_display['Tot_Vincolo'].sum():g}")
