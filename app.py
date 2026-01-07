import streamlit as st
import pandas as pd
import os
st.set_page_config(page_title="Lega", layout="wide")
st.markdown("<style>.stApp{background-color:#f4f7f6;} .stTabs{background-color:white; border-radius:10px; padding:10px;}</style>", unsafe_allow_html=True)
st.title("⚽ Centro Direzionale")
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
def ld(n):
    f_a = next((f for f in os.listdir(".") if f.lower() == n.lower()), None)
    if f_a:
        try:
            df = pd.read_csv(f_a, sep=None, engine='python', encoding='utf-8-sig').dropna(how='all')
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except: return None
    return None
def sc(obj):
    s = obj if hasattr(obj, 'style') == False else obj.style
    return s.set_properties(**{'text-align': 'center'}).set_table_styles([dict(selector='th', props=[('text-align', 'center')])])
f1, f2, f3, f4 = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])
with t[0]:
    c1, c2 = st.columns(2)
    if f1 is not None:
        with c1: st.subheader("🔥 Scontri"); st.dataframe(sc(f1), hide_index=True)
    if f2 is not None:
        with c2: st.subheader("🎯 Punti"); st.dataframe(sc(f2), hide_index=True)
if f3 is not None and len(f3.columns) >= 3:
    cs = f3.columns
    f3[cs[-1]] = pd.to_numeric(f3[cs[-1]].astype(str).str.replace(',','.').str.extract('(\d+)', expand=False), errors='coerce').fillna(0)
    with t[1]:
        st.subheader("💰 Bilancio")
        e = f3.groupby(cs[0])[cs[-1]].sum().reset_index()
        e['Extra'] = e[cs[0]].str.strip().str.upper().map(bg_ex).fillna(0)
        e['Totale'] = (e[cs[-1]] + e['Extra']).astype(int)
        st.dataframe(sc(e.sort_values('Totale', ascending=False)), hide_index=True)
    with t[2]:
        st.subheader("🧠 Ruoli")
        df_s = f3.copy()
        df_s[cs[2]] = df_s[cs[2]].astype(str).str.upper().replace({'P':'Portiere','D':'Difensore','C':'Centrocampista','A':'Attaccante'})
        st.dataframe(sc(df_s.pivot_table(index=cs[0], columns=cs[2], values=cs[1], aggfunc='count').fillna(0).astype(int)))
    with t[3]:
        sq = st.selectbox("Squadra:", sorted(f3[cs[0]].unique()))
        d_q = f3[f3[cs[0]] == sq][[cs[2], cs[1], cs[-1]]].sort_values(cs[-1], ascending=False)
        st.dataframe(sc(d_q.style.background_gradient(subset=[cs[-1]], cmap='Greens')), hide_index=True)
if f4 is not None and len(f4.columns) >= 3:
    with t[4]:
        st.subheader("📅 Vincoli")
        vc = f4.columns
        f4[vc[2]] = pd.to_numeric(f4[vc[2]].astype(str).str.replace(',','.').str.extract('(\d+)', expand=False), errors='coerce').fillna(0)
        v1, v2 = st.columns([1, 2])
        with v1:
            st.write("**Crediti**")
            db = f4.groupby(vc[0])[vc[2]].sum().reset_index().sort_values(vc[2], ascending=False)
            st.dataframe(sc(db), hide_index=True)
        with v2:
            st.write("**
