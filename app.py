import streamlit as st
import pandas as pd
import os

# 1. SETUP
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- FUNZIONE PREZZI CORRETTA ---
def cv(v):
    if pd.isna(v) or str(v).strip() == "": return 0.0
    s = str(v).replace('"', '').strip()
    # Se il numero ha la virgola, è il decimale (es. 15,5)
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    # Se non ha virgola ma ha un punto solo verso la fine, è decimale (es 15.0)
    # Se ha un punto e poi 3 cifre, è un migliaio (es 1.000) -> lo rimuoviamo
    try:
        val = float(s)
        # Se il valore è enorme (es. un 15 diventato 1500), correggiamo
        return val
    except:
        return 0.0

def clean_s(s):
    if pd.isna(s): return ""
    return str(s).replace('*', '').strip().upper()

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True)
        if df.columns[0].startswith('Unnamed') or df.empty:
            df = pd.read_csv(f, skiprows=1, engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# CARICAMENTO
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")

# ELABORAZIONE
if f_rs is not None:
    # Applichiamo una conversione sicura: se il numero è > 500 probabilmente è un errore di virgola (es. 15.0 -> 150)
    f_rs['Prezzo_N'] = pd.to_numeric(f_rs['Prezzo'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_s).replace(map_n)

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_s).replace(map_n)
    v_cols = [c for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29'] if c in f_vn.columns]
    for c in v_cols: 
        f_vn[c] = pd.to_numeric(f_vn[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    # ELIMINA NOMI DOPPI NEI VINCOLI
    f_vn = f_vn.drop_duplicates(subset=['Sq_N', 'Giocatore'])

t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    with c1:
        if f_pt is not None:
            st.subheader("🎯 Punti")
            f_pt['Punti'] = pd.to_numeric(f_pt['Punti Totali'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            f_pt['FM'] = pd.to_numeric(f_pt['Media'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            st.dataframe(f_pt[['Posizione','Giocatore','Punti','FM']].sort_values('Posizione')
                         .style.background_gradient(subset=['Punti', 'FM'], cmap='YlGn')
                         .format({"Punti": "{:g}", "FM": "{:.2f}"}), hide_index=True, use_container_width=True)
    with c2:
        if f_sc is not None:
            st.subheader("⚔️ Scontri Diretti")
            f_sc['Punti_S'] = pd.to_numeric(f_sc['Punti'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            st.dataframe(f_sc[['Posizione','Giocatore','Punti_S','Gol Fatti','Gol Subiti']]
                         .style.background_gradient(subset=['Punti_S'], cmap='Blues')
                         .format({"Punti_S": "{:g}"}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        st.subheader("💰 Bilancio Globale")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index()
        bu.columns = ['Squadra', 'Spesa Rose']
        
        if f_vn is not None:
            v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index()
            bu = pd.merge(bu, v_sum, left_on='Squadra', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1)
            bu.rename(columns={'Tot_Vincolo': 'Spesa Vincoli'}, inplace=True)
        else: bu['Spesa Vincoli'] = 0
        
        bu['Crediti Disponibili'] = bu['Squadra'].map(bg_ex).fillna(0)
        bu['Patrimonio Reale'] = bu['Spesa Rose'] + bu['Spesa Vincoli'] + bu['Crediti Disponibili']
        
        cols_grad = ['Spesa Rose', 'Spesa Vincoli', 'Crediti Disponibili', 'Patrimonio Reale']
        st.dataframe(bu.sort_values('Patrimonio Reale', ascending=False)
                     .style.background_gradient(cmap='YlOrRd', subset=cols_grad)
                     .format({c: "{:g}" for c in cols_grad}), hide_index=True, use_container_width=True)

with t[2]: # ROSE
    if f_rs is not None:
        lista_sq = sorted([s for s in f_rs['Squadra_N'].unique() if s and '*' not in s])
        sq = st.selectbox("Squadra:", lista_sq)
        df_sq = f_rs[f_rs['Squadra_N'] == sq].copy()
        
        def color_ruoli(row):
            r = str(row['Ruolo']).upper()
            bg = '#E3F2FD' if 'PORT' in r else '#E8F5E9' if 'DIF' in r else '#FFFDE7' if 'CEN' in r else '#FFEBEE' if 'ATT' in r else '#FFFFFF'
            return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
        
        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo_N']].style.apply(color_ruoli, axis=1).format({"Prezzo_N":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI (PULITI DAI DOPPIONI)
    if f_vn is not None:
        st.subheader("📅 Vincoli Pluriennali")
        lista_sq_v = sorted([s for s in f_vn['Sq_N'].unique() if s and '*' not in s])
        sq_v = st.selectbox("Filtra Squadra:", ["TUTTE"] + lista_sq_v)
        df_v_display = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        
        st.dataframe(df_v_display[['Squadra', 'Giocatore', 'Tot_Vincolo']].sort_values('Tot_Vincolo', ascending=False)
                     .style.background_gradient(subset=['Tot_Vincolo'], cmap='Purples')
                     .format("{:g}"), hide_index=True, use_container_width=True)
