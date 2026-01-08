import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.9.1", layout="wide", initial_sidebar_state="expanded")

# --- BLOCCO CSS DEFINITIVO (Headers, Neretto 900 e Colori) ---
st.markdown("""
<style>
    /* 1. FORZA NERETTO 900 OVUNQUE */
    html, body, [data-testid="stAppViewContainer"] *, p, div, span, label { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    
    /* 2. FIX HEADERS (Sia per st.table che per st.dataframe) */
    th, .stDataFrame thead tr th, [data-testid="stTable"] thead tr th {
        font-weight: 900 !important;
        text-transform: uppercase !important;
        text-align: center !important;
        color: #000 !important;
        background-color: #f0f2f6 !important;
        border: 1px solid #333 !important;
    }

    /* 3. CARD E BOX STATISTICHE */
    .stat-card { 
        background-color: #f8f9fa; 
        padding: 15px; 
        border-radius: 10px; 
        border: 3px solid #333; 
        text-align: center; 
        box-shadow: 4px 4px 0px #333; 
    }
    
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def bold_df(df):
    """Applica il neretto 900 alle celle e centra i dati"""
    return df.style.set_properties(**{
        'font-weight': '900',
        'color': 'black',
        'text-align': 'center',
        'border': '1px solid #eee'
    })

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() in ['x', '', '-']: return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def super_clean(name):
    if not isinstance(name, str): return ""
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

def normalize_ruolo_v3(r):
    r = str(r).upper().strip()
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
    
    # FIX GIOVANI: Rileva chi ha prezzo 0
    def identify_role(row):
        if to_num(row['Prezzo']) == 0: return 'GIO'
        return normalize_ruolo_v3(row['Ruolo'])
    rs['Ruolo_N'] = rs.apply(identify_role, axis=1)
    
    # Fix Quotazioni e Omonimie (Ferguson)
    if os.path.exists("quotazioni.csv"):
        qt = pd.read_csv("quotazioni.csv", encoding='latin1', engine='python')
        qt.columns = [c.strip() for c in qt.columns]
        col_nome_qt = next((c for c in qt.columns if c.upper() in ['NOME', 'CALCIATORE']), 'Nome')
        col_ruolo_qt = next((c for c in qt.columns if c.upper() in ['RUOLO', 'R', 'POS']), 'Ruolo')
        col_valore_qt = next((c for c in qt.columns if 'QT' in c.upper() or 'VAL' in c.upper()), None)
        
        if col_valore_qt:
            qt['Match_Nome'] = qt[col_nome_qt].apply(super_clean)
            qt['Ruolo_N_QT'] = qt[col_ruolo_qt].apply(normalize_ruolo_v3)
            # Merge incrociato su NOME e RUOLO
            rs['Ruolo_Merge'] = rs['Ruolo'].apply(normalize_ruolo_v3)
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

        # 2. TABELLA RIASSUNTIVA (Headers Bold, Uppercase, Centrati tramite st.table)
        st.write("---"); st.markdown("#### 📊 RIPARTIZIONE PER RUOLO")
        riass_list = []
        for r in ['POR', 'DIF', 'CEN', 'ATT', 'GIO']:
            d_rep = df_team[df_team['Ruolo_N'] == r]
            label = "GIOVANI" if r == 'GIO' else r
            v_asta = int(d_rep['Prezzo_N'].sum()) if r != 'GIO' else 0
            v_att = int(d_rep['Quotazione'].sum()) if r != 'GIO' else 0
            riass_list.append({"RUOLO": label, "N°": len(d_rep), "SPESA ASTA": v_asta, "VALORE ATTUALE": v_att})
        
        df_riass = pd.DataFrame(riass_list)
        df_riass.columns = [c.upper() for c in df_riass.columns]

        def style_riass(row):
            v = str(row['RUOLO']).upper()
            pal = {
                'POR': ['#F06292', 'white'], 'DIF': ['#81C784', 'white'], 
                'CEN': ['#64B5F6', 'white'], 'ATT': ['#FFF176', 'black'], 'GIOVANI': ['#AB47BC', 'white']
            }
            bg, txt = pal.get(v, ['white', 'black'])
            return [f'background-color: {bg}; color: {txt}; text-align: center;' for _ in range(4)]

        # Nota: st.table forza il rendering HTML che rispetta il CSS per gli headers
        st.table(bold_df(df_riass).apply(style_riass, axis=1))

        # 3. DETTAGLIO ROSA (Interactive con Headers Uppercase)
        st.write("---"); st.markdown(f"#### 🏃 DETTAGLIO COMPLETO: {sq_r}")
        df_disp = df_team[['Ruolo_N', 'Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']].copy()
        df_disp.columns = [c.upper() for c in df_disp.columns]
        
        def style_dettaglio(row):
            v = str(row['RUOLO_N']).upper()
            pal = {
                'POR': ['#FCE4EC']*2 + ['#F8BBD0', '#F48FB1', '#F06292'],
                'DIF': ['#E8F5E9']*2 + ['#C8E6C9', '#A5D6A7', '#81C784'],
                'CEN': ['#E3F2FD']*2 + ['#BBDEFB', '#90CAF9', '#64B5F6'],
                'ATT': ['#FFFDE7']*2 + ['#FFF9C4', '#FFF59D', '#FFF176'],
                'GIO': ['#F3E5F5']*2 + ['#E1BEE7', '#CE93D8', '#AB47BC']
            }
            return [f'background-color: {c}; text-align: left;' for c in pal.get(v, ['']*5)]

        st.dataframe(bold_df(df_disp).apply(style_dettaglio, axis=1).format({"PREZZO_N":"{:g}", "QUOTAZIONE":"{:g}"}), 
                     column_order=("RUOLO", "NOME", "PREZZO_N", "QUOTAZIONE"), 
                     hide_index=True, use_container_width=True)
