import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V4.8", layout="wide", initial_sidebar_state="expanded")

# --- BLOCCO CSS DEFINITIVO (Forza Neretto, Gradienti e Ripristina Menu) ---
st.markdown("""
<style>
    /* 1. FORZA NERETTO 900 OVUNQUE MA NON SUI WIDGET DI SISTEMA */
    html, body, [data-testid="stAppViewContainer"] p, div, span, label, table, td, th { 
        font-weight: 900 !important; 
        color: #000 !important;
    }
    
    /* 2. TABELLE HTML PREMIUM (ROSE) */
    .golden-table { width: 100%; border-collapse: collapse; border: 3px solid #333; margin: 10px 0; }
    .golden-table th { background-color: #f1f5f9; border: 2px solid #333; padding: 12px; text-transform: uppercase; }
    .golden-table td { border: 1px solid #333; padding: 10px; text-align: center; }

    /* 3. GRADIENTI PER COLONNE (Tramite classi specifiche) */
    .col-asta { background: linear-gradient(90deg, #ffffff 0%, #e0f2fe 100%); }
    .col-valore { background: linear-gradient(90deg, #ffffff 0%, #dcfce7 100%); }
    .col-punti { background: linear-gradient(90deg, #ffffff 0%, #fef9c3 100%); }

    /* 4. BOX SPECIALI */
    .stat-card { background: #fff; padding: 15px; border-radius: 10px; border: 3px solid #333; text-align: center; box-shadow: 4px 4px 0px #333; }
    .cut-box { background: #fff; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def format_no_zero(val):
    """Elimina i decimali se sono .0"""
    if isinstance(val, float) and val.is_integer():
        return int(val)
    return val

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() in ['x', '', '-']: return 0.0
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
    rs['Squadra_N'] = rs['Fantasquadra'].str.upper().str.strip().replace(map_n)
    rs['Match_Nome'] = rs['Nome'].apply(super_clean)
    rs['Prezzo_N'] = rs['Prezzo'].apply(to_num)
    
    if os.path.exists("quotazioni.csv"):
        qt = pd.read_csv("quotazioni.csv", encoding='latin1')
        col_q = next((c for c in qt.columns if 'QT' in c.upper() or 'VAL' in c.upper()), 'Qt.A')
        qt['Match_Nome'] = qt['Nome'].apply(super_clean)
        rs = pd.merge(rs, qt[['Match_Nome', col_q]], on='Match_Nome', how='left').fillna({col_q: 0})
        rs = rs.rename(columns={col_q: 'Quotazione'})
    
    def simple_ld(f): return pd.read_csv(f, engine='python', encoding='latin1').dropna(how='all') if os.path.exists(f) else None
    return rs, simple_ld("vincoli.csv"), simple_ld("classificapunti.csv"), simple_ld("scontridiretti.csv")

f_rs, f_vn, f_pt, f_sc = load_all()
df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

# TAB ROSE (STILE ROSEAGG CON PULIZIA ZERO E GRADIENTI)
with t[2]:
    if f_rs is not None:
        sq_r = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="sel_rose_v48")
        df_team = f_rs[f_rs['Squadra_N'] == sq_r].copy()
        
        # 1. Metric Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card">👥 TOTALI<br><h2>{len(df_team)}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card">💰 ASTA<br><h2>{format_no_zero(df_team["Prezzo_N"].sum())}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card">📈 VALORE<br><h2>{format_no_zero(df_team["Quotazione"].sum())}</h2></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="stat-card">👶 GIOVANI<br><h2>{len(df_team[df_team["Prezzo_N"] == 0])}</h2></div>', unsafe_allow_html=True)

        # 2. Tabella Dettagliata con Gradienti nelle celle
        st.write("---")
        shades = {'POR': ['#FCE4EC','#F8BBD0','#F48FB1','#F06292'], 'DIF': ['#E8F5E9','#C8E6C9','#A5D6A7','#81C784'], 'CEN': ['#E3F2FD','#BBDEFB','#90CAF9','#64B5F6'], 'ATT': ['#FFFDE7','#FFF9C4','#FFF59D','#FFF176']}
        html_d = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>NOME</th><th class="col-asta">ASTA</th><th class="col-valore">QUOT</th></tr></thead><tbody>'
        for _, row in df_team.sort_values(['Prezzo_N'], ascending=False).iterrows():
            rk = 'ATT' if 'ATT' in str(row['Ruolo']).upper() else 'CEN' if 'CEN' in str(row['Ruolo']).upper() else 'DIF' if 'DIF' in str(row['Ruolo']).upper() else 'POR'
            sh = shades.get(rk, ['#fff']*4)
            html_d += f'<tr><td style="background-color:{sh[0]}">{row["Ruolo"]}</td><td style="background-color:{sh[1]}">{row["Nome"]}</td><td class="col-asta">{format_no_zero(row["Prezzo_N"])}</td><td class="col-valore">{format_no_zero(row["Quotazione"])}</td></tr>'
        st.markdown(html_d + '</tbody></table>', unsafe_allow_html=True)

# TAB CLASSIFICHE (Gradienti sulle colonne Punti)
with t[0]:
    st.subheader("📊 CLASSIFICHE")
    if f_pt is not None:
        st.write("**🎯 PUNTI**")
        html_pt = '<table class="golden-table"><thead><tr><th>POS</th><th>GIOCATORE</th><th class="col-punti">PUNTI</th></tr></thead><tbody>'
        for _, r in f_pt.iterrows():
            html_pt += f'<tr><td>{r.iloc[0]}</td><td>{r.iloc[1]}</td><td class="col-punti">{format_no_zero(to_num(r.iloc[2]))}</td></tr>'
        st.markdown(html_pt + '</tbody></table>', unsafe_allow_html=True)

# TAB BUDGET (Gradienti sulla colonna Totale)
with t[1]:
    st.subheader("💰 PATRIMONIO")
    if f_rs is not None:
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'ASTA'})
        bu['TOTALE'] = bu['ASTA'] + bu['Squadra_N'].map(bg_ex).fillna(0)
        html_bu = '<table class="golden-table"><thead><tr><th>SQUADRA</th><th>ASTA</th><th class="col-valore">TOTALE</th></tr></thead><tbody>'
        for _, r in bu.sort_values('TOTALE', ascending=False).iterrows():
            html_bu += f'<tr><td>{r["Squadra_N"]}</td><td>{format_no_zero(r["ASTA"])}</td><td class="col-valore">{format_no_zero(r["TOTALE"])}</td></tr>'
        st.markdown(html_bu + '</tbody></table>', unsafe_allow_html=True)

# TAB MERCATO (Ripristinata)
with t[6]:
    st.subheader("🚀 MERCATO CESSIONI")
    if not df_mercato.empty:
        st.table(df_mercato)
    else:
        st.info("Nessuna cessione registrata.")
