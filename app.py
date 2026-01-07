import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Lega Manager", layout="wide")
st.markdown("<style>.stApp{background-color:#e8f5e9;} .stTabs, .stDataFrame{background-color:white; border-radius:12px; padding:10px;}</style>", unsafe_allow_html=True)
st.title("⚽ Centro Direzionale Fantalega")

bg_f = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

def cl(df, c):
    if df is None or c not in df.columns: return df
    m = {"NICO FABIO":"NICHOLAS","NICHO":"NICHOLAS","MATTEO STEFANO":"MATTEO"}
    df[c] = df[c].astype(str).str.strip().str.upper().replace(m)
    return df

def ld(target_name):
    """Cerca il file nel repository ignorando maiuscole/minuscole"""
    files = os.listdir(".")
    actual_file = next((f for f in files if f.lower() == target_name.lower()), None)
    if actual_file:
        try:
            df = pd.read_csv(actual_file, sep=None, engine='python', encoding='utf-8-sig').dropna(how='all')
            df.columns = [c.strip() for c in df.columns]
            return df
        except: return None
    return None

# Caricamento flessibile
d_sc = ld("scontridiretti.csv")
d_pt = ld("classificapunti.csv")
d_rs = ld("rose_complete.csv")
d_vn = ld("vincoli.csv")

t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

# --- TAB 1: CLASSIFICHE ---
with t[0]:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔥 Scontri")
        if d_sc is not None: st.dataframe(cl(d_sc, 'Giocatore'), hide_index=True, use_container_width=True)
        else: st.warning("File 'scontridiretti.csv' non trovato")
    with c2:
        st.subheader("🎯 Punti")
        if d_pt is not None:
            d_pt = cl(d_pt, 'Giocatore')
            for col in ['Punti Totali', 'Media']:
                if col in d_pt.columns: d_pt[col] = pd.to_numeric(d_pt[col].astype(str).str.replace(',','.'), errors='coerce').fillna(0)
            st.dataframe(d_pt[['Posizione','Giocatore','Punti Totali','Media']].sort_values('Punti Totali', ascending=False), hide_index=True, use_container_width=True)
        else: st.warning("File 'classificapunti.csv' non trovato")

# --- TAB BUDGET / STRATEGIA / ROSE ---
if d_rs is not None:
    f_c = next((c for c in d_rs.columns if 'squadra' in c.lower()), d_rs.columns[0])
    p_c = next((c for c in d_rs.columns if 'prezzo' in c.lower() or 'costo' in c.lower()), d_rs.columns[-1])
    r_c = next((c for c in d_rs.columns if 'ruolo' in c.lower()), d_rs.columns[2])
    n_c = next((c for c in d_rs.columns if 'nome' in c.lower() or 'giocatore' in c.lower()), d_rs.columns[1])
    d_rs = cl(d_rs, f_c)
    d_rs[p_c] = pd.to_numeric(d_rs[p_c].astype(str).str.replace(',','.'), errors='coerce').fillna(0)

    with t[1]:
        st.subheader("💰 Bilancio")
        e = d_rs.groupby(f_c)[p_c].sum().reset_index()
        e['Extra'] = e[f_c].map(bg_f).fillna(0)
        e['Totale'] = (e[p_c] + e['Extra']).astype(int)
        st.dataframe(e.sort_values('Totale', ascending=False), hide_index=True, use_container_width=True)
    
    with t[2]:
        st.subheader("🧠 Strategia")
        st.dataframe(d_rs.pivot_table(index=f_c, columns=r_c, values=n_c, aggfunc='count').fillna(0).astype(int), use_container_width=True)
    
    with t[3]:
        st.subheader("🏃 Rose")
        sq = st.selectbox("Seleziona Squadra:", sorted(d_rs[f_c].unique()))
        ds = d_rs[d_rs[f_c] == sq][[r_c, n_c, p_c]].sort_values(p_c, ascending=False)
        st.dataframe(ds.style.background_gradient(subset=[p_c], cmap='Greens'), hide_index=True, use_container_width=True)
else:
    for i in [1,2,3]: 
        with t[i]: st.error("❌ Non trovo 'rose_complete.csv' su GitHub. Verifica il nome del file!")

# --- TAB 5: VINCOLI ---
with t[4]:
    st.subheader("📅 Vincoli")
    if d_vn is not None:
        v_s = d_vn.columns[0]
        d_vn = d_vn[d_vn[v_s].notna() & ~d_vn[v_s].str.contains(r'\*|Riepilogo')].copy()
        c_f = d_vn.columns[2]
        d_vn[c_f] = pd.to_numeric(d_vn[c_f].astype(str).str.replace(',','.'), errors='coerce').fillna(0).astype(int)
        v1, v2 = st.columns([1, 2])
        with v1: st.dataframe(d_vn.groupby(v_s)[c_f].sum().reset_index().sort_values(c_f, ascending=False), hide_index=True, use_container_width=True)
        with v2:
            sv = st.selectbox("Dettaglio:", sorted(d_vn[v_s].unique()), key="v_s")
            st.dataframe(d_vn[d_vn[v_s] == sv].iloc[:, [1, 2]], hide_index=True, use_container_width=True)
    else:
        st.error("❌ Non trovo 'vincoli.csv' su GitHub.")
        
