import streamlit as st
import pandas as pd
import os

# 1. SETUP
st.set_page_config(page_title="Lega Manager", layout="wide")
st.markdown("<style>.stApp{background-color:#f4f7f6;} .stTabs{background-color:white; border-radius:10px; padding:10px;}</style>", unsafe_allow_html=True)
st.title("⚽ Centro Direzionale Fantalega")

bg_extra = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

# 2. FUNZIONE CARICAMENTO
def load_data(name):
    actual_file = next((f for f in os.listdir(".") if f.lower() == name.lower()), None)
    if actual_file:
        try:
            # Prova vari separatori
            df = pd.read_csv(actual_file, sep=None, engine='python', encoding='utf-8-sig').dropna(how='all')
            df.columns = df.columns.str.strip()
            return df
        except: return None
    return None

def style_df(obj):
    # Se è già uno Styler (colorato), aggiunge solo la centratura. Altrimenti crea lo Styler.
    styler = obj if hasattr(obj, 'render') else obj.style
    return styler.set_properties(**{'text-align': 'center'}).set_table_styles([dict(selector='th', props=[('text-align', 'center')])])

# 3. LETTURA FILE
f_sc, f_pt, f_rs, f_vn = load_data("scontridiretti.csv"), load_data("classificapunti.csv"), load_data("rose_complete.csv"), load_data("vincoli.csv")

# Sidebar di controllo
st.sidebar.header("🔍 Stato File")
st.sidebar.write("Scontri:", "✅" if f_sc is not None else "❌")
st.sidebar.write("Punti:", "✅" if f_pt is not None else "❌")
st.sidebar.write("Rose:", "✅" if f_rs is not None else "❌")
st.sidebar.write("Vincoli:", "✅" if f_vn is not None else "❌")

# 4. TAB
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_sc is not None:
        with c1: st.subheader("🔥 Scontri"); st.dataframe(style_df(f_sc), hide_index=True)
    if f_pt is not None:
        with c2: st.subheader("🎯 Punti"); st.dataframe(style_df(f_pt), hide_index=True)

if f_rs is not None:
    c = f_rs.columns
    # Pulizia prezzo (ultima colonna)
    f_rs[c[-1]] = pd.to_numeric(f_rs[c[-1]].astype(str).str.replace(',','.').str.extract('(\d+)')[0], errors='coerce').fillna(0)
    
    with t[1]: # BUDGET
        st.subheader("💰 Bilancio Crediti")
        eco = f_rs.groupby(c[0])[c[-1]].sum().reset_index()
        eco['Extra'] = eco[c[0]].str.upper().map(bg_extra).fillna(0)
        eco['Totale'] = (eco[c[-1]] + eco['Extra']).astype(int)
        st.dataframe(style_df(eco.sort_values('Totale', ascending=False)), hide_index=True)
    
    with t[2]: # STRATEGIA
        st.subheader("🧠 Distribuzione Ruoli")
        f_rs[c[2]] = f_rs[c[2]].replace({'P':'Portiere','D':'Difensore','C':'Centrocampista','A':'Attaccante'})
        piv = f_rs.pivot_table(index=c[0], columns=c[2], values=c[1], aggfunc='count').fillna(0).astype(int)
        st.dataframe(style_df(piv))

    with t[3]: # ROSE
        sq = st.selectbox("Squadra:", sorted(f_rs[c[0]].unique()))
        df_sq = f_rs[f_rs[c[0]] == sq][[c[2], c[1], c[-1]]].sort_values(c[-1], ascending=False)
        # APPLICAZIONE CORRETTA: Prima il gradiente, poi la centratura tramite style_df
        st_color = df_sq.style.background_gradient(subset=[c[-1]], cmap='Greens')
        st.dataframe(style_df(st_color), hide_index=True)

if f_vn is not None:
    with t[4]: # VINCOLI
        v = f_vn.columns
        f_vn[v[2]] = pd.to_numeric(f_vn[v[2]].astype(str).str.replace(',','.').str.extract('(\d+)')[0], errors='coerce').fillna(0)
        v1, v2 = st.columns([1, 2])
        with v1:
            st.write
