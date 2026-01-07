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
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

# Configurazione Budget Extra e Mappature
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "NICHO:79": "NICHOLAS"}
map_r = {"P": "PORTIERE", "D": "DIFENSORE", "C": "CENTROCAMPISTA", "A": "ATTACCANTE"}

def cv(v):
    if pd.isna(v): return 0.0
    try:
        s = str(v).replace('"', '').replace(',', '.').strip()
        return float(s) if s != "" else 0.0
    except: return 0.0

def clean_name(s):
    if pd.isna(s) or str(s).strip().upper() == "NONE" or str(s).strip() == "": return "SKIP"
    s = str(s).split(':')[0].replace('*', '').replace('"', '').strip().upper()
    return map_n.get(s, s)

def get_match_key(name):
    """Crea una chiave 'COGNOME I' per il match delle quotazioni"""
    name = clean_name(name)
    parts = name.replace("-", " ").split()
    if not parts: return ""
    surname = parts[0]
    initial = parts[1][0] if len(parts) > 1 else ""
    return f"{surname} {initial}".strip()

def clean_role(r):
    if pd.isna(r): return "NONE"
    r = str(r).strip().upper()
    return map_r.get(r, r)

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, sep=',', engine='python', encoding='utf-8-sig', skip_blank_lines=True)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# 2. CARICAMENTO E PULIZIA
f_sc, f_pt, f_rs, f_vn, f_qt = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv"), ld("quotazioni.csv")

# Elaborazione Quotazioni (R, Nome, Qt.A)
if f_qt is not None:
    f_qt = f_qt.rename(columns={'R': 'Ruolo_QT', 'Nome': 'Nome_QT', 'Qt.A': 'Quotazione'})
    f_qt['MatchKey'] = f_qt['Nome_QT'].apply(get_match_key)
    f_qt['Ruolo_QT'] = f_qt['Ruolo_QT'].apply(clean_role)
    f_qt['Quotazione'] = f_qt['Quotazione'].apply(cv)

# Elaborazione Rose e Match Quotazioni
if f_rs is not None:
    f_rs['Nome'] = f_rs['Nome'].apply(clean_name)
    f_rs['Ruolo'] = f_rs['Ruolo'].apply(clean_role)
    f_rs['Fantasquadra'] = f_rs['Fantasquadra'].apply(clean_name)
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)
    f_rs['MatchKey'] = f_rs['Nome'].apply(get_match_key)
    
    if f_qt is not None:
        # Match su Ruolo e MatchKey (Cognome + Iniziale)
        f_rs = pd.merge(f_rs, f_qt[['MatchKey', 'Ruolo_QT', 'Quotazione']], 
                        left_on=['MatchKey', 'Ruolo'], right_on=['MatchKey', 'Ruolo_QT'], how='left').drop('Ruolo_QT', axis=1)
        f_rs['Plusvalenza'] = f_rs['Quotazione'] - f_rs['Prezzo']

# Elaborazione Vincoli
if f_vn is not None:
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_name)
    f_vn['Squadra'] = f_vn['Squadra'].apply(clean_name)
    for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29']:
        if c in f_vn.columns: f_vn[c] = f_vn[c].apply(cv)
    f_vn['Spesa Complessiva'] = f_vn.get('Costo 2026-27', 0) + f_vn.get('Costo 2027-28', 0) + f_vn.get('Costo 2028-29', 0)

# 3. TABS
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

with t[1]: # BUDGET (FIX TYPEERROR)
    if f_rs is not None:
        st.subheader("💰 Bilancio e Valore Rosa")
        agg_cols = {'Prezzo': 'sum'}
        if 'Quotazione' in f_rs.columns: agg_cols['Quotazione'] = 'sum'
        
        eco = f_rs.groupby('Fantasquadra').agg(agg_cols).reset_index()
        eco.columns = ['Fantasquadra', 'Investimento'] + (['Valore Mercato'] if 'Quotazione' in agg_cols else [])
        eco['Crediti Disponibili'] = eco['Fantasquadra'].map(bg_ex).fillna(0)
        
        if f_vn is not None:
            # Calcolo sicuro dei vincoli per squadra
            v_sum = f_vn.groupby('Squadra')['Spesa Complessiva'].sum().reset_index()
            v_sum.columns = ['Fantasquadra', 'Vincoli']
            eco = pd.merge(eco, v_sum, on='Fantasquadra', how='left').fillna(0)
        
        val_rif = 'Valore Mercato' if 'Valore Mercato' in eco.columns else 'Investimento'
        eco['Patrimonio'] = eco[val_rif] + eco['Crediti Disponibili'] + eco.get('Vincoli', 0)
        
        st.dataframe(eco.sort_values('Patrimonio', ascending=False).style.background_gradient(subset=[val_rif], cmap='Greens').format({c: "{:g}" for c in eco.columns if c != 'Fantasquadra'}), hide_index=True, use_container_width=True)

with t[3]: # ROSE (VISUALIZZAZIONE QUOTAZIONI)
    if f_rs is not None:
        sq_l = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        sq = st.selectbox("Seleziona Squadra:", sq_l, key="rose_view")
        df_sq = f_rs[f_rs['Fantasquadra'] == sq].copy()
        
        cols = ['Ruolo', 'Nome', 'Prezzo']
        if 'Quotazione' in df_sq.columns:
            cols += ['Quotazione', 'Plusvalenza']
            st.dataframe(df_sq[cols].sort_values('Plusvalenza', ascending=False).style.background_gradient(subset=['Plusvalenza'], cmap='RdYlGn').format({"Prezzo": "{:g}", "Quotazione": "{:g}", "Plusvalenza": "{:+g}"}), hide_index=True, use_container_width=True)
            st.metric("Plusvalenza Totale Squadra", f"{df_sq['Plusvalenza'].sum():+g}")
        else:
            st.dataframe(df_sq[cols], hide_index=True, use_container_width=True)

# ... (Le altre tab Classifiche, Strategia, Vincoli e Scambi mantengono le logiche precedenti)
