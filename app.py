import streamlit as st
import pandas as pd
import os
import altair as alt

# 1. SETUP UI E STILE (GOLDEN UI)
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
map_r = {"P": "PORTIERE", "D": "DIFENSORE", "C": "CENTROCAMPISTA", "A": "ATTACCANTE"}

# --- UTILITY DI PULIZIA ---
def cv(v):
    if pd.isna(v) or str(v).strip() == "": return 0.0
    try:
        s = str(v).replace('"', '').replace('.', '').replace(',', '.').strip()
        return float(s)
    except: return 0.0

def clean_s(s):
    return str(s).strip().upper() if not pd.isna(s) else ""

def ld(f):
    if not os.path.exists(f): return None
    try:
        # Legge saltando le righe vuote
        df = pd.read_csv(f, skip_blank_lines=True, engine='python')
        # Gestione riga vuota iniziale (tipica del tuo file rose)
        if df.columns[0].startswith('Unnamed') or len(df.columns) < 2:
            df = pd.read_csv(f, skiprows=1, engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# --- CARICAMENTO DATI ---
f_rs = ld("rose_complete.csv")
f_pt = ld("classificapunti.csv")
f_vn = ld("vincoli.csv")
f_qt = ld("quotazioni.csv")

# --- ELABORAZIONE DATI (PROTEZIONE DAI CRASH) ---
if f_rs is not None:
    # Verifichiamo che esistano le colonne necessarie, altrimenti le creiamo
    if 'Prezzo' not in f_rs.columns: f_rs['Prezzo'] = 0.0
    
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)
    f_rs['Ruolo_C'] = f_rs['Ruolo'].apply(lambda x: map_r.get(clean_s(x)[0], clean_s(x)))
    f_rs['Squadra_C'] = f_rs['Fantasquadra'].apply(clean_s).replace(map_n)
    
    # Se esiste il file quotazioni, proviamo il merge
    if f_qt is not None:
        f_qt['Nome_Match'] = f_qt['Nome'].apply(clean_s)
        f_qt['Ruolo_QT'] = f_qt['R'].map(map_r)
        f_qt['Quotazione'] = f_qt['Qt.A'].apply(cv)
        
        f_rs['Nome_Match'] = f_rs['Nome'].apply(clean_s)
        f_rs = pd.merge(f_rs, f_qt[['Nome_Match', 'Ruolo_QT', 'Quotazione']], 
                        left_on=['Nome_Match', 'Ruolo_C'], right_on=['Nome_Match', 'Ruolo_QT'], 
                        how='left').drop(['Nome_Match', 'Ruolo_QT'], axis=1)
    
    # Protezione finale: se Quotazione non esiste dopo il merge, la creiamo a 0
    if 'Quotazione' not in f_rs.columns: f_rs['Quotazione'] = 0.0
    f_rs['Quotazione'] = f_rs['Quotazione'].fillna(0)
    f_rs['Plusvalenza'] = f_rs['Quotazione'] - f_rs['Prezzo']

# --- INTERFACCIA A TAB ---
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

with t[0]: # CLASSIFICA CON GRAFICO
    if f_pt is not None:
        f_pt['Punti_N'] = f_pt['Punti Totali'].apply(cv)
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🎯 Punti")
            st.dataframe(f_pt[['Posizione','Giocatore','Punti_N']].sort_values('Posizione').style.background_gradient(subset=['Punti_N'], cmap='Greens'), hide_index=True)
        with c2:
            chart = alt.Chart(f_pt).mark_line(point=True, color='green').encode(
                x=alt.X('Giocatore:N', sort='-y'), y=alt.Y('Punti_N:Q', scale=alt.Scale(domainMin=f_pt['Punti_N'].min()-10))
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)

with t[1]: # BUDGET (RISOLTO KEYERROR)
    if f_rs is not None:
        st.subheader("💰 Bilancio e Patrimonio")
        # Raggruppiamo solo le colonne che esistono sicuramente
        eco = f_rs.groupby('Squadra_C').agg({'Prezzo': 'sum', 'Quotazione': 'sum'}).reset_index()
        eco.columns = ['Squadra', 'Spesa Rosa', 'Valore Mercato']
        eco['Extra'] = eco['Squadra'].map(bg_ex).fillna(0)
        eco['Patrimonio'] = eco['Valore Mercato'] + eco['Extra']
        
        st.dataframe(eco.sort_values('Patrimonio', ascending=False).style.background_gradient(subset=['Valore Mercato'], cmap='YlGn').format({c: "{:g}" for c in eco.columns if c != 'Squadra'}), hide_index=True, use_container_width=True)

with t[3]: # ROSE COLORATE
    if f_rs is not None:
        sq = st.selectbox("Seleziona Squadra:", sorted(f_rs['Squadra_C'].unique()))
        df_sq = f_rs[f_rs['Squadra_C'] == sq].copy()
        
        def style_r(row):
            bg = {'PORTIERE':'#E3F2FD','DIFENSORE':'#E8F5E9','CENTROCAMPISTA':'#FFFDE7','ATTACCANTE':'#FFEBEE'}.get(row['Ruolo_C'], '#FFFFFF')
            return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
        
        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo', 'Quotazione', 'Plusvalenza']].style.apply(style_r, axis=1).background_gradient(subset=['Plusvalenza'], cmap='RdYlGn').format({"Prezzo":"{:g}","Quotazione":"{:g}","Plusvalenza":"{:+g}"}), hide_index=True, use_container_width=True)
