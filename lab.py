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
    .bg-viola { background-color: #F3E5F5 !important; } /* Colore per i Giovani */
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def bold_df(df): return df.style.set_properties(**{'font-weight': '900', 'color': 'black'})

def normalize_ruolo(row):
    r = str(row['Ruolo']).upper().strip()
    # Se il prezzo è 0, lo consideriamo "GIOVANE" per la statistica
    if to_num(row['Prezzo']) == 0: return 'GIO'
    if r in ['P', 'POR', 'PORTIERE']: return 'POR'
    if r in ['D', 'DIF', 'DIFENSORE']: return 'DIF'
    if r in ['C', 'CEN', 'CENTROCAMPISTA']: return 'CEN'
    if r in ['A', 'ATT', 'ATTACCANTE']: return 'ATT'
    return r

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x' or str(val).strip() == '': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

# --- CARICAMENTO DATI ---
# (Assumiamo che f_rs sia già caricato come visto nei passaggi precedenti)
if f_rs is not None:
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    f_rs['Ruolo_N'] = f_rs.apply(normalize_ruolo, axis=1) # Normalizzazione avanzata

# --- TAB ROSE ---
with t[2]: 
    if f_rs is not None:
        sq_r = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()))
        df_team = f_rs[f_rs['Squadra_N'] == sq_r].copy()
        
        # --- METRIC CARDS ---
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card">👥 TOTALI<br><b style="font-size:1.5em;">{len(df_team)}</b></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="border-color:#1a73e8;">💰 ASTA<br><b style="font-size:1.5em; color:#1a73e8;">{int(df_team["Prezzo_N"].sum())}</b></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card" style="border-color:#2e7d32;">📈 QUOT.<br><b style="font-size:1.5em; color:#2e7d32;">{int(df_team["Quotazione"].sum())}</b></div>', unsafe_allow_html=True)
        with c4: 
            n_giovani = len(df_team[df_team['Ruolo_N'] == 'GIO'])
            st.markdown(f'<div class="stat-card" style="border-color:#9c27b0;">👶 GIOVANI<br><b style="font-size:1.5em; color:#9c27b0;">{n_giovani}</b></div>', unsafe_allow_html=True)

        # --- TABELLA RIASSUNTIVA (COLORI INVERTITI) ---
        st.write("---"); st.markdown("#### 📊 RIPARTIZIONE PER RUOLO")
        riass_list = []
        for r in ['POR', 'DIF', 'CEN', 'ATT', 'GIO']:
            d_rep = df_team[df_team['Ruolo_N'] == r]
            if r == 'GIO' and len(d_rep) == 0: continue # Non mostra la riga se non ci sono giovani
            riass_list.append({
                "RUOLO": "GIOVANI" if r == 'GIO' else r,
                "N°": len(d_rep),
                "SPESA ASTA": int(d_rep['Prezzo_N'].sum()),
                "VAL. ATTUALE": int(d_rep['Quotazione'].sum())
            })
        df_riass = pd.DataFrame(riass_list)

        def color_inverted_plus(row):
            v = str(row['RUOLO']).upper()
            pal = {
                'POR': ['#F06292', '#F48FB1', '#F8BBD0', '#FCE4EC'],
                'DIF': ['#81C784', '#A5D6A7', '#C8E6C9', '#E8F5E9'],
                'CEN': ['#64B5F6', '#90CAF9', '#BBDEFB', '#E3F2FD'],
                'ATT': ['#FFF176', '#FFF59D', '#FFF9C4', '#FFFDE7'],
                'GIOVANI': ['#AB47BC', '#CE93D8', '#E1BEE7', '#F3E5F5']
            }
            return [f'background-color: {c}' for c in pal.get(v, ['']*4)]

        st.dataframe(bold_df(df_riass).apply(color_inverted_plus, axis=1), hide_index=True, use_container_width=True)

        # --- DETTAGLIO ROSA (COLORI TONO SU TONO) ---
        st.write("---"); st.markdown(f"#### 🏃 DETTAGLIO ROSA: {sq_r}")
        df_display = df_team[['Ruolo_N', 'Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']].copy()
        
        def color_shades_plus(row):
            v = str(row['Ruolo_N']).upper()
            pal = {
                'POR': ['#FCE4EC', '#FCE4EC', '#F8BBD0', '#F48FB1', '#F06292'],
                'DIF': ['#E8F5E9', '#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784'],
                'CEN': ['#E3F2FD', '#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6'],
                'ATT': ['#FFFDE7', '#FFFDE7', '#FFF9C4', '#FFF59D', '#FFF176'],
                'GIO': ['#F3E5F5', '#F3E5F5', '#E1BEE7', '#CE93D8', '#AB47BC']
            }
            return [f'background-color: {c}' for c in pal.get(v, ['']*5)]

        st.dataframe(bold_df(df_display).apply(color_shades_plus, axis=1).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), 
                     column_order=("Ruolo", "Nome", "Prezzo_N", "Quotazione"), 
                     hide_index=True, use_container_width=True)
