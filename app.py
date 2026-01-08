import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# CSS STYLE
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .status-box { padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 2px solid; }
    .status-error { background-color: #ffebee; border-color: #c62828; color: #c62828; }
    .status-ok { background-color: #e8f5e9; border-color: #2e7d32; color: #2e7d32; }
    .search-card { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; color: #1a1a1a !important; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONE DI PULIZIA "INTELLIGENTE" ---
def super_clean(name):
    if not isinstance(name, str): return ""
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    name = name.upper().strip()
    # Mappa correzioni manuali
    mapping = {
        'LAUTARO': 'MARTINEZ L', 'MARTINEZ L': 'MARTINEZ L',
        'THURAM M': 'THURAM', 'NICO PAZ': 'PAZ N',
        'PIO ESPOSITO': 'ESPOSITO FP', 'ZAMBO ANGUISSA': 'ANGUISSA'
    }
    # Rimuove punteggiatura per il match
    clean = re.sub(r'[^A-Z0-9]', '', name)
    for k, v in mapping.items():
        if k.replace(' ','') in clean: return re.sub(r'[^A-Z0-9]', '', v)
    return clean

# --- CARICAMENTO ---
def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', encoding='latin1')
        df.columns = [c.strip() for c in df.columns]
        if is_quot: df['Key'] = df['Nome'].apply(super_clean)
        return df
    except: return None

f_rs, f_vn, f_pt, f_sc = ld("rose_complete.csv"), ld("vincoli.csv"), ld("classificapunti.csv"), ld("scontridiretti.csv")
f_qt = ld("quotazioni.csv", is_quot=True)

if f_rs is not None and f_qt is not None:
    f_rs['Key'] = f_rs['Nome'].apply(super_clean)
    f_rs = pd.merge(f_rs, f_qt[['Key', 'Qt.A']], on='Key', how='left').fillna({'Qt.A': 0})
    f_rs = f_rs.rename(columns={'Qt.A': 'Quotazione'})

# --- MAIN APP ---
st.title("⚽ MUYFANTAMANAGER GOLDEN V8.1")
t = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "✂️ TAGLI", "🕵️ MERCATO", "🛠️ DATA CHECK"])

# (Le altre Tab 0-6 rimangono come prima...)

with t[7]: # NUOVA TAB DATA CHECK
    st.subheader("🛠️ STRUMENTI DI CONTROLLO DATI")
    
    if f_rs is not None:
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("### ⚠️ GIOCATORI CON VALORE 0")
            mancanti = f_rs[f_rs['Quotazione'] == 0][['Nome', 'Fantasquadra', 'Ruolo']]
            if not mancanti.empty:
                st.error(f"Trovati {len(mancanti)} nomi non riconosciuti nel listone.")
                st.dataframe(mancanti, use_container_width=True, hide_index=True)
            else:
                st.success("Tutti i nomi corrispondono al listone!")

        with c2:
            st.markdown("### 👯 DOPPIONI NELLE ROSE")
            doppioni = f_rs[f_rs.duplicated(subset=['Nome'], keep=False)].sort_values('Nome')
            if not doppioni.empty:
                st.warning(f"Attenzione: ci sono {len(doppioni)//2} nomi duplicati.")
                st.dataframe(doppioni[['Nome', 'Fantasquadra', 'Ruolo']], use_container_width=True, hide_index=True)
            else:
                st.success("Nessun doppione trovato!")

    st.info("💡 **CONSIGLIO**: Per i doppioni come TERRACCIANO, aggiungi l'iniziale nel file CSV (es. TERRACCIANO P. e TERRACCIANO F.) per distinguerli.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 RICERCA")
    if f_rs is not None:
        p_cerca = st.multiselect("GIOCATORE", sorted(f_rs['Nome'].unique()))
        for p in p_cerca:
            row = f_rs[f_rs['Nome'] == p].iloc[0]
            st.markdown(f'<div class="search-card"><b>{p}</b> ({row["Fantasquadra"]})<br>VAL: {int(row["Prezzo"])} | QUOT: {int(row["Quotazione"])}</div>', unsafe_allow_html=True)
