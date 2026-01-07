import streamlit as st
import pandas as pd
import os

# 1. SETUP E STILE
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("<style>.stApp{background-color:#f4f7f6;} .stTabs{background-color:white; border-radius:10px; padding:10px;}</style>", unsafe_allow_html=True)
st.title("⚽ MuyFantaManager")

# Configurazione Budget e Mappatura nomi
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "NICHO:79": "NICHOLAS"}

def cv(v):
    if pd.isna(v): return 0
    try: return float(str(v).replace('"', '').replace(',', '.'))
    except: return 0

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

def process_df(df, col_name):
    if df is not None:
        df = df.dropna(subset=[col_name])
        df[col_name] = df[col_name].apply(clean_name)
        df = df[df[col_name] != "SKIP"]
        return df
    return None

f_sc, f_pt, f_rs, f_vn = process_df(f_sc, 'Giocatore'), process_df(f_pt, 'Giocatore'), process_df(f_rs, 'Fantasquadra'), process_df(f_vn, 'Squadra')

# Funzione per colorare i ruoli
def color_ruolo(row):
    colors = {
        'Portiere': 'background-color: #f0f4ff',
        'Difensore': 'background-color: #f0fff0',
        'Centrocampista': 'background-color: #fffdf0',
        'Attaccante': 'background-color: #fff0f0',
        'Giovani': 'background-color: #fcf0ff'
    }
    return [colors.get(row['Ruolo'], '')] * len(row)

# Sidebar Ricerca
if f_rs is not None:
    st.sidebar.header("🔍 Cerca Giocatore")
    s = st.sidebar.text_input("Nome:").upper()
    if s:
        res = f_rs[f_rs['Nome'].str.upper().str.contains(s, na=False)].copy()
        if not res.empty:
            # Grassetto sul nome nella sidebar
            st.sidebar.dataframe(res[['Nome', 'Fantasquadra', 'Prezzo']].style.format({"Prezzo": "{:g}"}).set_properties(**{'font-weight': 'bold'}, subset=['Nome']), hide_index=True)
        else: st.sidebar.warning("Nessuno trovato")

t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔥 Scontri")
        if f_sc is not None: 
            st.dataframe(f_sc.style.set_properties(**{'font-weight': 'bold'}, subset=['Giocatore']), hide_index=True, use_container_width=True)
    with c2:
        st.subheader("🎯 Punti")
        if f_pt is not None:
            f_pt['Punti Totali'] = f_pt['Punti Totali'].apply(cv)
            # Grassetto su Giocatore
            st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali','Media']].sort_values('Punti Totali', ascending=False).style.format({"Punti Totali": "{:g}", "Media": "{:.2f}"}).set_properties(**{'font-weight': 'bold'}, subset=['Giocatore']), hide_index=True, use_container_width=True)

if f_rs is not None:
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)
    with t[1]: # BUDGET
        st.subheader("💰 Bilancio Globale")
        eco = f_rs.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        eco['Crediti Disponibili'] = eco['Fantasquadra'].map(bg_ex).fillna(0)
        if f_vn is not None:
            f_vn['Costo 2026-27'] = f_vn['Costo 2026-27'].apply(cv)
            v_sum = f_vn.groupby('Squadra')['Costo 2026-27'].sum().reset_index()
            v_sum.columns = ['Fantasquadra', 'Vincoli']
            eco = pd.merge(eco, v_sum, on='Fantasquadra', how='left').fillna(0)
        else: eco['Vincoli'] = 0
        eco['Totale'] = eco['Prezzo'] + eco['Crediti Disponibili'] + eco['Vincoli']
        st.dataframe(eco.sort_values('Totale', ascending=False).style.background_gradient(subset=['Totale'], cmap='RdYlGn').background_gradient(subset=['Crediti Disponibili'], cmap='YlGn').format({"Prezzo": "{:g}", "Crediti Disponibili": "{:g}", "Vincoli": "{:g}", "Totale": "{:g}"}), hide_index=True, use_container_width=True)
    
    with t[2]: # STRATEGIA
        st.subheader("🧠 Strategia")
        cs1, cs2 = st.columns([1.5, 1])
        with cs1:
            piv = f_rs.pivot_table(index='Fantasquadra', columns='Ruolo', values='Nome', aggfunc='count').fillna(0).astype(int)
            r_ord = ['Portiere', 'Difensore', 'Centrocampista', 'Attaccante', 'Giovani']
            st.dataframe(piv[[r for r in r_ord if r in piv.columns]], use_container_width=True)
        with cs2:
            st.write("**💎 Top Player**")
            idx = f_rs.groupby('Fantasquadra')['Prezzo'].idxmax()
            # Grassetto sul nome del Top Player
            st.dataframe(f_rs.loc[idx, ['Fantasquadra', 'Nome', 'Prezzo']].sort_values('Prezzo', ascending=False).style.format({"Prezzo": "{:g}"}).set_properties(**{'font-weight': 'bold'}, subset=['Nome']), hide_index=True, use_container_width=True)

    with t[3]: # ROSE COLORATE + GRASSETTO
        st.subheader("🏃 Dettaglio Rose")
        sq_list = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        sq = st.selectbox("Seleziona Squadra:", sq_list)
        df_sq = f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo']].sort_values('Prezzo', ascending=False)
        # Combinazione colori ruolo + grassetto sul nome
        st.dataframe(df_sq.style.apply(color_ruolo, axis=1).set_properties(**{'font-weight': 'bold'}, subset=['Nome']).format({"Prezzo": "{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # VINCOLI (GRASSETTO)
    st.subheader("📅 Gestione Vincoli")
    if f_vn is not None:
        if 'Durata (anni)' in f_vn.columns: f_vn['Durata (anni)'] = f_vn['Durata (anni)'].apply(cv)
        v1, v2 = st.columns([1, 2])
        with v1:
            deb = f_vn.groupby('Squadra')['Costo 2026-27'].sum().reset_index().sort_values('Costo 2026-27', ascending=False)
            st.dataframe(deb.style.format({"Costo 2026-27": "{:g}"}), hide_index=True, use_container_width=True)
        with v2:
            lista_sq = sorted([x for x in f_vn['Squadra'].unique() if x != "SKIP"])
            sv = st.selectbox("Seleziona Squadra per Dettaglio:", lista_sq, key="v_sel")
            det = f_vn[f_vn['Squadra'] == sv][['Giocatore', 'Costo 2026-27', 'Durata (anni)']].dropna(subset=['Giocatore'])
            # Grassetto su Giocatore
            st.dataframe(det.style.format({"Costo 2026-27": "{:g}", "Durata (anni)": "{:g}"}).set_properties(**{'font-weight': 'bold'}, subset=['Giocatore']), hide_index=True, use_container_width=True)
