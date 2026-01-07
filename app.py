import streamlit as st
import pandas as pd
import os
import altair as alt

# 1. SETUP UI E STILE
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

# Mappature Squadre e Budget Extra
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- FUNZIONI DI PULIZIA ---
def clean_val(v):
    if pd.isna(v) or str(v).strip() == "": return 0.0
    try:
        s = str(v).replace('"', '').replace('.', '').replace(',', '.').strip()
        return float(s)
    except: return 0.0

def clean_string_safe(s):
    """Trasforma qualsiasi valore in stringa pulita per evitare AttributeError"""
    if pd.isna(s): return ""
    return str(s).strip().upper()

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, skip_blank_lines=True)
        if df.columns[0].startswith('Unnamed'):
            df = pd.read_csv(f, skiprows=1)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# 2. CARICAMENTO DATI
f_pt = ld("classificapunti.csv")
f_rs = ld("rose_complete.csv")
f_vn = ld("vincoli.csv")

# 3. INTERFACCIA A SCHEDE
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

# --- TAB CLASSIFICHE ---
with t[0]:
    if f_pt is not None:
        f_pt['Punti_N'] = f_pt['Punti Totali'].apply(clean_val)
        c1, c2 = st.columns(2)
        with c1:
            st.dataframe(f_pt[['Posizione','Giocatore','Punti_N']].sort_values('Posizione').style.background_gradient(subset=['Punti_N'], cmap='Greens'), hide_index=True)
        with c2:
            chart = alt.Chart(f_pt).mark_line(point=True, color='green').encode(
                x=alt.X('Giocatore:N', sort='-y'),
                y=alt.Y('Punti_N:Q', scale=alt.Scale(domainMin=float(f_pt['Punti_N'].min())-5))
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)

# --- TAB BUDGET (RISOLTO ATTRIBUTEERROR) ---
with t[1]:
    if f_rs is not None:
        st.subheader("💰 Bilancio")
        # Pulizia forzata: prima trasformiamo in stringa, poi facciamo upper e replace
        f_rs['Sq_C'] = f_rs['Fantasquadra'].apply(clean_string_safe).replace(map_n)
        f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(clean_val)
        
        bu = f_rs.groupby('Sq_C')['Prezzo_N'].sum().reset_index()
        bu.columns = ['Squadra', 'Spesa_Rosa']
        bu['Extra'] = bu['Squadra'].map(bg_ex).fillna(0)
        bu['Totale'] = bu['Spesa_Rosa'] + bu['Extra']
        
        st.dataframe(bu.sort_values('Totale', ascending=False).style.background_gradient(subset=['Totale'], cmap='YlOrRd'), hide_index=True)

# --- TAB ROSE ---
with t[2]:
    if f_rs is not None:
        sq_list = sorted(f_rs['Sq_C'].unique())
        s_sel = st.selectbox("Seleziona Squadra:", [s for s in sq_list if s != ""])
        df_sq = f_rs[f_rs['Sq_C'] == s_sel].copy()
        
        def color_ruoli(row):
            r = str(row['Ruolo']).upper()
            bg = '#E3F2FD' if 'PORT' in r else '#E8F5E9' if 'DIF' in r else '#FFFDE7' if 'CEN' in r else '#FFEBEE' if 'ATT' in r else '#FFFFFF'
            return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
        
        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo_N']].style.apply(color_ruoli, axis=1), hide_index=True, use_container_width=True)

# --- TAB VINCOLI ---
with t[3]:
    if f_vn is not None:
        st.dataframe(f_vn, hide_index=True)

# --- TAB SCAMBI ---
with t[4]:
    st.subheader("🔄 Simulatore Scambi")
    st.info("Ripristino della logica di base per garantire stabilità.")
