import streamlit as st
import pandas as pd
import os
import altair as alt

# 1. SETUP UI GOLDEN ORIGINALE
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
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

def cv(v):
    if pd.isna(v): return 0.0
    try:
        return float(str(v).replace('"', '').replace(',', '.').strip())
    except: return 0.0

def ld(f):
    if not os.path.exists(f): return None
    try:
        # Legge saltando la riga vuota iniziale tipica del tuo file rose
        df = pd.read_csv(f, sep=',', engine='python', skip_blank_lines=True)
        if df.columns[0].startswith('Unnamed'):
            df = pd.read_csv(f, sep=',', engine='python', skiprows=1)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# 2. CARICAMENTO DATI (ESCLUDIAMO VOLUTAMENTE QUOTAZIONI.CSV)
f_pt = ld("classificapunti.csv")
f_rs = ld("rose_complete.csv")
f_vn = ld("vincoli.csv")

# 3. INTERFACCIA A TABS
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli"])

with t[0]: # CLASSIFICHE
    if f_pt is not None:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🎯 Classifica Punti")
            f_pt['Punti Totali'] = f_pt['Punti Totali'].apply(lambda x: cv(str(x).replace('.', '')))
            st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali']].sort_values('Posizione').style.background_gradient(subset=['Punti Totali'], cmap='Greens'), hide_index=True)
        with c2:
            st.subheader("📈 Grafico")
            chart = alt.Chart(f_pt).mark_line(point=True, color='green').encode(
                x=alt.X('Giocatore:N', sort='-y'),
                y=alt.Y('Punti Totali:Q', scale=alt.Scale(domainMin=f_pt['Punti Totali'].min()-5))
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        st.subheader("💰 Bilancio")
        f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)
        f_rs['Fantasquadra'] = f_rs['Fantasquadra'].str.upper().replace(map_n)
        bu = f_rs.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        bu['Extra'] = bu['Fantasquadra'].map(bg_ex).fillna(0)
        bu['Totale'] = bu['Prezzo'] + bu['Extra']
        st.dataframe(bu.sort_values('Totale', ascending=False).style.background_gradient(subset=['Totale'], cmap='YlOrRd'), hide_index=True)

with t[2]: # ROSE
    if f_rs is not None:
        sq = st.selectbox("Squadra:", sorted(f_rs['Fantasquadra'].unique()))
        df_sq = f_rs[f_rs['Fantasquadra'] == sq].copy()
        def color_ruoli(row):
            r = str(row['Ruolo']).upper()
            bg = '#E3F2FD' if 'PORTIERE' in r else '#E8F5E9' if 'DIFENSORE' in r else '#FFFDE7' if 'CENTROCAMPISTA' in r else '#FFEBEE' if 'ATTACCANTE' in r else '#FFFFFF'
            return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo']].style.apply(color_ruoli, axis=1), hide_index=True)

with t[3]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 Vincoli")
        st.dataframe(f_vn.style.set_properties(**{'font-weight': 'bold'}), hide_index=True)
