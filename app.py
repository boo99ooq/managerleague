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
# Mappatura specifica per il tuo file quotazioni.csv
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

def clean_role(r):
    if pd.isna(r): return "NONE"
    r = str(r).strip().upper()
    # Se il ruolo è una singola lettera (P, D, C, A), lo espandiamo
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

if f_rs is not None:
    f_rs['Nome'] = f_rs['Nome'].apply(clean_name)
    f_rs['Ruolo'] = f_rs['Ruolo'].apply(clean_role)
    f_rs['Fantasquadra'] = f_rs['Fantasquadra'].apply(clean_name)
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)

if f_qt is not None:
    # Adattiamo alle colonne del tuo file: R, Nome, Qt.A
    f_qt = f_qt.rename(columns={'R': 'Ruolo_QT', 'Nome': 'Nome_QT', 'Qt.A': 'Quotazione'})
    f_qt['Nome_QT'] = f_qt['Nome_QT'].apply(clean_name)
    f_qt['Ruolo_QT'] = f_qt['Ruolo_QT'].apply(clean_role)
    f_qt['Quotazione'] = f_qt['Quotazione'].apply(cv)

if f_vn is not None:
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_name)
    f_vn['Squadra'] = f_vn['Squadra'].apply(clean_name)
    for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29']:
        if c in f_vn.columns: f_vn[c] = f_vn[c].apply(cv)
    f_vn['Spesa Complessiva'] = f_vn.get('Costo 2026-27', 0) + f_vn.get('Costo 2027-28', 0) + f_vn.get('Costo 2028-29', 0)

# 3. UNIONE DATI (PLUSVALENZE)
if f_rs is not None and f_qt is not None:
    f_rs = pd.merge(f_rs, f_qt, left_on=['Nome', 'Ruolo'], right_on=['Nome_QT', 'Ruolo_QT'], how='left')
    f_rs['Plusvalenza'] = f_rs['Quotazione'] - f_rs['Prezzo']

# 4. TABS
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

with t[1]: # BUDGET CON VALORE DI MERCATO
    if f_rs is not None:
        st.subheader("💰 Bilancio e Valore Rosa Attuale")
        # Calcoliamo il costo d'acquisto e il valore attuale (quotazione)
        eco = f_rs.groupby('Fantasquadra').agg({'Prezzo': 'sum', 'Quotazione': 'sum'}).reset_index()
        eco.columns = ['Fantasquadra', 'Investimento', 'Valore Mercato']
        eco['Crediti Disponibili'] = eco['Fantasquadra'].map(bg_ex).fillna(0)
        
        if f_vn is not None:
            v_sum = f_vn.groupby('Squadra')['Spesa Complessiva'].sum().reset_index()
            v_sum.columns = ['Fantasquadra', 'Vincoli']
            eco = pd.merge(eco, v_sum, on='Fantasquadra', how='left').fillna(0)
        else: eco['Vincoli'] = 0
        
        eco['Patrimonio Totale'] = eco['Valore Mercato'] + eco['Crediti Disponibili'] + eco['Vincoli']
        
        st.dataframe(eco.sort_values('Patrimonio Totale', ascending=False).style.background_gradient(subset=['Valore Mercato'], cmap='Greens').format({c: "{:g}" for c in eco.columns if c != 'Fantasquadra'}), hide_index=True, use_container_width=True)

with t[3]: # ROSE CON DETTAGLIO QUOTAZIONI
    if f_rs is not None:
        sq_l = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        sq = st.selectbox("Seleziona Squadra:", sq_l, key="rose_sel")
        df_sq = f_rs[f_rs['Fantasquadra'] == sq].copy()
        
        if 'Quotazione' in df_sq.columns:
            # Mostriamo la tabella con i colori per le plusvalenze
            st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo', 'Quotazione', 'Plusvalenza']].style.background_gradient(subset=['Plusvalenza'], cmap='RdYlGn').format({"Prezzo": "{:g}", "Quotazione": "{:g}", "Plusvalenza": "{:+g}"}), hide_index=True, use_container_width=True)
            
            p_tot = df_sq['Plusvalenza'].sum()
            st.metric("Plusvalenza Totale Rosa", f"{p_tot:+g}", delta_color="normal")
        else:
            st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo']], hide_index=True, use_container_width=True)

with t[5]: # SIMULATORE SCAMBI (Invariato nella logica proporzionale)
    # ... (Qui rimane il codice degli scambi che abbiamo perfezionato prima)
    pass
