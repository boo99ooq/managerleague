import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.5", layout="wide", initial_sidebar_state="expanded")

# --- BLOCCO CSS DEFINITIVO ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame td, .stDataFrame th, p, div, span, label { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    .stat-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 3px solid #333; text-align: center; box-shadow: 3px 3px 0px #333; }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .refund-box-pastello { padding: 15px; border-radius: 12px; border: 3px solid #333; text-align: center; min-height: 135px; box-shadow: 4px 4px 0px #333; margin-bottom: 15px; }
    .bg-azzurro { background-color: #E3F2FD !important; } .bg-verde { background-color: #E8F5E9 !important; }
    .bg-rosa { background-color: #FCE4EC !important; } .bg-giallo { background-color: #FFFDE7 !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def bold_df(df): return df.style.set_properties(**{'font-weight': '900', 'color': 'black'})

def normalize_ruolo(r):
    r = str(r).upper().strip()
    if r in ['P', 'POR', 'PORTIERE']: return 'POR'
    if r in ['D', 'DIF', 'DIFENSORE']: return 'DIF'
    if r in ['C', 'CEN', 'CENTROCAMPISTA']: return 'CEN'
    if r in ['A', 'ATT', 'ATTACCANTE']: return 'ATT'
    return r

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x' or str(val).strip() == '': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def super_clean_match(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True, encoding='latin1')
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Match_Nome'] = df['Nome'].apply(super_clean_match)
            return df[['Match_Nome', 'Qt.A']].rename(columns={'Qt.A': 'Quotazione'})
        return df.dropna(how='all')
    except: return None

# --- CARICAMENTO DATI ---
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)
FILE_DB = "mercatone_gennaio.csv"
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].str.upper().str.strip().replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean_match)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    f_rs['Ruolo_N'] = f_rs['Ruolo'].apply(normalize_ruolo)
    if f_qt is not None: f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].str.upper().str.strip().replace(map_n)
    v_cols = [c for c in f_vn.columns if '202' in c]
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)

df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])

t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

with t[2]: # TAB ROSE
    if f_rs is not None:
        sq_r = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()))
        df_team = f_rs[f_rs['Squadra_N'] == sq_r].copy()
        
        c_m1, c_m2, c_m3 = st.columns(3)
        c_m1.markdown(f'<div class="stat-card">👥 GIOCATORI<br><b style="font-size:1.5em;">{len(df_team)}</b></div>', unsafe_allow_html=True)
        c_m2.markdown(f'<div class="stat-card" style="border-color:#1a73e8;">💰 TOT. ASTA<br><b style="font-size:1.5em; color:#1a73e8;">{int(df_team["Prezzo_N"].sum())}</b></div>', unsafe_allow_html=True)
        c_m3.markdown(f'<div class="stat-card" style="border-color:#2e7d32;">📈 TOT. QUOT.<br><b style="font-size:1.5em; color:#2e7d32;">{int(df_team["Quotazione"].sum())}</b></div>', unsafe_allow_html=True)

        # TABELLA RIASSUNTIVA (COLORI INVERTITI: SCURO -> CHIARO)
        st.write("---"); st.markdown("#### 📊 RIPARTIZIONE PER RUOLO")
        riass_list = []
        for r in ['POR', 'DIF', 'CEN', 'ATT']:
            d_rep = df_team[df_team['Ruolo_N'] == r]
            riass_list.append({"RUOLO": r, "N°": len(d_rep), "SPESA ASTA": int(d_rep['Prezzo_N'].sum()), "VAL. ATTUALE": int(d_rep['Quotazione'].sum())})
        df_riass = pd.DataFrame(riass_list)

        def color_inverted(row):
            v = str(row['RUOLO']).upper()
            pal = {
                'POR': ['#F06292', '#F48FB1', '#F8BBD0', '#FCE4EC'],
                'DIF': ['#81C784', '#A5D6A7', '#C8E6C9', '#E8F5E9'],
                'CEN': ['#64B5F6', '#90CAF9', '#BBDEFB', '#E3F2FD'],
                'ATT': ['#FFF176', '#FFF59D', '#FFF9C4', '#FFFDE7']
            }
            return [f'background-color: {c}' for c in pal.get(v, ['']*4)]

        st.dataframe(bold_df(df_riass).apply(color_inverted, axis=1), hide_index=True, use_container_width=True)

        # DETTAGLIO ROSA (COLORI CHIARI -> SCURI)
        st.write("---"); st.markdown(f"#### 🏃 DETTAGLIO ROSA: {sq_r}")
        
        # Filtriamo le colonne PRIMA dello stile per evitare il ValueError
        df_display = df_team[['Ruolo_N', 'Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']].copy()
        
        def color_shades(row):
            v = str(row['Ruolo_N']).upper()
            pal = {
                'POR': ['#FCE4EC', '#FCE4EC', '#F8BBD0', '#F48FB1', '#F06292'],
                'DIF': ['#E8F5E9', '#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784'],
                'CEN': ['#E3F2FD', '#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6'],
                'ATT': ['#FFFDE7', '#FFFDE7', '#FFF9C4', '#FFF59D', '#FFF176']
            }
            return [f'background-color: {c}' for c in pal.get(v, ['']*5)]

        st.dataframe(bold_df(df_display).apply(color_shades, axis=1).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), 
                     column_order=("Ruolo", "Nome", "Prezzo_N", "Quotazione"), 
                     hide_index=True, use_container_width=True)
