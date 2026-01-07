import streamlit as st
import pandas as pd
import os

# 1. SETUP E STILE
st.set_page_config(page_title="Lega", layout="wide")
st.markdown("<style>.stApp{background-color:#e8f5e9;} .stTabs, .stDataFrame{background-color:white; border-radius:10px; padding:5px;}</style>", unsafe_allow_html=True)

st.title("⚽ Centro Direzionale Fantalega")

# 2. BUDGET
budgets = {"GIANNI": 102.5, "DANI ROBI": 164.5, "MARCO": 131.0, "PIETRO": 101.5, "PIERLUIGI": 105.0, "GIGI": 232.5, "ANDREA": 139.0, "GIUSEPPE": 136.5, "MATTEO": 166.5, "NICHOLAS": 113.0}

# 3. FUNZIONI
def get_df(f):
    if os.path.exists(f):
        df = pd.read_csv(f, sep=',', encoding='utf-8-sig').dropna(how='all')
        df.columns = df.columns.str.strip()
        return df
    return None

def clean_n(df, c):
    if df is None or c not in df.columns: return df
    m = {"NICO FABIO": "NICHOLAS", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI", "MATTEO STEFANO": "MATTEO"}
    df[c] = df[c].astype(str).str.strip().str.upper().replace(m)
    return df

def style_c(df):
    # Allineamento centrale per celle e intestazioni
    return df.style.set_properties(**{'text-align': 'center'}).set_table_styles([dict(selector='th', props=[('text-align', 'center')])])

# 4. CARICAMENTO
f_sc = get_df("scontridiretti.csv")
f_pt = get_df("classificapunti.csv")
f_rs = get_df("rose_complete.csv")
f_vn = get_df("vincoli.csv")

# 5. APP
if any([f_sc is not None, f_pt is not None, f_rs is not None, f_vn is not None]):
    t = st.tabs(["🏆 Classifica", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

    with t[0]:
        c1, c2 = st.columns(2)
        if f_sc is not None:
            with c1: 
                st.write("🔥 **Scontri**")
                st.dataframe(style_c(clean_n(f_sc, 'Giocatore')), hide_index=True, use_container_width=True)
        if f_pt is not None:
            with c2:
                st.write("🎯 **Punti**")
                f_pt = clean_n(f_pt, 'Giocatore')
                for c in ['Punti Totali', 'Media']:
                    if c in f_pt.columns: f_pt[c] = f_pt[c].astype(str).str.replace(',','.').apply(pd.to_numeric, errors='coerce')
                st.dataframe(style_c(f_pt[['Posizione','Giocatore','Punti Totali','Media']]), hide_index=True, use_container_width=True)

    if f_rs is not None:
        f_rs.columns = [c.lower() for c in f_rs.columns]
        f_rs = clean_n(f_rs, 'fantasquadra')
        cp = next((c for c in f_rs.columns if 'prezzo' in c), 'prezzo')
        f_rs[cp] = pd.to_numeric(f_rs[cp], errors='coerce').fillna(0).astype(int)

        with t[1]:
            st.write("💰 **Bilancio**")
            eco = f_rs.groupby('fantasquadra')[cp].sum().reset_index()
            eco['Extra'] = eco['fantasquadra'].map(budgets).fillna(0)
            eco['Totale'] = (eco[cp] + eco['Extra']).astype(int)
            st.dataframe(style_c(eco.sort_values('Totale', ascending=False)), hide_index=True, use_container_width=True)

        with t[2]:
            st.write("🧠 **Strategia**")
            cx, cy = st.columns([1.5, 1])
            cr = next((c for c in f_
