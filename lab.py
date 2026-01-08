import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.7", layout="wide", initial_sidebar_state="expanded")

# --- CSS DEFINITIVO ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame td, .stDataFrame th, p, div, span, label { 
        font-weight: 900 !important; color: #000 !important; 
    }
    .stat-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 3px solid #333; text-align: center; box-shadow: 3px 3px 0px #333; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO ---
def bold_df(df): return df.style.set_properties(**{'font-weight': '900', 'color': 'black'})

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() in ['x', '']: return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def super_clean(name):
    if not isinstance(name, str): return ""
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

def normalize_ruolo_v3(row):
    # Logica Giovani: basata sul prezzo d'asta 0
    if to_num(row['Prezzo']) == 0: return 'GIO'
    r = str(row['Ruolo']).upper().strip()
    if r in ['P', 'POR']: return 'POR'
    if r in ['D', 'DIF']: return 'DIF'
    if r in ['C', 'CEN']: return 'CEN'
    if r in ['A', 'ATT']: return 'ATT'
    return r

# --- CARICAMENTO DATI ---
def load_data():
    if not os.path.exists("rose_complete.csv"): return None
    
    # Caricamento Rose
    rs = pd.read_csv("rose_complete.csv", encoding='latin1', engine='python')
    rs.columns = [c.strip() for c in rs.columns]
    rs['Squadra_N'] = rs['Fantasquadra'].str.upper().str.strip()
    rs['Match_Nome'] = rs['Nome'].apply(super_clean)
    rs['Prezzo_N'] = rs['Prezzo'].apply(to_num)
    rs['Ruolo_N'] = rs.apply(normalize_ruolo_v3, axis=1)
    
    # Caricamento Quotazioni
    if os.path.exists("quotazioni.csv"):
        qt = pd.read_csv("quotazioni.csv", encoding='latin1', engine='python')
        qt.columns = [c.strip() for c in qt.columns]
        qt['Match_Nome'] = qt['Nome'].apply(super_clean)
        
        # Cerchiamo la colonna della quotazione (gestendo Qt.A o Qt. A)
        col_qt = next((c for c in qt.columns if 'Qt' in c), None)
        
        if col_qt:
            # Creiamo una colonna Ruolo Normalizzata anche nel listone quotazioni
            qt['Ruolo_QT_Norm'] = qt['Ruolo'].apply(lambda x: normalize_ruolo_v3({'Ruolo': x, 'Prezzo': 10})) # Prezzo fittizio per non renderli GIO
            
            # Merge basato su NOME e RUOLO per risolvere Ferguson
            rs = pd.merge(rs, qt[['Match_Nome', 'Ruolo_QT_Norm', col_qt]], 
                          left_on=['Match_Nome', 'Ruolo_N'], 
                          right_on=['Match_Nome', 'Ruolo_QT_Norm'], 
                          how='left')
            
            rs['Quotazione'] = rs[col_qt].apply(to_num)
        else:
            rs['Quotazione'] = 0
    else:
        rs['Quotazione'] = 0
        
    return rs

f_rs = load_data()

# --- INTERFACCIA ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "🚀 **MERCATO**"])

with t[2]: # TAB ROSE
    if f_rs is not None:
        sq_r = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()))
        df_team = f_rs[f_rs['Squadra_N'] == sq_r].copy()
        
        # Metric Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card">👥 TOTALI<br><b style="font-size:1.5em;">{len(df_team)}</b></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card">💰 ASTA<br><b style="font-size:1.5em;">{int(df_team["Prezzo_N"].sum())}</b></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card">📈 QUOT.<br><b style="font-size:1.5em;">{int(df_team["Quotazione"].sum())}</b></div>', unsafe_allow_html=True)
        with c4: 
            n_gio = len(df_team[df_team['Ruolo_N'] == 'GIO'])
            st.markdown(f'<div class="stat-card" style="border-color:#9c27b0;">👶 GIOVANI<br><b style="font-size:1.5em; color:#9c27b0;">{n_gio}</b></div>', unsafe_allow_html=True)

        # TABELLA RIASSUNTIVA (Focus Conteggio Giovani)
        st.write("---"); st.markdown("#### 📊 RIPARTIZIONE")
        riass_list = []
        for r in ['POR', 'DIF', 'CEN', 'ATT', 'GIO']:
            d_rep = df_team[df_team['Ruolo_N'] == r]
            if r == 'GIO':
                riass_list.append({"RUOLO": "GIOVANI", "N°": len(d_rep), "SPESA ASTA": "-", "VAL. ATTUALE": "-"})
            else:
                riass_list.append({"RUOLO": r, "N°": len(d_rep), "SPESA ASTA": str(int(d_rep['Prezzo_N'].sum())), "VAL. ATTUALE": str(int(d_rep['Quotazione'].sum()))})
        
        df_riass = pd.DataFrame(riass_list)

        def style_riass(row):
            v = str(row['RUOLO']).upper()
            pal = {
                'POR': ['#F06292']*4, 'DIF': ['#81C784']*4, 
                'CEN': ['#64B5F6']*4, 'ATT': ['#FFF176']*4, 'GIOVANI': ['#AB47BC']*4
            }
            return [f'background-color: {c}; color: white' for c in pal.get(v, ['']*4)]

        st.dataframe(bold_df(df_riass).apply(style_riass, axis=1), hide_index=True, use_container_width=True)

        # DETTAGLIO ROSA (Sfumature Tono su Tono)
        st.write("---"); st.markdown(f"#### 🏃 DETTAGLIO: {sq_r}")
        df_disp = df_team[['Ruolo_N', 'Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']].copy()
        
        def style_dettaglio(row):
            v = str(row['Ruolo_N']).upper()
            pal = {
                'POR': ['#FCE4EC', '#FCE4EC', '#F8BBD0', '#F48FB1', '#F06292'],
                'DIF': ['#E8F5E9', '#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784'],
                'CEN': ['#E3F2FD', '#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6'],
                'ATT': ['#FFFDE7', '#FFFDE7', '#FFF9C4', '#FFF59D', '#FFF176'],
                'GIO': ['#F3E5F5', '#F3E5F5', '#E1BEE7', '#CE93D8', '#AB47BC']
            }
            return [f'background-color: {c}' for c in pal.get(v, ['']*5)]

        st.dataframe(bold_df(df_disp).apply(style_dettaglio, axis=1).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), 
                     column_order=("Ruolo", "Nome", "Prezzo_N", "Quotazione"), 
                     hide_index=True, use_container_width=True)
