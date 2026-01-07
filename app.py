import streamlit as st
import pandas as pd
import os

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("<style>.stApp { background-color: white; } div[data-testid='stDataFrame'] * { color: #1a1a1a !important; font-weight: bold !important; }</style>", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

# Configurazione Crediti Extra
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- FUNZIONI DI PULIZIA ---
def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "": return None
    return s_str.upper()

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True)
        if df.columns[0].startswith('Unnamed') or df.empty:
            df = pd.read_csv(f, skiprows=1, engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# CARICAMENTO FILE
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")

# ELABORAZIONE DATI (MAIUSCOLO E PULIZIA)
if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Nome'] = f_rs['Nome'].apply(clean_string)
    f_rs = f_rs.dropna(subset=['Squadra_N', 'Nome'])
    f_rs['Prezzo_N'] = pd.to_numeric(f_rs['Prezzo'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_string)
    v_cols = [c for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29'] if c in f_vn.columns]
    for c in v_cols: f_vn[c] = pd.to_numeric(f_vn[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn = f_vn.drop_duplicates(subset=['Sq_N', 'Giocatore'])

# --- TABS ---
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

# [TAB 0, 1, 2, 3 OMESSE PER BREVITÀ, RIMANGONO INVARIATE]

with t[4]: # TAB SCAMBI - LOGICA RIPARTIZIONE PESATA
    if f_rs is not None:
        st.subheader("🔄 Simulatore Scambi: Ripartizione Proporzionale")
        c1, c2 = st.columns(2)
        lista_nomi_sq = sorted(f_rs['Squadra_N'].unique())
        
        with c1:
            sa = st.selectbox("Squadra A:", lista_nomi_sq, key="sa_p")
            ga = st.multiselect("Escono da A:", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist(), key="ga_p")
        with c2:
            sb = st.selectbox("Squadra B:", [s for s in lista_nomi_sq if s != sa], key="sb_p")
            gb = st.multiselect("Escono da B:", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist(), key="gb_p")
        
        if ga and gb:
            def get_val_reale(nome):
                p = f_rs[f_rs['Nome']==nome]['Prezzo_N'].iloc[0] if nome in f_rs['Nome'].values else 0
                v = f_vn[f_vn['Giocatore']==nome]['Tot_Vincolo'].iloc[0] if (f_vn is not None and nome in f_vn['Giocatore'].values) else 0
                return p + v

            # 1. Valori Originali
            dict_a = {n: get_val_reale(n) for n in ga}
            dict_b = {n: get_val_reale(n) for n in gb}
            
            tot_a = sum(dict_a.values())
            tot_b = sum(dict_b.values())
            tot_scambio = tot_a + tot_b
            
            # 2. Nuovo Valore Obiettivo per squadra (Equo)
            nuovo_tot_squadra = tot_scambio / 2
            
            st.divider()
            st.write(f"### ⚖️ Valore Totale Scambiato: **{tot_scambio:g}**")
            st.write(f"Ogni squadra acquisirà giocatori per un valore totale di **{nuovo_tot_squadra:g}**")

            res_a, res_b = st.columns(2)
            
            with res_a:
                st.write(f"### ➡️ In entrata a {sa}")
                # Logica: i giocatori di B entrano in A. Il loro nuovo valore 
                # è (ValoreOriginale / Tot_B) * nuovo_tot_squadra
                for n, v_orig in dict_b.items():
                    peso = v_orig / tot_b if tot_b > 0 else 1/len(gb)
                    nuovo_val = peso * nuovo_tot_squadra
                    st.metric(n, f"{nuovo_val:.1f}", delta=f"ex {v_orig:g}")

            with res_b:
                st.write(f"### ➡️ In entrata a {sb}")
                # Logica: i giocatori di A entrano in B. Il loro nuovo valore
                # è (ValoreOriginale / Tot_A) * nuovo_tot_squadra
                for n, v_orig in dict_a.items():
                    peso = v_orig / tot_a if tot_a > 0 else 1/len(ga)
                    nuovo_val = peso * nuovo_tot_squadra
                    st.metric(n, f"{nuovo_val:.1f}", delta=f"ex {v_orig:g}")

            st.success(f"I pesi originali sono stati mantenuti. La somma dei nuovi valori per ogni squadra è esattamente {nuovo_tot_squadra:g}.")
