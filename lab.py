import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# SETUP UI E CSS (NERETTO 900)
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide")
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame, td, th { 
        font-weight: 900 !important; 
        color: #000 !important;
    }
</style>
""", unsafe_allow_html=True)

def super_clean_match(name):
    if not isinstance(name, str): return ""
    # Correzione accenti sporchi da CSV
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    # Normalizzazione (rimozione accenti e caratteri speciali)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    # Rimuove iniziali puntate (es. "MARTINEZ L." -> "MARTINEZ")
    name = re.sub(r'\s[A-Z]\.$', '', name)
    return name

# Caricamento file (omesso per brevità, usa la tua logica ld())
# ... (Caricamento f_rs, f_vn, f_qt) ...

with st.tabs(["🏃 **ROSE**", "🔄 **SCAMBI**", "🚀 **MERCATO**"])[0]:
    st.subheader("🏃 GESTIONE ROSE E RICERCA UNIVERSALE")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        lista_sq = ["TUTTE"] + sorted(f_rs['Squadra_N'].unique()) if f_rs is not None else ["TUTTE"]
        sq_sel = st.selectbox("**FILTRA SQUADRA**", lista_sq)
    
    with col2:
        cerca_testo = st.text_input("🔍 **DIGITA IL NOME (CERCA IN TUTTA LA LEGA)**", "").upper()

    if f_rs is not None:
        df_display = f_rs.copy()
        
        # LOGICA DI RICERCA POTENZIATA
        if sq_sel != "TUTTE":
            df_display = df_display[df_display['Squadra_N'] == sq_sel]
        
        if cerca_testo:
            # Cerca per contenimento (trova "MART" in "MARTINEZ")
            df_display = df_display[df_display['Nome'].str.upper().str.contains(cerca_testo, na=False)]
        
        st.dataframe(df_display[['Squadra_N', 'Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']].style.format({"Prezzo_N":"{:g}"}), use_container_width=True, hide_index=True)
