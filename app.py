import streamlit as st
import pandas as pd
import os
import altair as alt

# 1. FORZATURA STILE E LAYOUT
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager - Versione Ripristinata")

# Mappature Squadre
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# Funzione di caricamento ultra-sicura
def load_safe(f):
    if not os.path.exists(f):
        return None
    try:
        # Salta le righe vuote e corregge l'errore del tuo file rose
        df = pd.read_csv(f, skip_blank_lines=True)
        if df.columns[0].startswith('Unnamed'):
            df = pd.read_csv(f, skiprows=1)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except:
        return None

# Caricamento file (ignoriamo volutamente quotazioni.csv per evitare blocchi)
f_pt = load_safe("classificapunti.csv")
f_rs = load_safe("rose_complete.csv")
f_vn = load_safe("vincoli.csv")

# Se non trova nemmeno le rose, avvisa l'utente
if f_rs is None and f_pt is None:
    st.error("⚠️ Non riesco a leggere i file CSV. Controlla che siano presenti su GitHub.")
else:
    t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli"])

    with t[0]: # CLASSIFICHE
        if f_pt is not None:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🎯 Classifica Punti")
                # Pulizia punti (toglie il punto delle migliaia e gestisce la virgola)
                f_pt['Punti Totali'] = f_pt['Punti Totali'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
                st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali']].sort_values('Posizione').style.background_gradient(subset=['Punti Totali'], cmap='Greens'), hide_index=True)
            with c2:
                st.subheader("📈 Trend")
                chart = alt.Chart(f_pt).mark_line(point=True, color='green').encode(
                    x=alt.X('Giocatore:N', sort='-y'),
                    y=alt.Y('Punti Totali:Q', scale=alt.Scale(domainMin=float(f_pt['Punti Totali'].min())-10))
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)

    with t[1]: # BUDGET
        if f_rs is not None:
            st.subheader("💰 Bilancio Crediti")
            f_rs['Prezzo'] = pd.to_numeric(f_rs['Prezzo'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            f_rs['Fantasquadra'] = f_rs['Fantasquadra'].str.upper().replace(map_n)
            bu = f_rs.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
            bu['Extra'] = bu['Fantasquadra'].map(bg_ex).fillna(0)
            bu['Totale Speso'] = bu['Prezzo'] + bu['Extra']
            st.dataframe(bu.sort_values('Totale Speso', ascending=False).style.background_gradient(subset=['Totale Speso'], cmap='YlOrRd'), hide_index=True)

    with t[2]: # ROSE COLORATE
        if f_rs is not None:
            sq = st.selectbox("Seleziona Squadra:", sorted(f_rs['Fantasquadra'].unique()))
            df_sq = f_rs[f_rs['Fantasquadra'] == sq].copy()
            
            def color_ruoli(row):
                r = str(row['Ruolo']).upper()
                bg = '#E3F2FD' if 'PORT' in r else '#E8F5E9' if 'DIF' in r else '#FFFDE7' if 'CEN' in r else '#FFEBEE' if 'ATT' in r else '#FFFFFF'
                return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
            
            st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo']].style.apply(color_ruoli, axis=1), hide_index=True, use_container_width=True)

    with t[3]: # VINCOLI
        if f_vn is not None:
            st.subheader("📅 Contratti in corso")
            st.dataframe(f_vn.style.set_properties(**{'font-weight': 'bold'}), hide_index=True)
