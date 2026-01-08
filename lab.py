import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# CSS INTEGRALE
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .player-card { padding: 12px; border-radius: 10px; margin-bottom: 12px; border: 3px solid #333; box-shadow: 4px 4px 8px rgba(0,0,0,0.2); color: black; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; border: 3px solid #1a73e8; }
    .punto-incontro-box { background-color: #fff3e0; padding: 8px 25px; border-radius: 12px; border: 3px solid #ff9800; text-align: center; width: fit-content; }
    
    /* STYLE TAGLI */
    .cut-box { 
        background-color: #fdfdfd; padding: 25px; border-radius: 15px; border: 4px solid #333; 
        box-shadow: 6px 6px 0px #ff4b4b; color: #1a1a1a; margin-top: 10px;
    }
    .cut-player-name { font-size: 2.5em; color: #d32f2f; text-transform: uppercase; margin-bottom: 5px; line-height: 1; }
    .cut-refund-label { font-size: 0.9em; color: #555; text-transform: uppercase; }
    .cut-refund-value { font-size: 1.5em; color: #2e7d32; background: #e8f5e9; padding: 5px 15px; border-radius: 8px; display: inline-block; margin-top: 5px; }
    .stat-label { font-size: 0.85em; color: #666; font-weight: 400 !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def super_clean_match(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str.upper()

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
f_sc, f_pt = ld("scontridiretti.csv"), ld("classificapunti.csv")
f_rs, f_vn = ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)
FILE_DB = "mercatone_gennaio.csv"
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS"}

# --- ELABORAZIONE ---
if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean_match)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None: f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- DB MERCATO ---
if os.path.exists(FILE_DB):
    df_mercato = pd.read_csv(FILE_DB)
else:
    df_mercato = pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "SPESA", "QUOT", "RIMB_BASE", "VINCOLO", "TOTALE", "STATO"])
rimborsi_squadre_tot = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🆕 **MERCATO**"])

# --- TAB ROSE (FIXED STYLE) ---
with t[2]:
    if f_rs is not None:
        sq = st.selectbox("**SQUADRA**", sorted([s for s in f_rs['Squadra_N'].unique() if s]), key="rose_box")
        df_sq = f_rs[f_rs['Squadra_N'] == sq][['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']]
        st.dataframe(df_sq.style.format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

# --- TAB VINCOLI (FIXED STYLE) ---
with t[3]:
    if f_vn is not None:
        sq_v = st.selectbox("**FILTRA SQUADRA**", ["TUTTE"] + sorted([s for s in f_vn['Sq_N'].unique() if s]), key="vinc_box")
        df_v_disp = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        # FIX: aggiunto .style prima di .format
        st.dataframe(df_v_disp[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False).style.format({"Tot_Vincolo": "{:g}"}), hide_index=True, use_container_width=True)

# --- TAB TAGLI (NUOVO LAYOUT) ---
with t[5]:
    st.subheader("✂️ SIMULATORE TAGLI")
    if f_rs is not None:
        sq_t = st.selectbox("SQUADRA", sorted([s for s in f_rs['Squadra_N'].unique() if s]), key="sq_tag_page")
        gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist(), key="gioc_tag_page")
        
        if gt:
            p_t_v = f_rs[f_rs['Squadra_N']==sq_t]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sq_t]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sq_t, 0)
            v_asta = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt)]['Prezzo_N'].iloc[0]
            v_match = f_vn[f_vn['Giocatore_Match'] == super_clean_match(gt)] if f_vn is not None else pd.DataFrame()
            v_vinc = v_match['Tot_Vincolo'].iloc[0] if not v_match.empty else 0
            
            rimborso = round((v_asta + v_vinc) * 0.6)
            incidenza = ((v_asta + v_vinc) / p_t_v) * 100 if p_t_v > 0 else 0
            
            st.markdown(f'''
            <div class="cut-box">
                <div class="stat-label">SCHEDA TAGLIO CALCIATORE</div>
                <div class="cut-player-name">{gt}</div>
                <div class="cut-refund-label">RIMBORSO MATURATO (60%)</div>
                <div class="cut-refund-value">+{rimborso:g} CREDITI</div>
                <hr style="border: 0; border-top: 2px dashed #333; margin: 20px 0;">
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div style="flex: 1;">
                        <span class="stat-label">VALORE ASTA</span><br><b style="font-size: 1.2em;">{v_asta:g}</b>
                    </div>
                    <div style="flex: 1; border-left: 2px solid #eee; border-right: 2px solid #eee;">
                        <span class="stat-label">VALORE VINCOLI</span><br><b style="font-size: 1.2em;">{v_vinc:g}</b>
                    </div>
                    <div style="flex: 1;">
                        <span class="stat-label">INCIDENZA PATR.</span><br><b style="font-size: 1.2em;">{incidenza:.2f}%</b>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

# --- TAB MERCATO (NUOVA) ---
with t[6]:
    st.subheader("🚀 GESTIONE MERCATO GENNAIO")
    # Qui andrebbe il codice del database cessioni già sviluppato...
