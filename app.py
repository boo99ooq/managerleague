import streamlit as st
import pandas as pd
import os
st.set_page_config(layout="wide")
st.title("⚽ Centro Direzionale")
bg={"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
def l(n):
 for f in os.listdir("."):
  if f.lower()==n.lower():
   try:
    df=pd.read_csv(f,sep=None,engine='python',encoding='utf-8-sig').dropna(how='all')
    df.columns=[str(c).strip() for c in df.columns]
    return df
   except:return None
 return None
def s(o):
 x=o if hasattr(o,'style')==False else o.style
 return x.set_properties(**{'text-align':'center'}).set_table_styles([dict(selector='th',props=[('text-align','center')])])
f1,f2,f3,f4=l("scontridiretti.csv"),l("classificapunti.csv"),l("rose_complete.csv"),l("vincoli.csv")
t=st.tabs(["🏆 Classifica","💰 Budget","🧠 Strategia","🏃 Rose","📅 Vincoli"])
with t[0]:
 c1,c2=st.columns(2)
 if f1 is not None:
  with c1:st.write("🔥 Scontri");st.dataframe(s(f1),hide_index=True)
 if f2 is not None:
  with c2:st.write("🎯 Punti");st.dataframe(s(f2),hide_index=True)
if f3 is not None and len(f3.columns)>=3:
 c=f3.columns
 f3[c[-1]]=pd.to_numeric(f3[c[-1]].astype(str).str.replace(',','.').str.extract('(\d+)',expand=False),errors='coerce').fillna(0)
 with t[1]:
  e=f3.groupby(c[0])[c[-1]].sum().reset_index()
  e['Extra']=e[c[0]].str.strip().str.upper().map(bg).fillna(0)
  e['Totale']=(e[c[-1]]+e['Extra']).astype(int)
  st.dataframe(s(e.sort_values('Totale',ascending=False)),hide_index=True)
 with t[2]:
  df=f3.copy()
  df[c[2]]=df[c[2]].astype(str).str.upper().replace({'P':'POR','D':'DIF','C':'CEN','A':'ATT'})
  st.dataframe(s(df.pivot_table(index=c[0],columns=c[2],values=c[1],aggfunc='count').fillna(0).astype(int)))
 with t[3]:
  q=st.selectbox("Team:",sorted(f3[c[0]].unique()))
  d=f3[f3[c[0]]==q][[c[2],c[1],c[-1]]].sort_values(c[-1],ascending=False)
  st.dataframe(s(d.style.background_gradient(subset=[c[-1]],cmap='Greens')),hide_index=True)
if f4 is not None and len(f4.columns)>=3:
 with t[4]:
  v=f4.columns
  f4[v[2]]=pd.to_numeric(f4[v[2]].astype(str).str.replace(',','.').str.extract('(\d+)',expand=False),errors='coerce').fillna(0)
  v1,v2=st.columns([1,2])
  with v1:
   st.write
