import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Lega Manager", layout="wide")
st.markdown("<style>.stApp{background-color:#f4f7f6;} .stTabs{background-color:white; border-radius:10px; padding:10px;}</style>", unsafe_allow_html=True)
st.title("⚽ Centro Direzionale Fantalega")

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

def load_d(n):
    f_act = next((f for f in os.listdir(".") if f.lower() == n.lower()), None)
    if f_act:
        try:
            df = pd.read_csv(f_act, sep=None, engine='python', encoding='utf-8-sig').dropna(how='all')
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except: return None
    return None

def stl_c(obj):
    s = obj if hasattr(obj, 'style') == False else obj.style
    return s.set_properties(**{'text-align': 'center'}).set_table_styles([dict(selector='th', props=[('text-align', 'center')])])

f_sc, f_pt, f_rs, f_vn = load_d("scontridiretti.csv"), load_d("classificapunti.csv"), load_d("rose_complete.csv"), load_d("vincoli.csv")

t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])

with t[0]:
    c1, c2 = st.columns(2)
    if f_sc is not None:
        with c1: st.subheader("🔥 Scontri"); st.dataframe(stl_c(f_sc), hide_index=True)
    if f_pt is not None:
        with c2: st.subheader("🎯 Punti"); st.dataframe(stl_c(f_pt), hide_index=True)

if f_rs is not None and len(f_rs.columns) >= 3:
    cs = f_rs.columns
    f_rs[cs[-1]] = pd.to_numeric(f_rs[cs[-1]].astype(str).str.replace(',','.').str.extract('(\d+)', expand=False), errors='coerce').fillna(0)
    
    with t[1]:
        st.subheader("💰 Bilancio")
        e = f_rs.groupby(cs[0])[cs[-1]].sum().reset_index()
        e['Extra'] = e[cs[0]].str.strip().str.upper().map(bg_ex).fillna(0)
        e['Totale'] = (e[cs[-1]] + e['Extra']).astype(int)
        st.dataframe(stl_c(e.sort_values('Totale', ascending=False)), hide_index=True)
    
    with t[2]:
        st.subheader("🧠 Ruoli")
        df_st = f_rs.copy()
        df_st[cs[2]] = df_st[cs[2]].astype(str).str.upper().replace({'P':'Portiere','D':'Difensore','C':'Centrocampista','A':'Attaccante'})
        piv = df_st.pivot_table(index=cs[0], columns=cs[2], values=cs[1], aggfunc='count').fillna(0).astype(int)
        st.dataframe(stl_c(piv))

    with t
