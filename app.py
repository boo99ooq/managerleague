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

# ... (Le prime 5 Tab rimangono invariate per brevità, ma nel tuo file tieni quelle esistenti) ...

with t[5]: # NUOVO SIMULATORE SCAMBI MULTIPLI
    st.subheader("🔄 Simulatore Scambi Multipli (Punto di Incontro)")
    if f_rs is not None:
        sq_l = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        
        def get_total_package_value(lista_nomi):
            tot_p, tot_v = 0.0, 0.0
            for n in lista_nomi:
                p = f_rs[f_rs['Nome'] == n]['Prezzo'].values[0]
                v = f_vn[f_vn['Giocatore'] == n]['Spesa Complessiva'].values[0] if (f_vn is not None and n in f_vn['Giocatore'].values) else 0.0
                tot_p += p
                tot_v += v
            return tot_p, tot_v

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🏟️ Squadra A")
            sa = st.selectbox("Seleziona Squadra A:", sq_l, key="sa_m")
            ga_list = st.multiselect("Giocatori ceduti da A:", f_rs[f_rs['Fantasquadra']==sa]['Nome'], key="ga_m")
            pa, va = get_total_package_value(ga_list)
            vta = pa + va
            st.metric("Valore Totale Pacchetto A", f"{vta:g}")
            if ga_list: st.caption(f"Base: {pa:g} + Vincoli: {va:g}")

        with c2:
            st.markdown("### 🏟️ Squadra B")
            sb = st.selectbox("Seleziona Squadra B:", [s for s in sq_l if s != sa], key="sb_m")
            gb_list = st.multiselect("Giocatori ceduti da B:", f_rs[f_rs['Fantasquadra']==sb]['Nome'], key="gb_m")
            pb, vb = get_total_package_value(gb_list)
            vtb = pb + vb
            st.metric("Valore Totale Pacchetto B", f"{vtb:g}")
            if gb_list: st.caption(f"Base: {pb:g} + Vincoli: {vb:g}")

        st.write("---")
        num_tot = len(ga_list) + len(gb_list)
        
        if num_tot > 0:
            pi = (vta + vtb) / num_tot
            st.markdown(f"### 🤝 Punto di Incontro a giocatore: **{pi:g} crediti**")
            
            val_tot_scambio = vta + vtb
            st.write(f"Valore complessivo dell'operazione: **{val_tot_scambio:g}** crediti per **{num_tot}** giocatori.")
            
            # Analisi Impatto Pacchetto
            da = (pi * len(gb_list)) - vta # Valore ricevuto - Valore ceduto
            db = (pi * len(ga_list)) - vtb
            
            res1, res2 = st.columns(2)
            with res1:
                st.info(f"**{sa}**: Saldo operazione **{da:+g}** crediti")
            with res2:
                st.info(f"**{sb}**: Saldo operazione **{db:+g}** crediti")
        else:
            st.warning("Seleziona almeno un giocatore per parte per calcolare lo scambio.")
