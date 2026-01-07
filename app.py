import streamlit as st
import pandas as pd
import os
import numpy as np

# 1. SETUP E STILE
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

# Dati Budget Extra (Esempio)
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

def cv(v):
    if pd.isna(v): return 0.0
    try:
        s = str(v).replace('"', '').replace(',', '.').strip()
        return float(s) if s != "" else 0.0
    except: return 0.0

def clean_name(s):
    if pd.isna(s) or str(s).strip().upper() == "NONE" or str(s).strip() == "": return "SKIP"
    return str(s).split(':')[0].replace('*', '').replace('"', '').strip().upper()

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, sep=',', engine='python', encoding='utf-8-sig')
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return None

# CARICAMENTO
f_rs, f_vn = ld("rose_complete.csv"), ld("vincoli.csv")

if f_rs is not None:
    f_rs['Nome'] = f_rs['Nome'].apply(clean_name)
    f_rs['Fantasquadra'] = f_rs['Fantasquadra'].apply(clean_name)
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)

if f_vn is not None:
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_name)
    for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29']:
        if c in f_vn.columns: f_vn[c] = f_vn[c].apply(cv)
    f_vn['Spesa Complessiva'] = f_vn.get('Costo 2026-27', 0) + f_vn.get('Costo 2027-28', 0) + f_vn.get('Costo 2028-29', 0)

t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

with t[5]:
    st.subheader("🔄 Simulatore Scambi Proporzionale (con Arrotondamento)")
    if f_rs is not None:
        sq_l = sorted([x for x in f_rs['Fantasquadra'].unique() if x != "SKIP"])
        
        def get_details(lista_nomi):
            dati = []
            for n in lista_nomi:
                p = f_rs[f_rs['Nome'] == n]['Prezzo'].values[0]
                v = f_vn[f_vn['Giocatore'] == n]['Spesa Complessiva'].values[0] if (f_vn is not None and n in f_vn['Giocatore'].values) else 0.0
                dati.append({'Giocatore': n, 'Valore Iniziale': p + v})
            return pd.DataFrame(dati)

        c1, c2 = st.columns(2)
        with c1:
            sa = st.selectbox("Squadra A:", sq_l, key="sa_prop")
            ga_list = st.multiselect("Cede da A:", f_rs[f_rs['Fantasquadra']==sa]['Nome'], key="ga_prop")
            df_a = get_details(ga_list)
            if not df_a.empty: st.table(df_a)

        with c2:
            sb = st.selectbox("Squadra B:", [s for s in sq_l if s != sa], key="sb_prop")
            gb_list = st.multiselect("Cede da B:", f_rs[f_rs['Fantasquadra']==sb]['Nome'], key="gb_prop")
            df_b = get_details(gb_list)
            if not df_b.empty: st.table(df_b)

        if not df_a.empty and not df_b.empty:
            val_a = df_a['Valore Iniziale'].sum()
            val_b = df_b['Valore Iniziale'].sum()
            val_totale = val_a + val_b
            
            # Punto di incontro teorico per squadra (meta del valore totale scambiato)
            punto_pareggio = val_totale / 2
            
            # Calcolo coefficienti di rettifica per mantenere la proporzione iniziale
            # Se la squadra A cede 200 e deve ricevere 210 (punto pareggio), 
            # i giocatori che riceve vengono riproporzionati.
            coeff_per_giocatori_di_a = punto_pareggio / val_a if val_a > 0 else 1
            coeff_per_giocatori_di_b = punto_pareggio / val_b if val_b > 0 else 1

            st.write("---")
            st.markdown("### 📊 Esito dello Scambio (Valori Arrotondati)")
            
            col_res1, col_res2 = st.columns(2)
            
            with col_res1:
                st.write(f"**Giocatori che vanno a {sb}:**")
                for _, row in df_a.iterrows():
                    nuovo_val = round(row['Valore Iniziale'] * coeff_per_giocatori_di_a)
                    st.write(f"🔹 {row['Giocatore']}: da {row['Valore Iniziale']:g} a **{nuovo_val}**")

            with col_res2:
                st.write(f"**Giocatori che vanno a {sa}:**")
                for _, row in df_b.iterrows():
                    nuovo_val = round(row['Valore Iniziale'] * coeff_per_giocatori_di_b)
                    st.write(f"🔸 {row['Giocatore']}: da {row['Valore Iniziale']:g} a **{nuovo_val}**")
            
            st.info("💡 I nuovi valori tengono conto del peso iniziale del giocatore e sono arrotondati all'intero.")
