import streamlit as st
import pandas as pd
import os

# 1. SETUP
st.set_page_config(page_title="Lega Manager", layout="wide")
st.markdown("<style>.stApp{background-color:#f4f7f6;} .stTabs{background-color:white; border-radius:10px; padding:10px;}</style>", unsafe_allow_html=True)
st.title("⚽ Centro Direzionale Fantalega")

bg_extra = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

# 2. FUNZIONE CARICAMENTO SUPER ROBUSTA
def load_data(name):
    actual_file = None
    for f in os.listdir("."):
        if f.lower() == name.lower():
            actual_file = f
            break
    
    if actual_file:
        try:
            # Prova prima con virgola, poi con punto e virgola
            try:
                df = pd.read_csv(actual_file, sep=',', encoding='utf-8-sig')
            except:
                df = pd.read_csv(actual_file, sep=';', encoding='utf-8-sig')
            
            df = df.dropna(how='all')
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            st.sidebar.error(f"Errore tecnico in {name}: {e}")
            return None
    return None

def style_df(df):
    return df.style.set_properties(**{'text-align': 'center'}).set_table_styles([dict(selector='th', props=[('text-align', 'center')])])

# 3. LETTURA FILE
f_sc = load_data("scontridiretti.csv")
f_pt = load_data("classificapunti.csv")
f_rs = load_data("rose_complete.csv")
f_vn = load_data("vincoli.csv")

# Monitoraggio sidebar
st.sidebar.header("🔍 Stato File")
st.sidebar.write("Scontri:", "✅" if f_sc is not None else "❌")
st.sidebar.write("Punti:", "✅" if f_pt is not None else "❌")
st.sidebar.write("Rose:", "✅" if f_rs is not None else "❌")
st.sidebar.write("Vincoli:", "✅" if f_vn is not None else "❌")

# 4. LOGICA TAB
# Se un file non esiste, creiamo comunque le tab ma con un messaggio
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

# --- TAB 0: CLASSIFICHE ---
with t[0]:
    c1, c2 = st.columns(2)
    if f_sc is not None:
        with c1:
            st.subheader("🔥 Scontri Diretti")
            st.dataframe(style_df(f_sc), hide_index=True, use_container_width=True)
    if f_pt is not None:
        with c2:
            st.subheader("🎯 Classifica Punti")
            st.dataframe(style_df(f_pt), hide_index=True, use_container_width=True)
    if f_sc is None and f_pt is None:
        st.info("Carica scontridiretti.csv o classificapunti.csv")

# --- TAB 1, 2, 3: ROSE ---
if f_rs is not None:
    c = f_rs.columns
    # Pulizia numerica prezzi (gestisce virgole italiane)
    f_rs[c[-1]] = pd.to_numeric(f_rs[c[-1]].astype(str).str.replace(',','.').str.extract('(\d+)')[0], errors='coerce').fillna(0)
    
    with t[1]: # Budget
        st.subheader("💰 Bilancio Crediti")
        spesa = f_rs.groupby(c[0])[c[-1]].sum().reset_index()
        spesa['Extra'] = spesa[c[0]].str.upper().map(bg_extra).fillna(0)
        spesa['Totale'] = (spesa[c[-1]] + spesa['Extra']).astype(int)
        st.dataframe(style_df(spesa.sort_values('Totale', ascending=False)), hide_index=True, use_container_width=True)
    
    with t[2]: # Strategia
        st.subheader("🧠 Distribuzione Ruoli")
        f_rs[c[2]] = f_rs[c[2]].replace({'P':'Portiere','D':'Difensore','C':'Centrocampista','A':'Attaccante'})
        pivot = f_rs.pivot_table(index=c[0], columns=c[2], values=c[1], aggfunc='count').fillna(0).astype(int)
        st.dataframe(style_df(pivot), use_container_width=True)

    with t[3]: # Rose
        st.subheader("🏃 Rose Squadre")
        sel_sq = st.selectbox("Scegli Squadra:", sorted(f_rs[c[0]].unique()))
        rosa = f_rs[f_rs[c[0]] == sel_sq][[c[2], c[1], c[-1]]].sort_values(c[-1], ascending=False)
        st.dataframe(style_df(rosa.style.background_gradient(subset=[c[-1]], cmap='Greens')), hide_index=True, use_container_width=True)
else:
    with t[1]: st.warning("File rose_complete.csv non trovato")
    with t[2]: st.warning("File rose_complete.csv non trovato")
    with t[3]: st.warning("File rose_complete.csv non trovato")

# --- TAB 4: VINCOLI ---
if f_vn is not None:
    with t[4]:
        st.subheader("📅 Gestione Vincoli")
        v = f_vn.columns
        f_vn[v[2]] = pd.to_numeric(f_vn[v[2]].astype(str).str.replace(',','.').str.extract('(\d+)')[0], errors='coerce').fillna(0)
        f_vn[v[-1]] = pd.to_numeric(f_vn[v[-1]], errors='coerce').fillna(0).astype(int)

        v1, v2 = st.columns([1, 2])
        with v1:
            st.write("**Crediti Impegnati**")
            deb = f_vn.groupby(v[0])[v[2]].sum().reset_index().sort_values(v[2], ascending=False)
            st.dataframe(style_df(deb), hide_index=True, use_container_width=True)
        with v2:
            st.write("**Dettaglio Giocatori**")
            sq_v = st.selectbox("Squadra:", sorted(f_vn[v[0]].unique()), key="v_sel")
            det = f_vn[f_vn[v[0]] == sq_v][[v[1], v[2], v[-1]]].copy()
            st_v = det.sort_values(v[-1]).style.map(lambda x: 'background-color: #ffcdd2' if x == 1 else '', subset=[v[-1]])
            # Centratura forzata
            st
