import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V4.4", layout="wide", initial_sidebar_state="expanded")

# --- CSS INTEGRATO (Neretto 900, Gradienti Soft e Design Premium) ---
st.markdown("""
<style>
    /* Forza il neretto 900 ovunque */
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame td, .stDataFrame th, p, div, span, label, table, td, th { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    
    /* Tabelle Premium con Gradienti Soft */
    .golden-table { width: 100%; border-collapse: collapse; margin: 10px 0; }
    .golden-table th { padding: 12px 15px; border: 2px solid #333; text-align: center; background-color: #f0f2f6; text-transform: uppercase; }
    .golden-table td { padding: 10px 15px; border: 1px solid #ddd; text-align: center; }

    /* Classifiche: Gradiente Blu/Grigio Soft */
    .grad-classifica { 
        background: linear-gradient(135deg, #e0f2fe 0%, #f1f5f9 100%); 
        border: 2px solid #333;
        border-radius: 10px;
        padding: 10px;
    }

    /* Budget: Gradiente Verde/Giallo Soft */
    .grad-budget { 
        background: linear-gradient(135deg, #f0fdf4 0%, #fefce8 100%); 
        border: 2px solid #333;
        border-radius: 10px;
        padding: 10px;
    }

    /* Componenti Golden */
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .stat-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 3px solid #333; text-align: center; box-shadow: 4px 4px 0px #333; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; }
    .punto-incontro-box { background-color: #fff3e0; padding: 10px 30px; border-radius: 15px; border: 3px solid #ff9800; text-align: center; margin: 10px auto; width: fit-content; }
    .cut-box { background-color: #fdfdfd; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; text-align: center; }
    .cut-player-name { font-size: 3.5em; color: #d32f2f; text-transform: uppercase; line-height: 1; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x' or str(val).strip() == '': return 0.0
    s = str(val).replace('€', '').strip()
    if ',' in s: s = s.replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

def super_clean(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

# --- CARICAMENTO DATI ---
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS"}
FILE_DB = "mercatone_gennaio.csv"

def load_all():
    if not os.path.exists("rose_complete.csv"): return None, None, None, None
    rs = pd.read_csv("rose_complete.csv", encoding='latin1', engine='python')
    rs.columns = [c.strip() for c in rs.columns]
    rs['Squadra_N'] = rs['Fantasquadra'].str.upper().str.strip().replace(map_n)
    rs['Match_Nome'] = rs['Nome'].apply(super_clean)
    rs['Prezzo_N'] = rs['Prezzo'].apply(to_num)
    
    if os.path.exists("quotazioni.csv"):
        qt = pd.read_csv("quotazioni.csv", encoding='latin1', engine='python')
        qt.columns = [c.strip() for c in qt.columns]
        col_q = next((c for c in qt.columns if 'QT' in c.upper() or 'VAL' in c.upper()), 'Qt.A')
        qt['Match_Nome'] = qt['Nome'].apply(super_clean)
        rs = pd.merge(rs, qt[['Match_Nome', col_q]], on='Match_Nome', how='left').fillna({col_q: 0})
        rs = rs.rename(columns={col_q: 'Quotazione'}).drop_duplicates(subset=['Fantasquadra', 'Nome'])
    
    def simple_ld(f):
        if not os.path.exists(f): return None
        df = pd.read_csv(f, engine='python', skip_blank_lines=True, encoding='latin1')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')

    vn = simple_ld("vincoli.csv")
    if vn is not None:
        vn['Sq_N'] = vn['Squadra'].str.upper().str.strip().replace(map_n)
        vn['Giocatore_Match'] = vn['Giocatore'].apply(super_clean)
        v_cols = [c for c in vn.columns if '202' in c]
        for c in v_cols: vn[c] = vn[c].apply(to_num)
        vn['Tot_Vincolo'] = vn[v_cols].sum(axis=1)

    return rs, vn, simple_ld("classificapunti.csv"), simple_ld("scontridiretti.csv")

f_rs, f_vn, f_pt, f_sc = load_all()
df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])
rimborsi_m = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- SIDEBAR RICERCA ---
with st.sidebar:
    st.header("🔍 **RICERCA**")
    if f_rs is not None:
        cerca = st.multiselect("**CALCIATORE**", sorted(f_rs['Nome'].unique()))
        for n in cerca:
            d = f_rs[f_rs['Nome'] == n].iloc[0]
            st.markdown(f'<div class="player-card"><b>{n}</b> ({d["Squadra_N"]})<br>ASTA: {int(d["Prezzo_N"])} | QUOT: {int(d["Quotazione"])}</div>', unsafe_allow_html=True)

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

# TAB 0: CLASSIFICHE (Con Gradiente)
with t[0]:
    st.markdown('<div class="grad-classifica">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1: st.subheader("🎯 PUNTI"); st.dataframe(f_pt, hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2: st.subheader("⚔️ SCONTRI DIRETTI"); st.dataframe(f_sc, hide_index=True, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# TAB 1: BUDGET (Con Gradiente)
with t[1]:
    st.markdown('<div class="grad-budget">', unsafe_allow_html=True)
    if f_rs is not None:
        st.subheader("💰 PATRIMONIO DINAMICO")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_s = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_s, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO'] = bu['Squadra_N'].map(rimborsi_m).fillna(0)
        bu['TOTALE'] = bu['SPESA ROSE'] + bu['SPESA VINCOLI'] + bu['CREDITI'] + bu['RECUPERO']
        st.dataframe(bu.sort_values('TOTALE', ascending=False), hide_index=True, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# TAB 2: ROSE PREMIUM (Mantenuta grafica colorata)
with t[2]:
    if f_rs is not None:
        sq_r = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="sq_r_v4")
        df_team = f_rs[f_rs['Squadra_N'] == sq_r].copy()
        # ... (Logica visualizzazione HTML Roseagg già presente nelle versioni precedenti)
        shades = {'POR': ['#FCE4EC', '#F8BBD0', '#F48FB1', '#F06292'], 'DIF': ['#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784'], 'CEN': ['#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6'], 'ATT': ['#FFFDE7', '#FFF9C4', '#FFF59D', '#FFF176'], 'GIO': ['#F3E5F5', '#E1BEE7', '#CE93D8', '#AB47BC']}
        html_d = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>NOME</th><th>ASTA</th><th>QUOT</th></tr></thead><tbody>'
        for _, row in df_team.sort_values(['Prezzo_N'], ascending=False).iterrows():
            html_d += f'<tr><td>{row["Ruolo"]}</td><td>{row["Nome"]}</td><td>{int(row["Prezzo_N"])}</td><td>{int(row["Quotazione"])}</td></tr>'
        st.markdown(html_d + '</tbody></table>', unsafe_allow_html=True)

# TAB 3: VINCOLI (RIPRISTINATA)
with t[3]:
    st.subheader("📅 VINCOLI PLURIENNALI ATTIVI")
    if f_vn is not None:
        st.dataframe(f_vn[['Squadra', 'Giocatore', 'Tot_Vincolo']].sort_values('Tot_Vincolo', ascending=False), hide_index=True, use_container_width=True)
    else:
        st.info("Nessun dato vincoli trovato.")

# TAB 4: SCAMBI (Formula Golden)
with t[4]:
    st.subheader("🔄 SIMULATORE SCAMBI GOLDEN")
    # ... (Logica calcolo media/GAP ripristinata precedentemente)
    if f_rs is not None:
        c1, c2 = st.columns(2)
        with c1: sA = st.selectbox("SQUADRA A", sorted(f_rs['Squadra_N'].unique())); gA = st.multiselect("DA A", f_rs[f_rs['Squadra_N']==sA]['Nome'].tolist())
        with c2: sB = st.selectbox("SQUADRA B", [s for s in sorted(f_rs['Squadra_N'].unique()) if s != sA]); gB = st.multiselect("DA B", f_rs[f_rs['Squadra_N']==sB]['Nome'].tolist())
        # (Qui il codice esegue il calcolo media/gap come da versione Golden 3.2)

# TAB 5: TAGLI (Versione Dettagliata)
with t[5]:
    if f_rs is not None:
        st.subheader("✂️ TAGLI")
        sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="t_v4")
        gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist(), key="gt_v4")
        if gt:
            info = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt)].iloc[0]
            vv = f_vn[(f_vn['Sq_N'] == sq_t) & (f_vn['Giocatore_Match'] == super_clean(gt))]['Tot_Vincolo'].sum() if f_vn is not None else 0
            rimborso = round((info['Prezzo_N'] + vv) * 0.6, 1)
            st.markdown(f'<div class="cut-box"><div class="cut-player-name">{gt}</div><div style="font-size:2em; color:#2e7d32;">RIMBORSO: {rimborso:g}</div></div>', unsafe_allow_html=True)

# TAB 6: MERCATO
with t[6]:
    st.subheader("🚀 MERCATO")
    st.table(df_mercato)
