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

def process_df(df, col_name):
    if df is not None:
        df = df.dropna(subset=[col_name]).copy()
        df[col_name] = df[col_name].apply(clean_name)
        df = df[df[col_name] != "SKIP"]
        return df
    return None

f_sc, f_pt, f_rs, f_vn = process_df(f_sc, 'Giocatore'), process_df(f_pt, 'Giocatore'), process_df(f_rs, 'Fantasquadra'), process_df(f_vn, 'Squadra')

# Calcolo vincoli preventivo per simulatore e budget
if f_vn is not None:
    for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29']:
        f_vn[c] = f_vn[c].apply(cv) if c in f_vn.columns else 0.0
    f_vn['Spesa Complessiva'] = f_vn['Costo 2026-27'] + f_vn.get('Costo 2027-28', 0) + f_vn.get('Costo 2028-29', 0)

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
            cols_sc = f_sc.select_dtypes(include=['number']).columns
            st.dataframe(f_sc.style.background_gradient(subset=cols_sc, cmap='Blues'), hide_index=True, use_container_width=True)
    if f_pt is not None:
        with c2:
            st.subheader("🎯 Punti")
            f_pt['Punti Totali'] = f_pt['Punti Totali'].apply(cv)
            st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali','Media']].sort_values('Posizione').style.background_gradient(subset=['Punti Totali'], cmap='Greens').format({"Punti Totali": "{:g}", "Media": "{:.2f}"}), hide_index=True, use_container_width=True)
        st.write("---")
        p_min, p_max = f_pt['Punti Totali'].min() - 5, f_pt['Punti Totali'].max() + 5
        base = alt.Chart(f_pt).encode(x=alt.X('Giocatore:N', sort='-y'), y=alt.Y('Punti Totali:Q', scale=alt.Scale(domain=[p_min, p_max])))
        st.altair_chart((base.mark_line(point=True, color='green') + base.mark_text(dy=-10).encode(text='Punti Totali:Q')).properties(height=350), use_container_width=True)

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
        st.dataframe(piv, use_container_width=True)

with t[3]: # ROSE
    if f_rs is not None:
        sq_list = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        sq = st.selectbox("Seleziona Squadra:", sq_list)
        df_sq = f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo']].sort_values('Prezzo', ascending=False)
        st.dataframe(df_sq.style.apply(style_rose, axis=1).format({"Prezzo": "{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 Gestione Vincoli")
        v1, v2 = st.columns([1, 2.5])
        with v1:
            deb = f_vn.groupby('Squadra')['Spesa Complessiva'].sum().reset_index().sort_values('Spesa Complessiva', ascending=False)
            st.dataframe(deb.style.background_gradient(subset=['Spesa Complessiva'], cmap='Oranges').format({"Spesa Complessiva": "{:g}"}), hide_index=True, use_container_width=True)
        with v2:
            sv = st.selectbox("Squadra:", sorted([x for x in f_vn['Squadra'].unique() if x != "SKIP"]), key="v_sel")
            det = f_vn[f_vn['Squadra'] == sv].dropna(subset=['Giocatore'])
            st.dataframe(det.style.background_gradient(subset=['Spesa Complessiva'], cmap='YlOrBr').format({c: "{:g}" for c in det.columns if c != 'Giocatore' and c != 'Squadra'}), hide_index=True, use_container_width=True)

with t[5]: # SIMULATORE SCAMBI
    st.subheader("🔄 Simulatore Scambi (Punto di Incontro)")
    if f_rs is not None:
        sq_l = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        c1, c2 = st.columns(2)
        
        with c1:
            s_a = st.selectbox("Squadra A:", sq_l, key="sa")
            g_a = st.selectbox("Cede:", f_rs[f_rs['Fantasquadra']==s_a]['Nome'], key="ga")
            v_a = f_rs[f_rs['Nome']==g_a]['Prezzo'].values[0]
            vn_a = f_vn[f_vn['Giocatore']==g_a]['Spesa Complessiva'].values[0] if (f_vn is not None and g_a in f_vn['Giocatore'].values) else 0.0
            vt_a = v_a + vn_a
            st.metric(f"Valore {g_a}", f"{vt_a:g}", help="Prezzo d'acquisto + Vincoli")

        with c2:
            s_b = st.selectbox("Squadra B:", [s for s in sq_l if s != s_a], key="sb")
            g_b = st.selectbox("Cede:", f_rs[f_rs['Fantasquadra']==s_b]['Nome'], key="gb")
            v_b = f_rs[f_rs['Nome']==g_b]['Prezzo'].values[0]
            vn_b = f_vn[f_vn['Giocatore']==g_b]['Spesa Complessiva'].values[0] if (f_vn is not None and g_b in f_vn['Giocatore'].values) else 0.0
            vt_b = v_b + vn_b
            st.metric(f"Valore {g_b}", f"{vt_b:g}", help="Prezzo d'acquisto + Vincoli")

        st.write("---")
        p_incontro = (vt_a + vt_b) / 2
        st.subheader(f"🤝 Punto di Incontro: {p_incontro:g} crediti")
        
        # Analisi Impatto
        st.write("**Anteprima Bilancio Post-Scambio:**")
        impatto = pd.DataFrame({
            "Squadra": [s_a, s_b],
            "Giocatore in Entrata": [g_b, g_a],
            "Nuovo Valore Rosa": [p_incontro, p_incontro],
            "Variazione Rispetto a Prima": [p_incontro - vt_a, p_incontro - vt_b]
        })
        st.dataframe(impatto.style.format({"Nuovo Valore Rosa": "{:g}", "Variazione Rispetto a Prima": "{:+g}"}), hide_index=True)
