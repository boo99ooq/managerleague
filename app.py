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

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            f_pt['P_N'] = pd.to_numeric(f_pt['Punti Totali'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            f_pt['FM'] = pd.to_numeric(f_pt['Media'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N','FM']].sort_values('Posizione').style.background_gradient(subset=['P_N', 'FM'], cmap='YlGn').format({"P_N": "{:g}", "FM": "{:.2f}"}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            f_sc['P_S'] = pd.to_numeric(f_sc['Punti'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            st.dataframe(f_sc[['Posizione','Giocatore','P_S','Gol Fatti','Gol Subiti']].style.background_gradient(subset=['P_S'], cmap='Blues').format({"P_S": "{:g}"}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
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

with t[2]: # ROSE
    if f_rs is not None:
        lista_sq = sorted([s for s in f_rs['Squadra_N'].unique() if s])
        sq = st.selectbox("Seleziona Squadra:", lista_sq)
        df_sq = f_rs[f_rs['Squadra_N'] == sq].copy()
        def color_ruoli(row):
            r = str(row['Ruolo']).upper()
            bg = '#E3F2FD' if 'PORT' in r else '#E8F5E9' if 'DIF' in r else '#FFFDE7' if 'CEN' in r else '#FFEBEE' if 'ATT' in r else '#FFFFFF'
            return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo_N']].style.apply(color_ruoli, axis=1).format({"Prezzo_N":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI (FIXED sorted error)
    if f_vn is not None:
        st.subheader("📅 Dettaglio Vincoli")
        sq_list_v = sorted([s for s in f_vn['Sq_N'].unique() if s])
        sq_v = st.selectbox("Filtra Squadra:", ["TUTTE"] + sq_list_v)
        df_v_display = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.dataframe(df_v_display[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False).style.background_gradient(subset=['Tot_Vincolo'], cmap='Purples').format({"Tot_Vincolo": "{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI CON TOTALI SQUADRA
    if f_rs is not None:
        st.subheader("🔄 Simulatore Scambi: Analisi Quote")
        c1, c2 = st.columns(2)
        lista_n_sq = sorted([s for s in f_rs['Squadra_N'].unique() if s])
        
        with c1:
            sa = st.selectbox("Squadra A:", lista_n_sq, key="sa_t")
            ga = st.multiselect("Escono da A:", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist(), key="ga_t")
        with c2:
            sb = st.selectbox("Squadra B:", [s for s in lista_n_sq if s != sa], key="sb_t")
            gb = st.multiselect("Escono da B:", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist(), key="gb_t")
        
        if ga and gb:
            def get_info(nome):
                p = f_rs[f_rs['Nome']==nome]['Prezzo_N'].iloc[0] if nome in f_rs['Nome'].values else 0
                v = f_vn[f_vn['Giocatore']==nome]['Tot_Vincolo'].iloc[0] if (f_vn is not None and nome in f_vn['Giocatore'].values) else 0
                return {'p': p, 'v': v, 't': p + v}

            dict_a = {n: get_info(n) for n in ga}
            dict_b = {n: get_info(n) for n in gb}
            tot_ante_a, tot_ante_b = sum(d['t'] for d in dict_a.values()), sum(d['t'] for d in dict_b.values())
            nuovo_tot = (tot_ante_a + tot_ante_b) / 2
            
            # TOTALI SQUADRA
            st.divider()
            m1, m2 = st.columns(2)
            m1.metric(f"Totale Scambiato {sa}", f"{nuovo_tot:.1f}", delta=f"ex {tot_ante_a:g}")
            m2.metric(f"Totale Scambiato {sb}", f"{nuovo_tot:.1f}", delta=f"ex {tot_ante_b:g}")
            st.divider()

            res_a, res_b = st.columns(2)
            with res_a:
                st.write(f"### ➡️ In {sa}")
                for n, info in dict_b.items():
                    nuovo_t = (info['t'] / tot_ante_b) * nuovo_tot
                    st.write(f"**{n}** | Nuovo: **{nuovo_t:.1f}** (Base: {max(0, nuovo_t-info['v']):.1f}, Vinc: {info['v']:g})")
            with res_b:
                st.write(f"### ➡️ In {sb}")
                for n, info in dict_a.items():
                    nuovo_t = (info['t'] / tot_ante_a) * nuovo_tot
                    st.write(f"**{n}** | Nuovo: **{nuovo_t:.1f}** (Base: {max(0, nuovo_t-info['v']):.1f}, Vinc: {info['v']:g})")
