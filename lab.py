import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# --- BLOCCO CSS DEFINITIVO ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame td, .stDataFrame th, p, div, span, label { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .stat-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #333;
        text-align: center;
        box-shadow: 3px 3px 0px #333;
    }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; }
    .refund-box-pastello { padding: 15px; border-radius: 12px; border: 3px solid #333; text-align: center; min-height: 135px; box-shadow: 4px 4px 0px #333; margin-bottom: 15px; }
    .bg-azzurro { background-color: #E3F2FD !important; }
    .bg-verde { background-color: #E8F5E9 !important; }
    .bg-rosa { background-color: #FCE4EC !important; }
    .bg-giallo { background-color: #FFFDE7 !important; }
    .bg-arancio { background-color: #FFF3E0 !important; }
    .bg-viola { background-color: #F3E5F5 !important; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def bold_df(df):
    return df.style.set_properties(**{'font-weight': '900', 'color': 'black'})

def super_clean_match(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x' or str(val).strip() == '': return 0.0
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
    if f_qt is not None: f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].str.upper().str.strip().replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    v_cols = [c for c in f_vn.columns if '202' in c]
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 **RICERCA RAPIDA**")
    if f_rs is not None:
        cerca_side = st.multiselect("**GIOCATORE**", sorted(f_rs['Nome'].unique()))
        for n in cerca_side:
            d_g = f_rs[f_rs['Nome'] == n].iloc[0]
            st.markdown(f'''<div class="player-card" style="background-color:#fff;"><b>{n}</b> ({d_g['Squadra_N']})<br>ASTA: {int(d_g['Prezzo_N'])} | QUOT: {int(d_g['Quotazione'])}</div>''', unsafe_allow_html=True)

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

with t[2]: # TAB 2: ROSE POTENZIATA
    if f_rs is not None:
        st.subheader("🏃 DASHBOARD ROSE E STATISTICHE")
        
        sq_r = st.selectbox("**SELEZIONA SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="sq_rose_new")
        
        # Filtro dati per squadra
        df_team = f_rs[f_rs['Squadra_N'] == sq_r].copy()
        
        # --- CALCOLO STATISTICHE RIASSUNTIVE ---
        tot_giocatori = len(df_team)
        tot_prezzo = df_team['Prezzo_N'].sum()
        tot_quotazione = df_team['Quotazione'].sum()
        
        # Conteggio per ruolo
        conteggio_ruoli = df_team['Ruolo'].value_counts().to_dict()
        
        # Layout statistiche
        s1, s2, s3, s4 = st.columns(4)
        with s1: st.markdown(f'<div class="stat-card">👥 GIOCATORI<br><b style="font-size:1.5em;">{tot_giocatori}</b></div>', unsafe_allow_html=True)
        with s2: st.markdown(f'<div class="stat-card" style="border-color:#1a73e8;">💰 TOT. ASTA<br><b style="font-size:1.5em; color:#1a73e8;">{int(tot_prezzo)}</b></div>', unsafe_allow_html=True)
        with s3: st.markdown(f'<div class="stat-card" style="border-color:#2e7d32;">📈 TOT. QUOT.<br><b style="font-size:1.5em; color:#2e7d32;">{int(tot_quotazione)}</b></div>', unsafe_allow_html=True)
        with s4: 
            diff = tot_quotazione - tot_prezzo
            col_diff = "#2e7d32" if diff >= 0 else "#d32f2f"
            st.markdown(f'<div class="stat-card" style="border-color:{col_diff};">⚖️ PLUS/MINUS<br><b style="font-size:1.5em; color:{col_diff};">{"+" if diff>0 else ""}{int(diff)}</b></div>', unsafe_allow_html=True)

        st.write("---")
        
        # --- TABELLA RIASSUNTIVA RUOLI ---
        st.markdown("#### 📊 RIPARTIZIONE PER RUOLO")
        # Creiamo un dataframe per il riassunto
        ruoli_order = ['POR', 'DIF', 'CEN', 'ATT']
        riassunto_data = []
        for r in ruoli_order:
            df_r = df_team[df_team['Ruolo'] == r]
            riassunto_data.append({
                "RUOLO": r,
                "N°": len(df_r),
                "SPESA ASTA": int(df_r['Prezzo_N'].sum()),
                "VAL. ATTUALE": int(df_r['Quotazione'].sum())
            })
        df_riassunto = pd.DataFrame(riassunto_data)
        st.dataframe(bold_df(df_riassunto), hide_index=True, use_container_width=True)

        st.write("---")
        
        # --- ELENCO GIOCATORI COLORATO ---
        st.markdown(f"#### 🏃 DETTAGLIO ROSA: {sq_r}")
        def color_ruolo(val):
            v = str(val).upper()
            if 'POR' in v: return 'background-color: #FCE4EC'
            if 'DIF' in v: return 'background-color: #E8F5E9'
            if 'CEN' in v: return 'background-color: #E3F2FD'
            if 'ATT' in v: return 'background-color: #FFFDE7'
            return ''
        
        st.dataframe(bold_df(df_team[['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']]).applymap(color_ruolo, subset=['Ruolo']).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

# ... (seguono le altre TAB 0, 1, 3, 4, 5, 6 invariate)
