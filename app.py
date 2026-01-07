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

# CARICAMENTO
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")

# ELABORAZIONE ROSE
if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Nome'] = f_rs['Nome'].apply(clean_string)
    f_rs = f_rs.dropna(subset=['Squadra_N', 'Nome'])
    f_rs['Prezzo_N'] = pd.to_numeric(f_rs['Prezzo'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

# ELABORAZIONE VINCOLI
if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_string)
    v_cols = [c for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29'] if c in f_vn.columns]
    for c in v_cols: f_vn[c] = pd.to_numeric(f_vn[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " anni"
    f_vn = f_vn.drop_duplicates(subset=['Sq_N', 'Giocatore'])

# --- TABS ---
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

with t[1]: # TAB BUDGET (Salvaguardata)
    if f_rs is not None:
        st.subheader("💰 Bilancio Globale")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index()
        bu.columns = ['Squadra', 'Spesa Rose']
        if f_vn is not None:
            v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index()
            bu = pd.merge(bu, v_sum, left_on='Squadra', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1)
            bu.rename(columns={'Tot_Vincolo': 'Spesa Vincoli'}, inplace=True)
        else: bu['Spesa Vincoli'] = 0
        bu['Crediti Disponibili'] = bu['Squadra'].map(bg_ex).fillna(0)
        bu['Patrimonio Reale'] = bu['Spesa Rose'] + bu['Spesa Vincoli'] + bu['Crediti Disponibili']
        num_cols_b = ['Spesa Rose', 'Spesa Vincoli', 'Crediti Disponibili', 'Patrimonio Reale']
        st.dataframe(bu.sort_values('Patrimonio Reale', ascending=False).style.background_gradient(cmap='YlOrRd', subset=num_cols_b).format({c: "{:g}" for c in num_cols_b}), hide_index=True, use_container_width=True)

with t[4]: # TAB SCAMBI - ANALISI DETTAGLIATA PRE/POST
    if f_rs is not None:
        st.subheader("🔄 Simulatore Scambi: Analisi Granulare Valori")
        c1, c2 = st.columns(2)
        lista_n_sq = sorted([s for s in f_rs['Squadra_N'].unique() if s])
        
        with c1:
            sa = st.selectbox("Squadra A:", lista_n_sq, key="sa_val")
            ga = st.multiselect("Escono da A:", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist(), key="ga_val")
        with c2:
            sb = st.selectbox("Squadra B:", [s for s in lista_n_sq if s != sa], key="sb_val")
            gb = st.multiselect("Escono da B:", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist(), key="gb_val")
        
        if ga and gb:
            def get_info(nome):
                p = f_rs[f_rs['Nome']==nome]['Prezzo_N'].iloc[0] if nome in f_rs['Nome'].values else 0
                v = f_vn[f_vn['Giocatore']==nome]['Tot_Vincolo'].iloc[0] if (f_vn is not None and nome in f_vn['Giocatore'].values) else 0
                return {'p': p, 'v': v, 't': p + v}

            dict_a = {n: get_info(n) for n in ga}
            dict_b = {n: get_info(n) for n in gb}
            tot_ante_a = sum(d['t'] for d in dict_a.values())
            tot_ante_b = sum(d['t'] for d in dict_b.values())
            nuovo_tot_squadra = round((tot_ante_a + tot_ante_b) / 2)
            
            st.divider()
            m1, m2 = st.columns(2)
            m1.metric(f"Valore Totale Acquisito da {sa}", f"{nuovo_tot_squadra}", delta=f"ex {int(tot_ante_a)}")
            m2.metric(f"Valore Totale Acquisito da {sb}", f"{nuovo_tot_squadra}", delta=f"ex {int(tot_ante_b)}")
            st.divider()

            res_a, res_b = st.columns(2)
            with res_a:
                st.write(f"### ➡️ Acquisizioni {sa}")
                for n, info in dict_b.items():
                    peso = info['t'] / tot_ante_b if tot_ante_b > 0 else 1/len(gb)
                    nuovo_t = round(peso * nuovo_tot_squadra)
                    quota_v = int(info['v'])
                    quota_b = max(0, nuovo_t - quota_v)
                    
                    st.markdown(f"**{n}**")
                    st.markdown(f"📦 **POST: Base {quota_b} + Vincolo {quota_v}**")
                    st.caption(f"📜 PRE: Base {int(info['p'])} + Vincolo {quota_v} (Totale: {int(info['t'])})")
                    st.divider()
                    
            with res_b:
                st.write(f"### ➡️ Acquisizioni {sb}")
                for n, info in dict_a.items():
                    peso = info['t'] / tot_ante_a if tot_ante_a > 0 else 1/len(ga)
                    nuovo_t = round(peso * nuovo_tot_squadra)
                    quota_v = int(info['v'])
                    quota_b = max(0, nuovo_t - quota_v)
                    
                    st.markdown(f"**{n}**")
                    st.markdown(f"📦 **POST: Base {quota_b} + Vincolo {quota_v}**")
                    st.caption(f"📜 PRE: Base {int(info['p'])} + Vincolo {quota_v} (Totale: {int(info['t'])})")
                    st.divider()
