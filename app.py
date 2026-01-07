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

# Mappature e Budget Extra
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- UTILITY ---
def clean_val(v):
    if pd.isna(v) or str(v).strip() == "": return 0.0
    try:
        s = str(v).replace('"', '').replace('.', '').replace(',', '.').strip()
        return float(s)
    except: return 0.0

def safe_format(df):
    """Formatta solo le colonne numeriche esistenti nel DataFrame per evitare ValueError"""
    fmt_dict = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            fmt_dict[col] = "{:g}"
    return fmt_dict

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

# 3. INTERFACCIA TABS
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli"])

with t[0]: # CLASSIFICHE
    if f_pt is not None:
        f_pt['Punti_N'] = f_pt['Punti Totali'].apply(clean_val)
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🎯 Classifica")
            st.dataframe(f_pt[['Posizione','Giocatore','Punti_N']].sort_values('Posizione').style.background_gradient(subset=['Punti_N'], cmap='Greens'), hide_index=True)
        with c2:
            st.subheader("📈 Trend")
            chart = alt.Chart(f_pt).mark_line(point=True, color='green').encode(
                x=alt.X('Giocatore:N', sort='-y'),
                y=alt.Y('Punti_N:Q', scale=alt.Scale(domainMin=float(f_pt['Punti_N'].min())-5))
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)

with t[1]: # BUDGET (RISOLTO VALUEERROR)
    if f_rs is not None:
        st.subheader("💰 Bilancio")
        f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(clean_val)
        f_rs['Sq_C'] = f_rs['Fantasquadra'].str.upper().strip().replace(map_n)
        
        bu = f_rs.groupby('Sq_C')['Prezzo_N'].sum().reset_index()
        bu.columns = ['Squadra', 'Spesa_Rosa']
        bu['Extra'] = bu['Squadra'].map(bg_ex).fillna(0)
        bu['Patrimonio'] = bu['Spesa_Rosa'] + bu['Extra']
        
        # Formattazione sicura
        st.dataframe(
            bu.sort_values('Patrimonio', ascending=False)
            .style.background_gradient(subset=['Patrimonio'], cmap='YlOrRd')
            .format(safe_format(bu)), 
            hide_index=True, use_container_width=True
        )

with t[2]: # ROSE
    if f_rs is not None:
        sq = st.selectbox("Seleziona Squadra:", sorted(f_rs['Sq_C'].unique()))
        df_sq = f_rs[f_rs['Sq_C'] == sq].copy()
        
        def style_r(row):
            r = str(row['Ruolo']).upper()
            bg = '#E3F2FD' if 'PORT' in r else '#E8F5E9' if 'DIF' in r else '#FFFDE7' if 'CEN' in r else '#FFEBEE' if 'ATT' in r else '#FFFFFF'
            return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
        
        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo_N']].style.apply(style_r, axis=1).format({"Prezzo_N": "{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 Vincoli")
        st.dataframe(f_vn, hide_index=True)
