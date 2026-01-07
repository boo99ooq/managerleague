import streamlit as st
import pandas as pd
import os

# 1. SETUP
st.set_page_config(page_title="Lega", layout="wide")
st.markdown("<style>.stApp{background-color:#e8f5e9;} .stTabs, .stDataFrame{background-color:white; border-radius:10px; padding:5px;}</style>", unsafe_allow_html=True)
st.title("⚽ Centro Direzionale Fantalega")

# 2. BUDGET
budgets = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

# 3. FUNZIONI
def get_df(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, sep=',', encoding='utf-8-sig').dropna(how='all')
        df.columns = df.columns.str.strip()
        return df
    except: return None

def clean_n(df, c):
    if df is None or c not in df.columns: return df
    m = {"NICO FABIO":"NICHOLAS","NICHO":"NICHOLAS","DANI ROBI":"DANI ROBI","MATTEO STEFANO":"MATTEO"}
    df[c] = df[c].astype(str).str.strip().str.upper().replace(m)
    return df

def style_c(obj):
    s = obj.style if isinstance(obj, pd.DataFrame) else obj
    return s.set_properties(**{'text-align':'center'}).set_table_styles([dict(selector='th', props=[('text-align','center')])])

# 4. MONITORAGGIO FILE (Sidebar)
st.sidebar.header("🔍 Stato Database")
files = {
    "scontridiretti.csv": "❌ Mancante",
    "classificapunti.csv": "❌ Mancante",
    "rose_complete.csv": "❌ Mancante",
    "vincoli.csv": "❌ Mancante"
}
for f in files.keys():
    if os.path.exists(f): files[f] = "✅ Caricato"
    st.sidebar.write(f"{f}: {files[f]}")

# Caricamento
f_sc = get_df("scontridiretti.csv")
f_pt = get_df("classificapunti.csv")
f_rs = get_df("rose_complete.csv")
f_vn = get_df("vincoli.csv")

# 5. APP
if any([f_sc is not None, f_pt is not None, f_rs is not None, f_vn is not None]):
    # Creiamo solo i tab per i file che esistono davvero
    labels = []
    if f_sc is not None or f_pt is not None: labels.append("🏆 Classifiche")
    if f_rs is not None: 
        labels.append("💰 Budget")
        labels.append("🧠 Strategia")
        labels.append("🏃 Rose")
    if f_vn is not None: labels.append("📅 Vincoli")
    
    t = st.tabs(labels)
    curr = 0

    if f_sc is not None or f_pt is not None:
        with t[curr]:
            c1, c2 = st.columns(2)
            if f_sc is not None:
                with c1:
                    st.write("🔥 **Scontri**")
                    st.dataframe(style_c(clean_n(f_sc, 'Giocatore')), hide_index=True, use_container_width=True)
            if f_pt is not None:
                with c2:
                    st.write("🎯 **Punti**")
                    df_pt = clean_n(f_pt, 'Giocatore')
                    for col in ['Punti Totali', 'Media']:
                        if col in df_pt.columns:
                            df_pt[col] = df_pt[col].astype(str).str.replace(',','.').apply(pd.to_numeric, errors='coerce')
                    st.dataframe(style_c(df_pt[['Posizione','Giocatore','Punti Totali','Media']]), hide_index=True, use_container_width=True)
        curr += 1

    if f_rs is not None:
        cs = f_rs.columns
        f_c, n_c, r_c, p_c = cs[0], cs[1], cs[2], cs[-1]
        f_rs = clean_n(f_rs, f_c)
        f_rs[p_c] = pd.to_numeric(f_rs[p_c], errors='coerce').fillna(0).astype(int)
        
        with t[curr]:
            st.write("💰 **Bilancio Economico**")
            eco = f_rs.groupby(f_c)[p_c].sum().reset_index()
