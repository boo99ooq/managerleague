import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Lega", layout="wide")
st.markdown("<style>.stApp{background-color:#e8f5e9;} .stTabs, .stDataFrame{background-color:white; border-radius:10px; padding:5px;}</style>", unsafe_allow_html=True)
st.title("⚽ Fantalega Manager")

bg = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

def get_df(n):
    for f in os.listdir("."):
        if f.lower() == n.lower():
            try:
                df = pd.read_csv(f, sep=',', encoding='utf-8-sig').dropna(how='all')
                df.columns = df.columns.str.strip()
                return df
            except: return None
    return None

def stl(obj):
    s = obj.style if isinstance(obj, pd.DataFrame) else obj
    return s.set_properties(**{'text-align':'center'}).set_table_styles([dict(selector='th', props=[('text-align','center')])])

f_sc, f_pt, f_rs, f_vn = get_df("scontridiretti.csv"), get_df("classificapunti.csv"), get_df("rose_complete.csv"), get_df("vincoli.csv")

st.sidebar.write("Scontri:", "✅" if f_sc is not None else "❌")
st.sidebar.write("Punti:", "✅" if f_pt is not None else "❌")
st.sidebar.write("Rose:", "✅" if f_rs is not None else "❌")
st.sidebar.write("Vincoli:", "✅" if f_vn is not None else "❌")

if any([f_sc is not None, f_pt is not None, f_rs is not None, f_vn is not None]):
    tabs = []
    if f_sc is not None or f_pt is not None: tabs.append("🏆 Classifiche")
    if f_rs is not None: tabs.extend(["💰 Budget", "🧠 Strategia", "🏃 Rose"])
    if f_vn is not None: tabs.append("📅 Vincoli")
    
    t = st.tabs(tabs)
    i = 0

    if f_sc is not None or f_pt is not None:
        with t[i]:
            c1, c2 = st.columns(2)
            if f_sc is not None:
                with c1: st.write("**Scontri**"); st.dataframe(stl(f_sc), hide_index=True)
            if f_pt is not None:
                with c2:
                    st.write("**Punti**")
                    for c in ['Punti Totali', 'Media']:
                        if c in f_pt.columns: f_pt[c] = f_pt[c].astype(str).str.replace(',','.').apply(pd.to_numeric, errors='coerce')
                    st.dataframe(stl(f_pt[['Posizione','Giocatore','Punti Totali','Media']]), hide_index=True)
        i += 1

    if f_rs is not None:
        c = f_rs.columns
        fc, nc, rc, pc = c[0], c[1], c[2], c[-1]
        f_rs[pc] = pd.to_numeric(f_rs[pc], errors='coerce').fillna(0).astype(int)
        with t[i]:
            st.write("**Crediti**")
            e = f_rs.groupby(fc)[pc].sum().reset_index()
            e['Extra'] = e[fc].str.upper().map(bg).fillna(0)
            e['Totale'] = (e[pc] + e['Extra']).astype(int)
            st.dataframe(stl(e.sort_values('Totale', ascending=False)), hide_index=True)
        with t[i+1]:
            st.write("**Ruoli**")
            f_rs[rc] = f_rs[rc].replace({'P':'Portiere','D':'Difensore','C':'Centrocampista','A':'Attaccante'})
            st.dataframe(stl(f_rs.pivot_table(index=fc, columns=rc, values=nc, aggfunc='count').fillna(0).astype(int)))
        with t[i+2]:
            s = st.selectbox("Squadra:", sorted(f_rs[fc].unique()))
            d = f_rs[f_rs[fc] == s][[rc, nc, pc]].sort_values(pc, ascending=False)
            st.dataframe(stl(d.style.background_gradient(subset=[pc], cmap='Greens')), hide_index=True)
        i += 3

    if f_vn is not None:
        with t[i]:
            v = f_vn.columns
            sv, gv, cv, dv = v[0], v[1], v[2], v[-1]
            f_vn[cv] = f_vn[cv].astype(str).str.replace(',','.').apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)
            vx, vy = st.columns([1, 2])
            with vx: st.dataframe(stl(f_vn.groupby(sv)[cv].sum().reset_index().sort_values(cv, ascending=False)), hide_index=True)
            with vy:
                sl = st.selectbox("Dettaglio:", sorted(f_vn[sv].unique()), key="v")
                dfv = f_vn[f_vn[sv] == sl][[gv, cv, dv]].copy()
                dfv[dv] = pd.to_numeric(dfv[dv], errors='coerce').fillna(0).astype(int)
                st.dataframe(stl(dfv.sort_values(dv, ascending=False).style.map(lambda x: 'background-color: #ffcdd2' if x == 1 else '', subset=[dv])), hide_index=True)
else: st.warning("Carica i CSV su GitHub.")
