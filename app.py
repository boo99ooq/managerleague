import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# CSS PER GRASSETTO SU INTERFACCIA (MENU, SIDEBAR, CARD)
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * {
        font-weight: 900 !important;
    }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid; }
    .card-blue { background-color: #e3f2fd; border-color: #1a73e8; }
    .card-red { background-color: #fbe9e7; border-color: #d32f2f; }
    .card-grey { background-color: #f1f3f4; border-color: #9e9e9e; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI PULIZIA ---
def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str.upper()

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True)
        if df.columns[0].startswith('Unnamed') or df.empty:
            df = pd.read_csv(f, skiprows=1, engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# --- CARICAMENTO ---
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- ELABORAZIONE ---
if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Nome'] = f_rs['Nome'].apply(clean_string)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_string)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- MAIN ---
st.title("⚽ **MUYFANTAMANAGER**")
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 **CLASSIFICA PUNTI**")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            f_pt['FM'] = f_pt['Media'].apply(to_num)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N','FM']].sort_values('Posizione').style\
                .background_gradient(subset=['P_N', 'FM'], cmap='YlGn')\
                .format({"P_N": "{:g}", "FM": "{:.2f}"})\
                .set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ **SCONTRI DIRETTI**")
            f_sc['P_S'] = f_sc['Punti'].apply(to_num)
            f_sc['GF'] = f_sc['Gol Fatti'].apply(to_num)
            f_sc['GS'] = f_sc['Gol Subiti'].apply(to_num)
            f_sc['DR'] = f_sc['GF'] - f_sc['GS'] # Calcolo Differenza Reti
            
            st.dataframe(f_sc[['Posizione','Giocatore','P_S','GF','GS','DR']].style\
                .background_gradient(subset=['P_S'], cmap='Blues')\
                .background_gradient(subset=['DR'], cmap='RdYlGn')\
                .format({"P_S": "{:g}", "GF": "{:g}", "GS": "{:g}", "DR": "{:+g}"})\
                .set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        st.subheader("💰 **BUDGET E PATRIMONIO**")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        
        bu['CREDITI DISPONIBILI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['PATRIMONIO TOTALE'] = bu['SPESA ROSE'] + bu['SPESA VINCOLI'] + bu['CREDITI DISPONIBILI']
        
        st.bar_chart(bu.set_index("Squadra_N")[['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISPONIBILI']], color=["#1a73e8", "#9c27b0", "#ff9800"])
        
        # Gradiente aggiunto anche su Crediti Disponibili
        st.dataframe(bu.sort_values("PATRIMONIO TOTALE", ascending=False).style\
            .background_gradient(cmap='YlOrRd', subset=['PATRIMONIO TOTALE'])\
            .background_gradient(cmap='Greens', subset=['CREDITI DISPONIBILI'])\
            .format({c: "{:g}" for c in bu.columns if c != 'Squadra_N'})\
            .set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

# [LE ALTRE TAB RIMANGONO INVARIATE COME NELL'ULTIMA VERSIONE CORRETTA]
