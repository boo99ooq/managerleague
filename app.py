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
def ld(f):
 if os.path.exists(f):
  try:
   df = pd.read_csv(f, sep=None, engine='python', encoding='utf-8-sig').dropna(how='all')
   df.columns = df.columns.str.strip()
   return df
  except: return None
 return None
d_sc, d_pt, d_rs, d_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
if any([d_sc is not None, d_pt is not None, d_rs is not None, d_vn is not None]):
 t = st.tabs(["🏆 Classifiche", "📊 Economia", "🧠 Strategia", "🏃 Rose", "📅 Vincoli"])
 with t[0]:
  c1, c2 = st.columns(2)
  if d_sc is not None:
   with c1: st.subheader("🔥 Scontri"); st.dataframe(cl(d_sc, 'Giocatore'), hide_index=True)
  if d_pt is not None:
   with c2:
    st.subheader("🎯 Punti")
    d_pt = cl(d_pt, 'Giocatore')
    for c in ['Punti Totali', 'Media']:
     if c in d_pt.columns: d_pt[c] = pd.to_numeric(d_pt[c].astype(str).str.replace(',','.'), errors='coerce').fillna(0)
    st.dataframe(d_pt[['Posizione','Giocatore','Punti Totali','Media']].sort_values('Punti Totali', ascending=False), hide_index=True)
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
   st.dataframe(e.sort_values('Totale', ascending=False), hide_index=True)
  with t[2]:
   st.subheader("🧠 Strategia")
   st.dataframe(d_rs.pivot_table(index=f_c, columns=r_c, values=n_c, aggfunc='count').fillna(0).astype(int))
  with t[3]:
   sq = st.selectbox("Squadra:", sorted(d_rs[f_c].unique()))
   ds = d_rs[d_rs[f_c] == sq][[r_c, n_c, p_c]].sort_values(p_c, ascending=False)
   st.dataframe(ds.style.background_gradient(subset=[p_c], cmap='Greens'), hide_index=True)
 if d_vn is not None:
  with t[4]:
   st.subheader("📅 Vincoli")
   v_s = d_vn.columns[0]
   d_vn = d_vn[d_vn[v_s].notna() & ~d_vn[v_s].str.contains(r'\*|Riepilogo')].copy()
   c_f = d_vn.columns[2]
   d_vn[c_f] = pd.to_numeric(d_vn[c_f].astype(str).str.replace(',','.'), errors='coerce').fillna(0).astype(int)
   v1, v2 = st.columns([1, 2])
   with v1: st.dataframe(d_vn.groupby(v_s)[c_f].sum().reset_index().sort_values(c_f, ascending=False), hide_index=True)
   with v2:
    sv = st.selectbox("Dettaglio:", sorted(d_vn[v_s].unique()), key="v_s")
    st.dataframe(d_vn[d_vn[v_s] == sv].iloc[:, [1, 2]], hide_index=True)
else: st.info("👋 Carica i CSV su GitHub.")
