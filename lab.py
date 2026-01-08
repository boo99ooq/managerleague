import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.6", layout="wide", initial_sidebar_state="expanded")

# --- BLOCCO CSS DEFINITIVO ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame td, .stDataFrame th, p, div, span, label { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    .stat-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 3px solid #333; text-align: center; box-shadow: 3px 3px 0px #333; }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; }
    .refund-box-pastello { padding: 15px; border-radius: 12px; border: 3px solid #333; text-align: center; min-height: 135px; box-shadow: 4px 4px 0px #333; margin-bottom: 15px; }
    .bg-azzurro { background-color: #E3F2FD !important; } .bg-verde { background-color: #E8F5E9 !important; }
    .bg-rosa { background-color: #FCE4EC !important; } .bg-giallo { background-color: #FFFDE7 !important; }
    .bg-viola { background-color: #F3E5F5 !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def bold_df(df): return df.style.set_properties(**{'font-weight': '900', 'color': 'black'})

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x' or str(val).strip() == '': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def normalize_ruolo_giovani(row):
    # Logica Giovani: se il prezzo è 0 lo marchiamo come GIO per la statistica
    if to_num(row['Prezzo']) == 0: return 'GIO'
    r = str(row['Ruolo']).upper().strip()
    if r in ['P', 'POR', 'PORTIERE']: return 'POR'
    if r in ['D', 'DIF', 'DIFENSORE']: return 'DIF'
    if r in ['C', 'CEN', 'CENTROCAMPISTA']: return 'CEN'
    if r in ['A', 'ATT', 'ATTACCANTE']: return 'ATT'
    return r

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
    f_rs['Ruolo_N'] = f_rs.apply(normalize_ruolo_giovani, axis=1) # FIX: Crea colonna normalizzata
    if f_qt is not None: f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].str.upper().str.strip().replace(map_n)
    v_cols = [c for c in f_vn.columns if '202' in c]
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)

df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])

t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

with t[2]: # TAB 2: ROSE DASHBOARD GOLDEN
    if f_rs is not None:
        sq_r = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()))
        df_team = f_rs[f_rs['Squadra_N'] == sq_r].copy()
        
        # Metric Cards (Inclusi i Giovani)
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card">👥 TOTALI<br><b style="font-size:1.5em;">{len(df_team)}</b></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="border-color:#1a73e8;">💰 ASTA<br><b style="font-size:1.5em; color:#1a73e8;">{int(df_team["Prezzo_N"].sum())}</b></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card" style="border-color:#2e7d32;">📈 QUOT.<br><b style="font-size:1.5em; color:#2e7d32;">{int(df_team["Quotazione"].sum())}</b></div>', unsafe_allow_html=True)
        with c4: 
            n_gio = len(df_team[df_team['Ruolo_N'] == 'GIO'])
            st.markdown(f'<div class="stat-card" style="border-color:#9c27b0;">👶 GIOVANI<br><b style="font-size:1.5em; color:#9c27b0;">{n_gio}</b></div>', unsafe_allow_html=True)

        # TABELLA RIASSUNTIVA (COLORI SCURI -> CHIARO)
        st.write("---"); st.markdown("#### 📊 RIPARTIZIONE PER REPARTO")
        riass_list = []
        for r in ['POR', 'DIF', 'CEN', 'ATT', 'GIO']:
            d_rep = df_team[df_team['Ruolo_N'] == r]
            if r == 'GIO' and len(d_rep) == 0: continue
            riass_list.append({"RUOLO": "GIOVANI" if r == 'GIO' else r, "N°": len(d_rep), "SPESA ASTA": int(d_rep['Prezzo_N'].sum()), "VAL. ATTUALE": int(d_rep['Quotazione'].sum())})
        df_riass = pd.DataFrame(riass_list)

        def color_inverted_final(row):
            v = str(row['RUOLO']).upper()
            pal = {
                'POR': ['#F06292', '#F48FB1', '#F8BBD0', '#FCE4EC'],
                'DIF': ['#81C784', '#A5D6A7', '#C8E6C9', '#E8F5E9'],
                'CEN': ['#64B5F6', '#90CAF9', '#BBDEFB', '#E3F2FD'],
                'ATT': ['#FFF176', '#FFF59D', '#FFF9C4', '#FFFDE7'],
                'GIOVANI': ['#AB47BC', '#CE93D8', '#E1BEE7', '#F3E5F5']
            }
            return [f'background-color: {c}' for c in pal.get(v, ['']*4)]

        st.dataframe(bold_df(df_riass).apply(color_inverted_final, axis=1), hide_index=True, use_container_width=True)

        # DETTAGLIO ROSA (COLORI CHIARI -> SCURI)
        st.write("---"); st.markdown(f"#### 🏃 DETTAGLIO ROSA: {sq_r}")
        df_display = df_team[['Ruolo_N', 'Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']].copy()
        
        def color_shades_final(row):
            v = str(row['Ruolo_N']).upper()
            pal = {
                'POR': ['#FCE4EC', '#FCE4EC', '#F8BBD0', '#F48FB1', '#F06292'],
                'DIF': ['#E8F5E9', '#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784'],
                'CEN': ['#E3F2FD', '#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6'],
                'ATT': ['#FFFDE7', '#FFFDE7', '#FFF9C4', '#FFF59D', '#FFF176'],
                'GIO': ['#F3E5F5', '#F3E5F5', '#E1BEE7', '#CE93D8', '#AB47BC']
            }
            return [f'background-color: {c}' for c in pal.get(v, ['']*5)]

        st.dataframe(bold_df(df_display).apply(color_shades_final, axis=1).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), 
                     column_order=("Ruolo", "Nome", "Prezzo_N", "Quotazione"), 
                     hide_index=True, use_container_width=True)

# BUDGET E ALTRE TAB (ESTESE)
with t[1]: # BUDGET
    if f_rs is not None:
        rim_u = df_mercato[df_mercato['STATO'] == 'UFFICIALE'].groupby('SQUADRA')['TOTALE'].sum().to_dict()
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_s = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_s, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI DISPONIBILI'] = bu['Squadra_N'].map(bg_ex).fillna(0); bu['RECUPERO CESSIONI'] = bu['Squadra_N'].map(rim_u).fillna(0)
        voci = ['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISPONIBILI', 'RECUPERO CESSIONI']
        sel = st.multiselect("**VOCI PATRIMONIO:**", voci, default=voci)
        if sel:
            bu['TOTALE'] = bu[sel].sum(axis=1)
            n_cols = bu.select_dtypes(include=['number']).columns
            st.dataframe(bold_df(bu[['Squadra_N'] + sel + ['TOTALE']].sort_values('TOTALE', ascending=False)).background_gradient(cmap='YlOrRd', subset=['TOTALE']).format({c: "{:g}" for c in n_cols}), hide_index=True, use_container_width=True)

with t[6]: # MERCATO
    st.subheader("🚀 MERCATO")
    # ... (Il resto del codice mercato è identico all'ultima versione stabile)
