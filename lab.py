import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# CSS GOLDEN (Neretto 900, Gradienti e Box Originali)
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; color: #000 !important; }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; color: black; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; margin-bottom: 10px; }
    .punto-incontro-box { background-color: #fff3e0; padding: 10px 30px; border-radius: 15px; border: 3px solid #ff9800; text-align: center; margin: 10px auto; width: fit-content; }
    .cut-box { background-color: #fdfdfd; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; }
    .cut-player-name { font-size: 3em; color: #d32f2f; text-transform: uppercase; line-height: 1; }
    .refund-box { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 2px solid #333; text-align: center; min-height: 110px; }
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
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].str.upper().str.strip().replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    v_cols = [c for c in f_vn.columns if '202' in c]
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# Database Mercato per i rimborsi extra
df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame()
rimborsi_tot = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

with t[0]: # CLASSIFICHE CON GRADIENTI
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 PUNTI")
            st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali']].style.background_gradient(cmap='YlGn'), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ SCONTRI DIRETTI")
            st.dataframe(f_sc[['Posizione','Giocatore','Punti']].style.background_gradient(cmap='Blues'), hide_index=True, use_container_width=True)

with t[1]: # BUDGET AGGIORNATO
    if f_rs is not None:
        st.subheader("💰 PATRIMONIO E RECUPERI")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N','Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO'] = bu['Squadra_N'].map(rimborsi_tot).fillna(0)
        bu['TOTALE'] = bu[['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI', 'RECUPERO']].sum(axis=1)
        st.dataframe(bu.sort_values('TOTALE', ascending=False).style.background_gradient(cmap='YlOrRd', subset=['TOTALE']).format("{:g}", subset=bu.columns[1:]), hide_index=True, use_container_width=True)

with t[2]: # ROSE CON MENU TUTTE E RICERCA
    if f_rs is not None:
        c1, c2 = st.columns([1, 2])
        with c1: sq_sel = st.selectbox("**SQUADRA**", ["TUTTE"] + sorted(f_rs['Squadra_N'].unique()))
        with c2: cerca = st.text_input("🔍 **CERCA CALCIATORE (CASE-INSENSITIVE)**", "").upper()
        df_d = f_rs.copy()
        if sq_sel != "TUTTE": df_d = df_d[df_d['Squadra_N'] == sq_sel]
        if cerca: df_d = df_d[df_d['Nome'].str.upper().str.contains(cerca, na=False)]
        st.dataframe(df_d[['Squadra_N', 'Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']].style.format({"Prezzo_N":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI (MENU E DETTAGLIO)
    if f_vn is not None:
        st.subheader("📅 DETTAGLIO VINCOLI")
        st.dataframe(f_vn[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False).style.format({"Tot_Vincolo":"{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI (CON DETTAGLIO VALORI PRECEDENTI)
    st.subheader("🔄 SIMULATORE SCAMBI")
    c1, c2 = st.columns(2)
    with c1:
        sa = st.selectbox("SQUADRA A", sorted(f_rs['Squadra_N'].unique()), key="sa")
        ga = st.multiselect("ESCONO DA A", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist())
    with c2:
        sb = st.selectbox("SQUADRA B", [s for s in sorted(f_rs['Squadra_N'].unique()) if s != sa], key="sb")
        gb = st.multiselect("ESCONO DA B", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist())
    
    if ga and gb:
        def get_v(n):
            p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
            v_m = f_vn[f_vn['Giocatore_Match']==super_clean_match(n)] if f_vn is not None else pd.DataFrame()
            v = v_m['Tot_Vincolo'].iloc[0] if not v_m.empty else 0
            return p + v, v
        
        val_a = sum(get_v(n)[0] for n in ga); val_b = sum(get_v(n)[0] for n in gb)
        diff = val_a - val_b
        st.markdown(f'<div class="punto-incontro-box">GAP SCAMBIO: {diff:g}<br><small>Media: {round((val_a+val_b)/2):g}</small></div>', unsafe_allow_html=True)
        
        # LOGICA PATRIMONIO PRECEDENTE (DA APP.PY)
        p_a_ante = f_rs[f_rs['Squadra_N']==sa]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sa]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sa,0)
        p_b_ante = f_rs[f_rs['Squadra_N']==sb]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sb]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sb,0)
        
        cp1, cp2 = st.columns(2)
        cp1.markdown(f'<div class="patrimonio-box">NUOVO PATRIMONIO {sa}<br><h2>{int(p_a_ante - diff)}</h2><small>PRIMA: {int(p_a_ante)}</small></div>', unsafe_allow_html=True)
        cp2.markdown(f'<div class="patrimonio-box">NUOVO PATRIMONIO {sb}<br><h2>{int(p_b_ante + diff)}</h2><small>PRIMA: {int(p_b_ante)}</small></div>', unsafe_allow_html=True)

with t[5]: # TAGLI (NOME GIGANTE)
    st.subheader("✂️ TAGLI GOLDEN")
    sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="sqt")
    gioc_t = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N']==sq_t]['Nome'].tolist())
    if gioc_t:
        p_a = f_rs[f_rs['Nome']==gioc_t]['Prezzo_N'].iloc[0]
        v_m = f_vn[f_vn['Giocatore_Match']==super_clean_match(gioc_t)] if f_vn is not None else pd.DataFrame()
        v_v = v_m['Tot_Vincolo'].iloc[0] if not v_m.empty else 0
        st.markdown(f'<div class="cut-box"><div class="cut-player-name">{gioc_t}</div><div style="font-size:1.8em;color:#2e7d32">RIMBORSO: {round((p_a+v_v)*0.6):g}</div><br>ASTA: {p_a:g} | VINC: {v_v:g}</div>', unsafe_allow_html=True)
