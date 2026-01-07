import streamlit as st
import pandas as pd
import os
import altair as alt

# 1. SETUP E STILE
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

# Configurazione Budget
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

def cv(v):
    if pd.isna(v): return 0.0
    try:
        s = str(v).replace('"', '').replace(',', '.').strip()
        return float(s) if s != "" else 0.0
    except: return 0.0

def clean_name(s):
    if pd.isna(s) or str(s).strip().upper() == "NONE" or str(s).strip() == "": return "SKIP"
    return str(s).split(':')[0].replace('*', '').replace('"', '').strip().upper()

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, sep=',', engine='python', encoding='utf-8-sig', skip_blank_lines=True)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# 2. CARICAMENTO FILE
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv") # NUOVO FILE

# PULIZIA DATI
if f_rs is not None:
    f_rs['Nome'] = f_rs['Nome'].apply(clean_name)
    f_rs['Fantasquadra'] = f_rs['Fantasquadra'].apply(clean_name)
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)

if f_vn is not None:
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_name)
    f_vn['Spesa Complessiva'] = f_vn.get('Costo 2026-27', 0).apply(cv) + f_vn.get('Costo 2027-28', 0).apply(cv) + f_vn.get('Costo 2028-29', 0).apply(cv)

if f_qt is not None:
    # Cerchiamo la colonna della quotazione (spesso si chiama 'Qt. Attuale' o simile)
    # Rinominiamo per comodità
    f_qt.columns = [clean_name(c) for c in f_qt.columns]
    if 'NOME' in f_qt.columns: f_qt['NOME'] = f_qt['NOME'].apply(clean_name)
    # Cerchiamo la colonna numerica della quotazione
    qt_col = [c for c in f_qt.columns if 'QUOT' in c or 'QT' in c][0]
    f_qt['Quotazione_Ufficiale'] = f_qt[qt_col].apply(cv)

# TABS
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose & Plusvalenze", "📅 Vincoli", "🔄 Scambi"])

with t[2]: # TAB ROSE CON QUOTAZIONI
    st.subheader("🏃 Analisi Rose e Plusvalenze")
    if f_rs is not None:
        sq_l = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        sq = st.selectbox("Seleziona Squadra:", sq_l)
        
        # Uniamo la rosa con le quotazioni
        df_sq = f_rs[f_rs['Fantasquadra'] == sq].copy()
        
        if f_qt is not None:
            df_sq = pd.merge(df_sq, f_qt[['NOME', 'Quotazione_Ufficiale']], left_on='Nome', right_on='NOME', how='left').drop('NOME', axis=1)
            df_sq['Plusvalenza'] = df_sq['Quotazione_Ufficiale'] - df_sq['Prezzo']
            
            st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo', 'Quotazione_Ufficiale', 'Plusvalenza']].style.format({
                "Prezzo": "{:g}", "Quotazione_Ufficiale": "{:g}", "Plusvalenza": "{:+g}"
            }).background_gradient(subset=['Plusvalenza'], cmap='RdYlGn'), hide_index=True, use_container_width=True)
            
            tot_plus = df_sq['Plusvalenza'].sum()
            st.metric("Plusvalenza Totale Rosa", f"{tot_plus:+g}")
        else:
            st.warning("File quotazioni.csv non trovato. Caricalo per vedere le plusvalenze.")
            st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo']], hide_index=True)

with t[4]: # TAB SCAMBI (Sempre presente)
    # ... Qui rimane il codice dello scambio proporzionale che abbiamo fatto prima ...
    pass
