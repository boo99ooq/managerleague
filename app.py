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

# Configurazione Budget e Mappature
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
    # Rimuoviamo eventuali iniziali puntate finali (es: "MARTINEZ L." -> "MARTINEZ")
    parts = s.split(' ')
    if len(parts) > 1 and len(parts[-1]) <= 2: 
        s = " ".join(parts[:-1]).strip()
    return map_n.get(s, s)

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

# 2. CARICAMENTO
f_sc, f_pt, f_rs, f_vn, f_qt = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv"), ld("quotazioni.csv")

# 3. ELABORAZIONE QUOTAZIONI
if f_qt is not None:
    # Cerchiamo di identificare le colonne correte (R, Nome, Qt.A)
    f_qt = f_qt.rename(columns={'R': 'Ruolo_QT', 'Nome': 'Nome_QT', 'Qt.A': 'Quotazione'})
    f_qt['Nome_Match'] = f_qt['Nome_QT'].apply(clean_name)
    f_qt['Ruolo_Match'] = f_qt['Ruolo_QT'].apply(clean_role)
    f_qt['Quotazione'] = f_qt['Quotazione'].apply(cv)

# 4. ELABORAZIONE ROSE E UNIONE
if f_rs is not None:
    f_rs['Nome'] = f_rs['Nome'].apply(clean_name)
    f_rs['Ruolo'] = f_rs['Ruolo'].apply(clean_role)
    f_rs['Fantasquadra'] = f_rs['Fantasquadra'].apply(clean_name)
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)
    
    if f_qt is not None:
        # Uniamo le rose con le quotazioni basandoci su Nome (pulito) e Ruolo
        f_rs = pd.merge(f_rs, f_qt[['Nome_Match', 'Ruolo_Match', 'Quotazione']], 
                        left_on=['Nome', 'Ruolo'], right_on=['Nome_Match', 'Ruolo_Match'], how='left')
        f_rs['Plusvalenza'] = f_rs['Quotazione'] - f_rs['Prezzo']
        
        # Diagnostica
        match_count = f_rs['Quotazione'].notna().sum()
        total_players = len(f_rs)
        st.sidebar.success(f"✅ Quotazioni caricate: {match_count}/{total_players} giocatori trovati.")

# 5. TABS
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

with t[1]: # TAB BUDGET
    if f_rs is not None:
        st.subheader("💰 Bilancio e Valore di Mercato")
        agg_cols = {'Prezzo': 'sum'}
        if 'Quotazione' in f_rs.columns: agg_cols['Quotazione'] = 'sum'
        
        eco = f_rs.groupby('Fantasquadra').agg(agg_cols).reset_index()
        eco.columns = ['Fantasquadra', 'Costo Rose'] + (['Valore Mercato'] if 'Quotazione' in agg_cols else [])
        
        eco['Crediti Disponibili'] = eco['Fantasquadra'].map(bg_ex).fillna(0)
        if f_vn is not None:
            v_sum = f_vn.groupby('Squadra').agg({'Costo 2026-27':'sum','Costo 2027-28':'sum','Costo 2028-29':'sum'}).sum(axis=1).reset_index()
            v_sum.columns = ['Fantasquadra', 'Vincoli']
            eco = pd.merge(eco, v_sum, on='Fantasquadra', how='left').fillna(0)
        
        target = 'Valore Mercato' if 'Valore Mercato' in eco.columns else 'Costo Rose'
        eco['Patrimonio'] = eco[target] + eco['Crediti Disponibili'] + eco.get('Vincoli', 0)
        
        st.dataframe(eco.sort_values('Patrimonio', ascending=False).style.background_gradient(subset=[target], cmap='Greens').format({c: "{:g}" for c in eco.columns if c != 'Fantasquadra'}), hide_index=True, use_container_width=True)

with t[3]: # TAB ROSE
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

# ... (Le altre tab Classifiche, Strategia, Vincoli e Scambi rimangono attive con le logiche precedenti)
