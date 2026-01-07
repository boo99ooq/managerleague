import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Lega Manager", layout="wide")
st.markdown("<style>.stApp{background-color:#f4f7f6;} .stTabs{background-color:white; border-radius:10px; padding:10px; shadow: 2px 2px 5px rgba(0,0,0,0.1);}</style>", unsafe_allow_html=True)
st.title("⚽ Centro Direzionale Fantalega")

# Configurazione Budget Extra
bg_extra = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

def load_data(name):
    for f in os.listdir("."):
        if f.lower() == name.lower():
            try:
                df = pd.read_csv(f, sep=None, engine='python', encoding='utf-8-sig').dropna(how='all')
                df.columns = df.columns.str.strip()
                return df
            except Exception as e:
                st.error(f"Errore caricamento {f}: {e}")
    return None

def style_df(df):
    return df.style.set_properties(**{'text-align': 'center'}).set_table_styles([dict(selector='th', props=[('text-align', 'center')])])

# Caricamento file
f_sc = load_data("scontridiretti.csv")
f_pt = load_data("classificapunti.csv")
f_rs = load_data("rose_complete.csv")
f_vn = load_data("vincoli.csv")

# Creazione Tab dinamiche
tabs_list = []
if f_sc is not None or f_pt is not None: tabs_list.append("🏆 Classifiche")
if f_rs is not None: tabs_list.extend(["💰 Budget", "🧠 Strategia", "🏃 Rose"])
if f_vn is not None: tabs_list.append("📅 Vincoli")

if tabs_list:
    t = st.tabs(tabs_list)
    idx = 0

    # --- TAB CLASSIFICHE ---
    if f_sc is not None or f_pt is not None:
        with t[idx]:
            c1, c2 = st.columns(2)
            if f_sc is not None:
                with c1:
                    st.subheader("🔥 Scontri Diretti")
                    st.dataframe(style_df(f_sc), hide_index=True, use_container_width=True)
            if f_pt is not None:
                with c2:
                    st.subheader("🎯 Classifica Punti")
                    st.dataframe(style_df(f_pt), hide_index=True, use_container_width=True)
        idx += 1

    # --- TAB BUDGET, STRATEGIA, ROSE ---
    if f_rs is not None:
