import streamlit as st
import pandas as pd
import os

# 1. SETUP & STYLE
st.set_page_config(page_title="Lega Manager", layout="wide")
st.markdown("<style>.stApp{background-color:#e8f5e9;} .stTabs, .stDataFrame{background-color:white; border-radius:12px; padding:10px; shadow:0 4px 6px rgba(0,0,0,0.05);}</style>", unsafe_allow_html=True)
st.title("⚽ Centro Direzionale Fantalega")

# 2. DATI FISSI
bg_f = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

# 3. FUNZIONI
def cl_n(df, c):
    if df is None or c not in df.columns: return df
    m = {"NICO FABIO":"NICHOLAS","NICHO":"NICHOLAS","MATTEO STEFANO":"MATTEO"}
    df[c] = df[c].astype(str).str.strip().str.upper().replace(m)
    return df

def ld(f):
    if os.path.exists(f):
        try:
            df = pd.read_csv(f, sep=None, engine='python', encoding='utf-8-sig').dropna(how='all')
            df.columns = df.columns.str.strip()
            return df
        except: return None
    return None

# 4. CARICAMENTO
d_sc, d_pt, d_rs, d_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")

# 5. LOGICA APP
if any([d_sc is not None, d_pt is not None, d_rs is not None, d_vn is not None]):
    tabs = st.tabs(["🏆 Classifiche", "📊 Economia", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

    with tabs[0]: # CLASSIFICHE
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🔥 Scontri Diretti")
            if d_sc is not None: st.dataframe(cl_n(d_sc, 'Giocatore'), hide_index=True)
        with c2:
            st.subheader("🎯 Classifica Punti")
            if d_pt is not None:
                d_pt = cl_n(d_pt, 'Giocatore')
                for c in ['Punti Totali', 'Media']:
                    if c in d_pt.columns: d_pt[c] = pd.to_numeric(d_pt[c].astype(str).str.replace(',','.'), errors='coerce').fillna(0)
                st.dataframe(d_pt[['Posizione','Giocatore','Punti Totali','Media']].sort_values('Punti Totali', ascending=False), hide_index=True)

    if d_rs is not None:
        f_c = next((c for c in d_rs.columns if 'squadra' in c.lower()), d_rs.columns[0])
        p_c = next((c for c in d_rs.columns if 'prezzo' in c.lower() or 'costo' in c.lower()), d_rs.columns[-1])
        r_c = next((c for c in d_rs.columns if 'ruolo' in c.lower()), d_rs.columns[2])
        n_c = next((c for c in d_rs.columns if 'nome' in c.lower() or 'giocatore' in c.lower()), d_rs.columns[1])
        d_rs = cl_n(d_rs, f_c)
        d_rs[p_c] = pd.to_numeric(d_rs[p_c].astype(str).str.replace(',','.'), errors='coerce').fillna(0)

        with tabs[1]: # ECONOMIA
            st.subheader("💰 Bilancio")
            eco = d_rs.groupby(f_c)[p_c].sum().reset_index()
            eco['Extra'] = eco[f_c].map(bg_f).fillna(0)
            eco['Totale'] = (eco[p_c] + eco['Extra']).astype(int)
            st.dataframe(eco.sort_values('Totale', ascending=False), hide_index=
