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
        if df.columns[0].startswith('Unnamed'):
            df = pd.read_csv(f, sep=',', engine='python', encoding='utf-8-sig', skiprows=1)
            df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# 2. CARICAMENTO E PULIZIA
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")

if f_rs is not None:
    f_rs['Nome'] = f_rs['Nome'].apply(clean_name)
    f_rs['Fantasquadra'] = f_rs['Fantasquadra'].apply(clean_name)
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)

if f_vn is not None:
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_name)
    f_vn['Squadra'] = f_vn['Squadra'].apply(clean_name)
    for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29']:
        if c in f_vn.columns: f_vn[c] = f_vn[c].apply(cv)
    f_vn['Spesa Complessiva'] = f_vn.get('Costo 2026-27', 0) + f_vn.get('Costo 2027-28', 0) + f_vn.get('Costo 2028-29', 0)

# TABS
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

# (Le tab 0-4 rimangono come prima)

with t[5]:
    st.subheader("🔄 Simulatore Scambi: Calcolo Nuovi Valori Individuali")
    if f_rs is not None:
        sq_l = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        
        def get_details(lista_nomi):
            dati = []
            for n in lista_nomi:
                p = f_rs[f_rs['Nome'] == n]['Prezzo'].values[0]
                v = f_vn[f_vn['Giocatore'] == n]['Spesa Complessiva'].values[0] if (f_vn is not None and n in f_vn['Giocatore'].values) else 0.0
                dati.append({'Giocatore': n, 'Acquisto': p, 'Vincoli': v, 'Valore Reale': p + v})
            return pd.DataFrame(dati)

        c1, c2 = st.columns(2)
        with c1:
            sa = st.selectbox("Squadra A:", sq_l, key="sa_fin")
            ga_list = st.multiselect("Giocatori ceduti da A:", f_rs[f_rs['Fantasquadra']==sa]['Nome'], key="ga_fin")
            df_a = get_details(ga_list)
            if not df_a.empty:
                st.dataframe(df_a, hide_index=True)
        
        with c2:
            sb = st.selectbox("Squadra B:", [s for s in sq_l if s != sa], key="sb_fin")
            gb_list = st.multiselect("Giocatori ceduti da B:", f_rs[f_rs['Fantasquadra']==sb]['Nome'], key="gb_fin")
            df_b = get_details(gb_list)
            if not df_b.empty:
                st.dataframe(df_b, hide_index=True)

        st.write("---")
        num_tot = len(ga_list) + len(gb_list)
        
        if num_tot > 0:
            somma_valori = (df_a['Valore Reale'].sum() if not df_a.empty else 0) + (df_b['Valore Reale'].sum() if not df_b.empty else 0)
            nuovo_valore = somma_valori / num_tot
            
            st.success(f"### 💎 Punto di Incontro: {nuovo_valore:g} crediti")
            
            st.markdown("#### 📋 Nuovo Valore a Bilancio per singolo giocatore:")
            tutti_giocatori = ga_list + gb_list
            for g in tutti_giocatori:
                st.write(f"✅ **{g}**: passerà a un valore di **{nuovo_valore:g}**")

            # Analisi Saldo Squadre
            st.write("---")
            col_a, col_b = st.columns(2)
            with col_a:
                bilancio_a = (nuovo_valore * len(gb_list)) - (df_a['Valore Reale'].sum() if not df_a.empty else 0)
                st.metric(f"Saldo Bilancio {sa}", f"{bilancio_a:+g}")
            with col_b:
                bilancio_b = (nuovo_valore * len(ga_list)) - (df_b['Valore Reale'].sum() if not df_b.empty else 0)
                st.metric(f"Saldo Bilancio {sb}", f"{bilancio_b:+g}")
        else:
            st.info("Aggiungi i giocatori per vedere il nuovo valore di Lautaro e degli altri coinvolti.")
