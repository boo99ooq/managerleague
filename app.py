import streamlit as st
import pandas as pd
import os

# 1. SETUP E STILE (FIX LEGGIBILITÀ E GRASSETTO)
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

# Dati Budget Extra (da regolamento)
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "NICHO:79": "NICHOLAS"}

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

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, sep=',', engine='python', encoding='utf-8-sig', skip_blank_lines=True)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# 2. CARICAMENTO E PULIZIA
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")

def process_df(df, col_name):
    if df is not None:
        df = df.dropna(subset=[col_name]).copy()
        df[col_name] = df[col_name].apply(clean_name)
        df = df[df[col_name] != "SKIP"]
        return df
    return None

f_sc, f_pt, f_rs, f_vn = process_df(f_sc, 'Giocatore'), process_df(f_pt, 'Giocatore'), process_df(f_rs, 'Fantasquadra'), process_df(f_vn, 'Squadra')

def style_rose(row):
    colors = {'Portiere':'#E3F2FD','Difensore':'#E8F5E9','Centrocampista':'#FFFDE7','Attaccante':'#FFEBEE','Giovani':'#F3E5F5'}
    return [f'background-color: {colors.get(row["Ruolo"], "#FFFFFF")}; color: black; font-weight: bold;'] * len(row)

t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

# ... (Tab Classifiche, Budget, Strategia e Rose rimangono invariate come nell'ultima versione) ...

with t[4]: # VINCOLI CON GRADIENTI
    st.subheader("📅 Gestione Vincoli")
    if f_vn is not None:
        # Pulizia e calcoli
        for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29', 'Durata (anni)']:
            f_vn[c] = f_vn[c].apply(cv) if c in f_vn.columns else 0.0
        
        f_vn['Spesa Complessiva'] = f_vn['Costo 2026-27'] + f_vn.get('Costo 2027-28', 0) + f_vn.get('Costo 2028-29', 0)
        
        v1, v2 = st.columns([1, 2.5])
        with v1:
            st.write("**Riepilogo Squadre**")
            deb = f_vn.groupby('Squadra')['Spesa Complessiva'].sum().reset_index().sort_values('Spesa Complessiva', ascending=False)
            st.dataframe(
                deb.style.background_gradient(subset=['Spesa Complessiva'], cmap='Oranges')
                .format({"Spesa Complessiva": "{:g}"})
                .set_properties(**{'font-weight': 'bold'}),
                hide_index=True, use_container_width=True
            )
        
        with v2:
            st.write("**Dettaglio Giocatori**")
            sv = st.selectbox("Squadra:", sorted([x for x in f_vn['Squadra'].unique() if x != "SKIP"]), key="v_sel")
            cols_v = ['Giocatore', 'Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29', 'Durata (anni)', 'Spesa Complessiva']
            present_v = [c for c in cols_v if c in f_vn.columns]
            det = f_vn[f_vn['Squadra'] == sv][present_v].dropna(subset=['Giocatore']).copy()
            
            # Applicazione gradienti su dettaglio
            st.dataframe(
                det.style.background_gradient(subset=['Costo 2026-27'], cmap='YlGn')
                .background_gradient(subset=['Spesa Complessiva'], cmap='YlOrBr')
                .format({c: "{:g}" for c in present_v if c != 'Giocatore'})
                .set_properties(**{'font-weight': 'bold'}),
                hide_index=True, use_container_width=True
            )
