import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.9.7", layout="wide", initial_sidebar_state="expanded")

# --- BLOCCO CSS DEFINITIVO (Headers, Neretto 900 e Allineamento) ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, p, div, span, label { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    
    .golden-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    }
    .golden-table thead tr {
        background-color: #f0f2f6;
        color: #000;
    }
    .golden-table th {
        padding: 12px 15px;
        font-weight: 900 !important;
        text-transform: uppercase !important;
        border: 2px solid #333;
        text-align: center;
    }
    .golden-table td {
        padding: 10px 15px;
        border: 1px solid #ddd;
        text-align: center;
        font-weight: 900 !important;
    }
    .stat-card { 
        background-color: #f8f9fa; 
        padding: 15px; 
        border-radius: 10px; 
        border: 3px solid #333; 
        text-align: center; 
        box-shadow: 4px 4px 0px #333; 
    }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def to_num(val):
    if pd.isna(val): return 0.0
    s = str(val).replace('€', '').strip()
    if s == '' or s == '-' or s.lower() == 'x': return 0.0
    # FIX: Se c'è la virgola è formato italiano (1.000,50), altrimenti è standard (10.0)
    if ',' in s:
        s = s.replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

def super_clean(name):
    if not isinstance(name, str): return ""
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

def normalize_ruolo_v3(row):
    r = str(row['Ruolo']).upper().strip()
    p = to_num(row['Prezzo'])
    # FIX GIOVANI: Riconosce se il ruolo contiene "G" o "GIOVANI" OPPURE se il prezzo è 0
    if 'GIOVANI' in r or r == 'G' or p == 0:
        return 'GIO'
    if r in ['P', 'POR', 'PORTIERE']: return 'POR'
    if r in ['D', 'DIF', 'DIFENSORE']: return 'DIF'
    if r in ['C', 'CEN', 'CENTROCAMPISTA']: return 'CEN'
    if r in ['A', 'ATT', 'ATTACCANTE']: return 'ATT'
    return r

# --- CARICAMENTO DATI ---
def load_data():
    if not os.path.exists("rose_complete.csv"): return None
    rs = pd.read_csv("rose_complete.csv", encoding='latin1', engine='python')
    rs.columns = [c.strip() for c in rs.columns]
    rs['Squadra_N'] = rs['Fantasquadra'].str.upper().str.strip()
    rs['Match_Nome'] = rs['Nome'].apply(super_clean)
    rs['Prezzo_N'] = rs['Prezzo'].apply(to_num)
    rs['Ruolo_N'] = rs.apply(normalize_ruolo_v3, axis=1) # Applica la nuova logica giovani
    
    # Merge Quotazioni e Ferguson
    if os.path.exists("quotazioni.csv"):
        qt = pd.read_csv("quotazioni.csv", encoding='latin1', engine='python')
        qt.columns = [c.strip() for c in qt.columns]
        col_nome_qt = next((c for c in qt.columns if c.upper() in ['NOME', 'CALCIATORE']), 'Nome')
        col_ruolo_qt = next((c for c in qt.columns if c.upper() in ['RUOLO', 'R', 'POS']), 'Ruolo')
        col_valore_qt = next((c for c in qt.columns if 'QT' in c.upper() or 'VAL' in c.upper()), None)
        if col_valore_qt:
            qt['Match_Nome'] = qt[col_nome_qt].apply(super_clean)
            qt['Ruolo_N_QT'] = qt[col_ruolo_qt].apply(lambda x: normalize_ruolo_v3({'Ruolo': x, 'Prezzo': 10})) # Prezzo fittizio per merge
            rs['Ruolo_Merge'] = rs['Ruolo'].apply(lambda x: normalize_ruolo_v3({'Ruolo': x, 'Prezzo': 10}))
            rs = pd.merge(rs, qt[['Match_Nome', 'Ruolo_N_QT', col_valore_qt]], 
                          left_on=['Match_Nome', 'Ruolo_Merge'], 
                          right_on=['Match_Nome', 'Ruolo_N_QT'], 
                          how='left')
            rs['Quotazione'] = rs[col_valore_qt].apply(to_num)
            rs = rs.drop_duplicates(subset=['Fantasquadra', 'Nome', 'Ruolo'])
    return rs

f_rs = load_data()

# --- INTERFACCIA ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "🚀 **MERCATO**"])

with t[2]: # TAB ROSE
    if f_rs is not None:
        sq_r = st.selectbox("**SELEZIONA SQUADRA**", sorted(f_rs['Squadra_N'].unique()))
        df_team = f_rs[f_rs['Squadra_N'] == sq_r].copy()
        
        # 1. Metric Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card">👥 TOTALI<br><b style="font-size:1.5em;">{len(df_team)}</b></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="border-color:#1a73e8;">💰 ASTA<br><b style="font-size:1.5em; color:#1a73e8;">{int(df_team["Prezzo_N"].sum())}</b></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card" style="border-color:#2e7d32;">📈 QUOT.<br><b style="font-size:1.5em; color:#2e7d32;">{int(df_team["Quotazione"].sum())}</b></div>', unsafe_allow_html=True)
        with c4: 
            n_gio = len(df_team[df_team['Ruolo_N'] == 'GIO'])
            st.markdown(f'<div class="stat-card" style="border-color:#9c27b0;">👶 GIOVANI<br><b style="font-size:1.5em; color:#9c27b0;">{n_gio}</b></div>', unsafe_allow_html=True)

        # 2. TABELLA RIASSUNTIVA (HTML Custom)
        st.write("---"); st.markdown("#### 📊 RIPARTIZIONE PER RUOLO")
        riass_list = []
        for r in ['POR', 'DIF', 'CEN', 'ATT', 'GIO']:
            d_rep = df_team[df_team['Ruolo_N'] == r]
            label = "GIOVANI" if r == 'GIO' else r
            riass_list.append({"RUOLO": label, "N°": len(d_rep), "SPESA ASTA": int(d_rep['Prezzo_N'].sum()), "VALORE ATTUALE": int(d_rep['Quotazione'].sum())})
        
        pal_piena = {'POR': '#F06292', 'DIF': '#81C784', 'CEN': '#64B5F6', 'ATT': '#FFF176', 'GIOVANI': '#AB47BC'}
        html_riass = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>N°</th><th>SPESA ASTA</th><th>VALORE ATTUALE</th></tr></thead><tbody>'
        for row in riass_list:
            bg = pal_piena.get(row['RUOLO'], '#fff')
            txt = 'black' if row['RUOLO'] == 'ATT' else 'white'
            # Per i giovani mostriamo solo il numero
            s_asta = row['SPESA ASTA'] if row['RUOLO'] != 'GIOVANI' else "-"
            s_att = row['VALORE ATTUALE'] if row['RUOLO'] != 'GIOVANI' else "-"
            html_riass += f'<tr style="background-color:{bg}; color:{txt};"><td>{row["RUOLO"]}</td><td>{row["N°"]}</td><td>{s_asta}</td><td>{s_att}</td></tr>'
        html_riass += '</tbody></table>'
        st.markdown(html_riass, unsafe_allow_html=True)

        # 3. DETTAGLIO ROSA (HTML Custom)
        st.write("---"); st.markdown(f"#### 🏃 DETTAGLIO COMPLETO: {sq_r}")
        pal_shades = {
            'POR': ['#FCE4EC', '#F8BBD0', '#F48FB1', '#F06292'],
            'DIF': ['#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784'],
            'CEN': ['#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6'],
            'ATT': ['#FFFDE7', '#FFF9C4', '#FFF59D', '#FFF176'],
            'GIO': ['#F3E5F5', '#E1BEE7', '#CE93D8', '#AB47BC']
        }
        html_dett = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>NOME</th><th>PREZZO</th><th>QUOTAZIONE</th></tr></thead><tbody>'
        for _, row in df_team.sort_values(['Ruolo_N', 'Prezzo_N'], ascending=[True, False]).iterrows():
            v = str(row['Ruolo_N']).upper()
            sh = pal_shades.get(v, ['#fff']*4)
            html_dett += f'<tr><td style="background-color:{sh[0]}">{row["Ruolo"]}</td><td style="background-color:{sh[1]}">{row["Nome"]}</td><td style="background-color:{sh[2]}">{int(row["Prezzo_N"])}</td><td style="background-color:{sh[3]}">{int(row["Quotazione"])}</td></tr>'
        html_dett += '</tbody></table>'
        st.markdown(html_dett, unsafe_allow_html=True)
