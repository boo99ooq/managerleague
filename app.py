import streamlit as st
import pandas as pd
import os
import altair as alt

# 1. SETUP UI ORIGINALE
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

# --- FUNZIONI DI CARICAMENTO STABILI ---
def cv(v):
    if pd.isna(v): return 0.0
    try:
        return float(str(v).replace('"', '').replace(',', '.').strip())
    except: return 0.0

def ld(f):
    if not os.path.exists(f): return None
    try:
        # Questa riga risolve il problema della riga vuota iniziale
        df = pd.read_csv(f, sep=',', engine='python', skip_blank_lines=True)
        if df.columns[0].startswith('Unnamed'):
            df = pd.read_csv(f, sep=',', engine='python', skiprows=1)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# 2. CARICAMENTO DATI
f_sc = ld("scontridiretti.csv")
f_pt = ld("classificapunti.csv")
f_rs = ld("rose_complete.csv")
f_vn = ld("vincoli.csv")

# 3. INTERFACCIA A TABS (COME ORIGINALE)
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli"])

with t[0]: # CLASSIFICHE E GRAFICO ZOOM
    if f_pt is not None:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("🎯 Classifica Punti")
            f_pt['Punti Totali'] = f_pt['Punti Totali'].apply(lambda x: cv(str(x).replace('.', '')))
            st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali']].sort_values('Posizione').style.background_gradient(subset=['Punti Totali'], cmap='Greens'), hide_index=True, use_container_width=True)
        
        with c2:
            st.subheader("📈 Trend")
            p_min = f_pt['Punti Totali'].min() - 5
            chart = alt.Chart(f_pt).mark_line(point=True, color='green').encode(
                x=alt.X('Giocatore:N', sort='-y'),
                y=alt.Y('Punti Totali:Q', scale=alt.Scale(domainMin=p_min))
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)

with t[1]: # BUDGET E BAR CHART
    if f_rs is not None:
        st.subheader("💰 Situazione Crediti")
        f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)
        f_rs['Fantasquadra'] = f_rs['Fantasquadra'].str.upper().replace(map_n)
        
        bu = f_rs.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        bu['Extra'] = bu['Fantasquadra'].map(bg_ex).fillna(0)
        bu['Totale Speso'] = bu['Prezzo'] + bu['Extra']
        
        st.dataframe(bu.sort_values('Totale Speso', ascending=False).style.background_gradient(subset=['Totale Speso'], cmap='YlOrRd'), hide_index=True, use_container_width=True)
        
        # Grafico a barre
        st.altair_chart(alt.Chart(bu).mark_bar().encode(
            x=alt.X('Totale Speso:Q'),
            y=alt.Y('Fantasquadra:N', sort='-x'),
            color=alt.value('orange')
        ).properties(height=400), use_container_width=True)

with t[2]: # ROSE COLORATE
    if f_rs is not None:
        lista_sq = sorted(f_rs['Fantasquadra'].unique())
        sq = st.selectbox("Seleziona Squadra:", lista_sq)
        
        df_sq = f_rs[f_rs['Fantasquadra'] == sq].copy()
        
        def color_ruoli(row):
            r = str(row['Ruolo']).upper()
            if 'PORTIERE' in r: color = '#E3F2FD'
            elif 'DIFENSORE' in r: color = '#E8F5E9'
            elif 'CENTROCAMPISTA' in r: color = '#FFFDE7'
            elif 'ATTACCANTE' in r: color = '#FFEBEE'
            else: color = '#FFFFFF'
            return [f'background-color: {color}; color: black; font-weight: bold;'] * len(row)

        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo']].style.apply(color_ruoli, axis=1), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 Contratti e Vincoli")
        st.dataframe(f_vn.style.set_properties(**{'font-weight': 'bold'}), hide_index=True, use_container_width=True)
