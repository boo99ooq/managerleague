import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Lega Manager", layout="wide")
st.markdown("<style>.stApp{background-color:#f4f7f6;} .stTabs{background-color:white; border-radius:10px; padding:10px;}</style>", unsafe_allow_html=True)
st.title("⚽ Centro Direzionale Fantalega")

# Configurazione Budget Extra originale
bg_extra = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

def load_data(name):
    for f in os.listdir("."):
        if f.lower() == name.lower():
            try:
                # Lettura con auto-rilevamento separatore (virgola o punto e virgola)
                df = pd.read_csv(f, sep=None, engine='python', encoding='utf-8-sig').dropna(how='all')
                df.columns = df.columns.str.strip()
                return df
            except:
                return None
    return None

def style_df(df):
    return df.style.set_properties(**{'text-align': 'center'}).set_table_styles([dict(selector='th', props=[('text-align', 'center')])])

# Caricamento file
f_sc = load_data("scontridiretti.csv")
f_pt = load_data("classificapunti.csv")
f_rs = load_data("rose_complete.csv")
f_vn = load_data("vincoli.csv")

# Creazione Tab
tabs_list = []
if f_sc is not None or f_pt is not None: tabs_list.append("🏆 Classifiche")
if f_rs is not None: tabs_list.extend(["💰 Budget", "🧠 Strategia", "🏃 Rose"])
if f_vn is not None: tabs_list.append("📅 Vincoli")

if tabs_list:
    t = st.tabs(tabs_list)
    idx = 0

    # --- CLASSIFICHE ---
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

    # --- ROSE E BUDGET ---
    if f_rs is not None:
        cols = f_rs.columns
        sq_col, nom_col, r_col, prz_col = cols[0], cols[1], cols[2], cols[-1]
        f_rs[prz_col] = pd.to_numeric(f_rs[prz_col].astype(str).str.replace(',','.'), errors='coerce').fillna(0)

        with t[idx]: # Budget
            st.subheader("💰 Bilancio Crediti")
            spesa = f_rs.groupby(sq_col)[prz_col].sum().reset_index()
            spesa['Extra'] = spesa[sq_col].str.upper().map(bg_extra).fillna(0)
            spesa['Totale'] = (spesa[prz_col] + spesa['Extra']).astype(int)
            st.dataframe(style_df(spesa.sort_values('Totale', ascending=False)), hide_index=True, use_container_width=True)
        
        with t[idx+1]: # Strategia
            st.subheader("🧠 Distribuzione Ruoli")
            pivot = f_rs.pivot_table(index=sq_col, columns=r_col, values=nom_col, aggfunc='count').fillna(0).astype(int)
            st.dataframe(style_df(pivot), use_container_width=True)

        with t[idx+2]: # Rose
            st.subheader("🏃 Rose Squadre")
            sel_sq = st.selectbox("Scegli Squadra:", sorted(f_rs[sq_col].unique()))
            rosa = f_rs[f_rs[sq_col] == sel_sq][[r_col, nom_col, prz_col]].sort_values(prz_col, ascending=False)
            st.dataframe(style_df(rosa.style.background_gradient(subset=[prz_col], cmap='Greens')), hide_index=True, use_container_width=True)
        idx += 3

    # --- VINCOLI ---
    if f_vn is not None:
        with t[idx]:
            st.subheader("📅 Gestione Vincoli")
            v_cols = f_vn.columns
            v_sq, v_nom, v_costo
