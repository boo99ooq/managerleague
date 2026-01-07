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
    # Portiamo tutto in MAIUSCOLO per evitare errori di match tra file diversi
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

# Pulizia Giocatori e Squadre (TUTTO MAIUSCOLO)
if f_rs is not None:
    f_rs['Nome'] = f_rs['Nome'].apply(clean_name)
    f_rs['Fantasquadra'] = f_rs['Fantasquadra'].apply(clean_name)

if f_vn is not None:
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_name)
    f_vn['Squadra'] = f_vn['Squadra'].apply(clean_name)

if f_pt is not None:
    f_pt['Giocatore'] = f_pt['Giocatore'].apply(clean_name)

# Calcolo Spesa Complessiva Vincoli
if f_vn is not None:
    for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29']:
        if c in f_vn.columns: f_vn[c] = f_vn[c].apply(cv)
    f_vn['Spesa Complessiva'] = f_vn.get('Costo 2026-27', 0) + f_vn.get('Costo 2027-28', 0) + f_vn.get('Costo 2028-29', 0)

def style_rose(row):
    colors = {'Portiere':'#E3F2FD','Difensore':'#E8F5E9','Centrocampista':'#FFFDE7','Attaccante':'#FFEBEE','Giovani':'#F3E5F5'}
    return [f'background-color: {colors.get(row["Ruolo"], "#FFFFFF")}; color: black; font-weight: bold;'] * len(row)

# TABS
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_sc is not None:
        with c1:
            st.subheader("🔥 Scontri")
            st.dataframe(f_sc.style.set_properties(**{'font-weight': 'bold'}), hide_index=True, use_container_width=True)
    if f_pt is not None:
        with c2:
            st.subheader("🎯 Punti")
            f_pt['Punti Totali'] = f_pt['Punti Totali'].apply(cv)
            st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali','Media']].sort_values('Posizione').style.background_gradient(subset=['Punti Totali'], cmap='Greens').format({"Punti Totali": "{:g}", "Media": "{:.2f}"}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)
        st.subheader("💰 Bilancio Globale")
        eco = f_rs.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        eco.columns = ['Fantasquadra', 'Valore Rosa']
        eco['Crediti Disponibili'] = eco['Fantasquadra'].map(bg_ex).fillna(0)
        if f_vn is not None:
            v_sum = f_vn.groupby('Squadra')['Spesa Complessiva'].sum().reset_index()
            v_sum.columns = ['Fantasquadra', 'Vincoli']
            eco = pd.merge(eco, v_sum, on='Fantasquadra', how='left').fillna(0)
        else: eco['Vincoli'] = 0
        eco['Totale'] = eco['Valore Rosa'] + eco['Crediti Disponibili'] + eco['Vincoli']
        st.dataframe(eco.sort_values('Totale', ascending=False).style.background_gradient(subset=['Valore Rosa'], cmap='YlOrRd').background_gradient(subset=['Crediti Disponibili'], cmap='GnBu').background_gradient(subset=['Vincoli'], cmap='Purples').background_gradient(subset=['Totale'], cmap='YlGn').format({"Valore Rosa": "{:g}", "Crediti Disponibili": "{:g}", "Vincoli": "{:g}", "Totale": "{:g}"}), hide_index=True, use_container_width=True)

with t[2]: # STRATEGIA
    if f_rs is not None:
        st.subheader("🧠 Strategia")
        piv = f_rs.pivot_table(index='Fantasquadra', columns='Ruolo', values='Nome', aggfunc='count').fillna(0).astype(int)
        st.dataframe(piv.style.set_properties(**{'font-weight': 'bold'}), use_container_width=True)

with t[3]: # ROSE
    if f_rs is not None:
        sq_list = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        sq = st.selectbox("Seleziona Squadra:", sq_list)
        df_sq = f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo']].sort_values('Prezzo', ascending=False)
        st.dataframe(df_sq.style.apply(style_rose, axis=1).format({"Prezzo": "{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 Gestione Vincoli")
        sv = st.selectbox("Squadra:", sorted([x for x in f_vn['Squadra'].unique() if x != "SKIP"]), key="v_sel")
        det = f_vn[f_vn['Squadra'] == sv].dropna(subset=['Giocatore'])
        st.dataframe(det.style.background_gradient(subset=['Spesa Complessiva'], cmap='YlOrBr').format({c: "{:g}" for c in det.columns if c != 'Giocatore' and c != 'Squadra'}), hide_index=True, use_container_width=True)

with t[5]: # SCAMBI (FIX MAIUSCOLO E VINCOLI)
    st.subheader("🔄 Simulatore Scambi (Punto di Incontro)")
    if f_rs is not None:
        sq_l = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        
        def get_val(nome):
            # Prezzo dalle rose
            p = f_rs[f_rs['Nome'] == nome]['Prezzo'].values[0]
            # Vincoli (Somma Complessiva)
            v = 0.0
            if f_vn is not None and nome in f_vn['Giocatore'].values:
                v = f_vn[f_vn['Giocatore'] == nome]['Spesa Complessiva'].values[0]
            return p, v

        c1, c2 = st.columns(2)
        with c1:
            sa = st.selectbox("Squadra A:", sq_l, key="sa_f")
            ga = st.selectbox("Cede:", f_rs[f_rs['Fantasquadra']==sa]['Nome'], key="ga_f")
            pa, va = get_val(ga)
            vta = pa + va
            st.metric(f"Valore Reale {ga}", f"{vta:g}")
            st.caption(f"Base: {pa:g} + Vincoli: {va:g}")

        with c2:
            sb = st.selectbox("Squadra B:", [s for s in sq_l if s != sa], key="sb_f")
            gb = st.selectbox("Cede:", f_rs[f_rs['Fantasquadra']==sb]['Nome'], key="gb_f")
            pb, vb = get_val(gb)
            vtb = pb + vb
            st.metric(f"Valore Reale {gb}", f"{vtb:g}")
            st.caption(f"Base: {pb:g} + Vincoli: {vb:g}")

        st.write("---")
        pi = (vta + vtb) / 2
        st.markdown(f"### 🤝 Punto di Incontro: **{pi:g} crediti**")
        
        # Anteprima impatto
        da, db = pi - vta, pi - vtb
        st.info(f"**{sa}**: {ga} (scambio a {pi:g}) → Variazione Rosa: **{da:+g}**")
        st.info(f"**{sb}**: {gb} (scambio a {pi:g}) → Variazione Rosa: **{db:+g}**")
