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

def style_rose(row):
    colors = {'Portiere':'#E3F2FD','Difensore':'#E8F5E9','Centrocampista':'#FFFDE7','Attaccante':'#FFEBEE','Giovani':'#F3E5F5'}
    return [f'background-color: {colors.get(row["Ruolo"], "#FFFFFF")}; color: black; font-weight: bold;'] * len(row)

t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

with t[0]: # CLASSIFICHE + GRAFICO ZOOM
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

if f_rs is not None:
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)
    with t[1]: # BUDGET + GRAFICO BILANCIO
        st.subheader("💰 Bilancio Globale")
        eco = f_rs.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        eco.columns = ['Fantasquadra', 'Valore Rosa']
        eco['Crediti Disponibili'] = eco['Fantasquadra'].map(bg_ex).fillna(0)
        if f_vn is not None:
            c26 = f_vn['Costo 2026-27'].apply(cv); c27 = f_vn.get('Costo 2027-28', pd.Series(0.0, index=f_vn.index)).apply(cv); c28 = f_vn.get('Costo 2028-29', pd.Series(0.0, index=f_vn.index)).apply(cv)
            f_vn['Vincolo Totale'] = c26 + c27 + c28
            v_sum = f_vn.groupby('Squadra')['Vincolo Totale'].sum().reset_index()
            v_sum.columns = ['Fantasquadra', 'Vincoli']
            eco = pd.merge(eco, v_sum, on='Fantasquadra', how='left').fillna(0)
        else: eco['Vincoli'] = 0
        eco['Totale'] = eco['Valore Rosa'] + eco['Crediti Disponibili'] + eco['Vincoli']
        st.dataframe(eco.sort_values('Totale', ascending=False).style.background_gradient(subset=['Valore Rosa'], cmap='YlOrRd').background_gradient(subset=['Crediti Disponibili'], cmap='GnBu').background_gradient(subset=['Vincoli'], cmap='Purples').background_gradient(subset=['Totale'], cmap='YlGn').format({"Valore Rosa": "{:g}", "Crediti Disponibili": "{:g}", "Vincoli": "{:g}", "Totale": "{:g}"}), hide_index=True, use_container_width=True)
        st.write("---")
        eco_melt = eco.melt(id_vars='Fantasquadra', value_vars=['Valore Rosa', 'Crediti Disponibili', 'Vincoli'])
        chart_b = alt.Chart(eco_melt).mark_bar().encode(x='sum(value):Q', y=alt.Y('Fantasquadra:N', sort='-x'), color=alt.Color('variable:N', scale=alt.Scale(range=['#ff9e9e', '#9ecbff', '#d19eff'])))
        st.altair_chart(chart_b.properties(height=400), use_container_width=True)

    with t[2]: # STRATEGIA + GRAFICO RUOLI
        st.subheader("🧠 Bilanciamento Squadre")
        piv = f_rs.pivot_table(index='Fantasquadra', columns='Ruolo', values='Nome', aggfunc='count').fillna(0).astype(int)
        st.dataframe(piv, use_container_width=True)
        st.write("---")
        piv_melt = piv.reset_index().melt(id_vars='Fantasquadra')
        chart_r = alt.Chart(piv_melt).mark_bar().encode(x='Fantasquadra:N', y='value:Q', color='Ruolo:N', column='Ruolo:N')
        st.altair_chart(chart_r.properties(width=150, height=200))

    with t[3]: # ROSE
        sq = st.selectbox("Squadra:", sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"]))
        df_sq = f_rs[f_rs['Fantasquadra'] == sq][['Ruolo', 'Nome', 'Prezzo']].sort_values('Prezzo', ascending=False)
        st.dataframe(df_sq.style.apply(style_rose, axis=1).format({"Prezzo": "{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # VINCOLI
    st.subheader("📅 Gestione Vincoli")
    if f_vn is not None:
        for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29', 'Durata (anni)']: f_vn[c] = f_vn[c].apply(cv) if c in f_vn.columns else 0.0
        f_vn['Spesa Complessiva'] = f_vn['Costo 2026-27'] + f_vn.get('Costo 2027-28', 0) + f_vn.get('Costo 2028-29', 0)
        v1, v2 = st.columns([1, 2.5])
        with v1:
            deb = f_vn.groupby('Squadra')['Spesa Complessiva'].sum().reset_index().sort_values('Spesa Complessiva', ascending=False)
            st.dataframe(deb.style.background_gradient(subset=['Spesa Complessiva'], cmap='Oranges').format({"Spesa Complessiva": "{:g}"}), hide_index=True, use_container_width=True)
        with v2:
            sv = st.selectbox("Squadra:", sorted([x for x in f_vn['Squadra'].unique() if x != "SKIP"]), key="v_sel")
            det = f_vn[f_vn['Squadra'] == sv].dropna(subset=['Giocatore'])
            st.dataframe(det.style.background_gradient(subset=['Spesa Complessiva'], cmap='YlOrBr').format({c: "{:g}" for c in det.columns if c != 'Giocatore' and c != 'Squadra'}), hide_index=True, use_container_width=True)
