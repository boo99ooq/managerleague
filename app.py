import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# CSS "DI CEMENTO" PER IL GRASSETTO
st.markdown("""
<style>
    /* Forza grassetto su TUTTO il testo visibile */
    html, body, [data-testid="stAppViewContainer"], .st-emotion-cache-10trblm {
        font-weight: bold !important;
        font-family: 'Source Sans Pro', sans-serif;
    }

    /* Target specifico per le tabelle Streamlit */
    [data-testid="stTable"] td, [data-testid="stTable"] th {
        font-weight: bold !important;
        font-size: 1.1rem !important;
        color: black !important;
    }

    /* Target per le intestazioni dei Dataframe */
    [data-testid="stDataFrame"] * {
        font-weight: bold !important;
    }

    /* Forza grassetto sui menu a tendina e bottoni */
    .stSelectbox div[data-baseweb="select"] * {
        font-weight: bold !important;
        color: black !important;
    }
    
    .stMultiSelect div[data-baseweb="select"] * {
        font-weight: bold !important;
    }

    /* Card Scambi e Tagli */
    .player-card, .patrimonio-box, .cut-box {
        font-weight: bold !important;
        border: 3px solid !important;
    }
    
    /* Metriche (Punti e Budget) */
    [data-testid="stMetricValue"] {
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI PULIZIA ---
def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str.upper()

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try:
        return float(str(val).replace(',', '.'))
    except:
        return 0.0

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True)
        if df.columns[0].startswith('Unnamed') or df.empty:
            df = pd.read_csv(f, skiprows=1, engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# --- CARICAMENTO E MAPPATURA ---
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Nome'] = f_rs['Nome'].apply(clean_string)
    f_rs = f_rs.dropna(subset=['Squadra_N', 'Nome'])
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_string)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- MAIN ---
st.title("⚽ MUYFANTAMANAGER")
t = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "✂️ TAGLI"])

with t[0]: # CLASSIFICHE (Usiamo st.table per forzare il grassetto HTML)
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 CLASSIFICA PUNTI")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            df_punti = f_pt[['Posizione','Giocatore','P_N']].sort_values('Posizione').head(10)
            st.table(df_punti.astype(str)) # Convertiamo in stringa per evitare decimali brutti
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ SCONTRI DIRETTI")
            f_sc['P_S'] = f_sc['Punti'].apply(to_num)
            st.table(f_sc[['Posizione','Giocatore','P_S']].sort_values('Posizione').astype(str))

with t[1]: # BUDGET
    if f_rs is not None:
        st.subheader("💰 BUDGET E PATRIMONIO")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI EXTRA'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['PATRIMONIO TOTALE'] = bu['SPESA ROSE'] + bu['SPESA VINCOLI'] + bu['CREDITI EXTRA']
        
        st.bar_chart(bu.set_index("Squadra_N")[['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI EXTRA']])
        st.table(bu.sort_values("PATRIMONIO TOTALE", ascending=False).astype(str))

with t[2]: # ROSE
    if f_rs is not None:
        sq = st.selectbox("SELEZIONA SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="rose_sel")
        df_sq = f_rs[f_rs['Squadra_N'] == sq][['Ruolo', 'Nome', 'Prezzo_N']]
        st.table(df_sq.astype(str))

with t[3]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 DETTAGLIO VINCOLI")
        sq_v = st.selectbox("FILTRA SQUADRA", ["TUTTE"] + sorted([s for s in f_vn['Sq_N'].unique() if s]), key="vinc_sel")
        df_v_display = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.table(df_v_display[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False).astype(str))

with t[4]: # SCAMBI
    # ... (Stessa logica ricalcolo patrimonio, ma i risultati li mostriamo con st.markdown)
    st.info("Utilizza il simulatore per ricalcolare i valori. I risultati sono evidenziati in grassetto nelle card sottostanti.")
    # [Codice scambi precedente con card blue/red]

# ... (Restante codice Tagli e Sidebar rimane invariato perché usa Markdown/HTML che accetta il grassetto)
