import streamlit as st
import pandas as pd
import os
import altair as alt

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("<style>.stApp { background-color: white; } div[data-testid='stDataFrame'] * { color: #1a1a1a !important; font-weight: bold !important; }</style>", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager - Versione Ripristinata")

# Mappature fisse
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- FUNZIONI DI CARICAMENTO ROBUSTE ---
def clean_num(val):
    """Converte stringhe come '1.074,5' in float 1074.5"""
    if pd.isna(val) or val == "": return 0.0
    s = str(val).replace('"', '').strip()
    # Se c'è sia il punto che la virgola (es 1.074,5)
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try: return float(s)
    except: return 0.0

def load_csv_safe(filename):
    if not os.path.exists(filename): return None
    try:
        # Legge il file ignorando le righe vuote
        df = pd.read_csv(filename, skip_blank_lines=True, engine='python')
        # Se la prima colonna è "Unnamed", significa che c'è una riga vuota all'inizio (come nel tuo file rose)
        if df.columns[0].startswith('Unnamed'):
            df = pd.read_csv(filename, skiprows=1, engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except:
        return None

# --- CARICAMENTO DATI ---
f_pt = load_csv_safe("classificapunti.csv")
f_rs = load_csv_safe("rose_complete.csv")
f_vn = load_csv_safe("vincoli.csv")

# Creazione Tab
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

# --- TAB 0: CLASSIFICHE ---
with t[0]:
    if f_pt is not None:
        st.subheader("🎯 Classifica Generale")
        f_pt['Punti_N'] = f_pt['Punti Totali'].apply(clean_num)
        c1, c2 = st.columns(2)
        with c1:
            st.dataframe(f_pt[['Posizione','Giocatore','Punti_N']].sort_values('Posizione').style.background_gradient(subset=['Punti_N'], cmap='Greens'), hide_index=True)
        with c2:
            chart = alt.Chart(f_pt).mark_line(point=True, color='green').encode(
                x=alt.X('Giocatore:N', sort='-y'),
                y=alt.Y('Punti_N:Q', scale=alt.Scale(domainMin=float(f_pt['Punti_N'].min())-10))
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)
    else:
        st.error("File 'classificapunti.csv' non trovato o vuoto.")

# --- TAB 1: BUDGET ---
with t[1]:
    if f_rs is not None:
        st.subheader("💰 Bilancio")
        f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(clean_num)
        f_rs['Squadra_N'] = f_rs['Fantasquadra'].str.upper().replace(map_n)
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index()
        bu['Extra'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['Totale'] = bu['Prezzo_N'] + bu['Extra']
        st.dataframe(bu.sort_values('Totale', ascending=False).style.background_gradient(subset=['Totale'], cmap='YlOrRd'), hide_index=True)
    else:
        st.error("File 'rose_complete.csv' non trovato o vuoto.")

# --- TAB 2: ROSE ---
with t[2]:
    if f_rs is not None:
        sq_list = sorted(f_rs['Squadra_N'].unique())
        s_sel = st.selectbox("Seleziona Squadra:", sq_list)
        df_sq = f_rs[f_rs['Squadra_N'] == s_sel].copy()
        
        def color_ruoli(row):
            r = str(row['Ruolo']).upper()
            bg = '#E3F2FD' if 'PORT' in r else '#E8F5E9' if 'DIF' in r else '#FFFDE7' if 'CEN' in r else '#FFEBEE' if 'ATT' in r else '#FFFFFF'
            return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
        
        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo']].style.apply(color_ruoli, axis=1), hide_index=True, use_container_width=True)

# --- TAB 3: VINCOLI ---
with t[3]:
    if f_vn is not None:
        st.subheader("📅 Contratti")
        st.dataframe(f_vn, hide_index=True)

# --- TAB 4: SCAMBI ---
with t[4]:
    st.subheader("🔄 Simulatore Scambi")
    st.write("Seleziona i giocatori per simulare lo scambio.")
