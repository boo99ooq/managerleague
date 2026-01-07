import streamlit as st
import pandas as pd
import os

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

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
    f_vn = f_vn.dropna(subset=['Sq_N', 'Giocatore'])
    v_cols = [c for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29'] if c in f_vn.columns]
    for c in v_cols: 
        f_vn[c] = pd.to_numeric(f_vn[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_Testo'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " anni"
    f_vn = f_vn.drop_duplicates(subset=['Sq_N', 'Giocatore'])

# --- TABS ---
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

# [TAB 0, 1, 2, 3 rimangono identici per coerenza di dati]
with t[0]:
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 Punti")
            f_pt['P_N'] = pd.to_numeric(f_pt['Punti Totali'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            f_pt['FM'] = pd.to_numeric(f_pt['Media'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N','FM']].sort_values('Posizione').style.background_gradient(subset=['P_N', 'FM'], cmap='YlGn').format({"P_N": "{:g}", "FM": "{:.2f}"}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ Scontri Diretti")
            f_sc['P_S'] = pd.to_numeric(f_sc['Punti'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            st.dataframe(f_sc[['Posizione','Giocatore','P_S','Gol Fatti','Gol Subiti']].style.background_gradient(subset=['P_S'], cmap='Blues').format({"P_S": "{:g}"}), hide_index=True, use_container_width=True)

with t[1]:
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

with t[2]:
    if f_rs is not None:
        lista_sq = sorted(f_rs['Squadra_N'].unique())
        sq = st.selectbox("Seleziona Squadra:", lista_sq)
        df_sq = f_rs[f_rs['Squadra_N'] == sq].copy()
        def color_ruoli(row):
            r = str(row['Ruolo']).upper()
            bg = '#E3F2FD' if 'PORT' in r else '#E8F5E9' if 'DIF' in r else '#FFFDE7' if 'CEN' in r else '#FFEBEE' if 'ATT' in r else '#FFFFFF'
            return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo_N']].style.apply(color_ruoli, axis=1).format({"Prezzo_N":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]:
    if f_vn is not None:
        st.subheader("📅 Dettaglio Vincoli")
        sq_v = st.selectbox("Filtra Squadra:", ["TUTTE"] + sorted(f_vn['Sq_N'].unique()))
        df_v_display = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        cols_v = ['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_Testo']
        st.dataframe(df_v_display[cols_v].sort_values('Tot_Vincolo', ascending=False).style.background_gradient(subset=['Tot_Vincolo'], cmap='Purples').format({"Tot_Vincolo": "{:g}"}), hide_index=True, use_container_width=True)
        st.info(f"💰 Totale Impegno Vincoli: **{df_v_display['Tot_Vincolo'].sum():g}** crediti")

with t[4]: # TAB SCAMBI - RICALCOLO COMPLETO
    if f_rs is not None:
        st.subheader("🔄 Simulatore Scambi: Analisi Pre/Post")
        c1, c2 = st.columns(2)
        lista_nomi_sq = sorted(f_rs['Squadra_N'].unique())
        
        with c1:
            sa = st.selectbox("Squadra A:", lista_nomi_sq, key="sa_f")
            ga = st.multiselect("Giocatori in uscita da A:", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist(), key="ga_f")
        with c2:
            sb = st.selectbox("Squadra B:", [s for s in lista_nomi_sq if s != sa], key="sb_f")
            gb = st.multiselect("Giocatori in uscita da B:", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist(), key="gb_f")
        
        if ga and gb:
            def get_val_reale(nome):
                p = f_rs[f_rs['Nome']==nome]['Prezzo_N'].iloc[0] if nome in f_rs['Nome'].values else 0
                v = f_vn[f_vn['Giocatore']==nome]['Tot_Vincolo'].iloc[0] if (f_vn is not None and nome in f_vn['Giocatore'].values) else 0
                return p + v

            # 1. Calcolo Valore Ante
            ante_a = sum(get_val_reale(n) for n in ga)
            ante_b = sum(get_val_reale(n) for n in gb)
            
            # 2. Ricalcolo Valore Medio (Meritocratico)
            tot_scambio = ante_a + ante_b
            nuovo_val_unitario = tot_scambio / (len(ga) + len(gb))
            
            # 3. Valore Post Scambio
            post_a = nuovo_val_unitario * len(gb)
            post_b = nuovo_val_unitario * len(ga)

            st.divider()
            st.info(f"✨ **Logica Meritocratica:** Il valore totale degli atleti ({tot_scambio:g}) viene ripartito equamente. Ogni giocatore assumerà un nuovo valore di **{nuovo_val_unitario:.1f}**.")

            # Visualizzazione Tabelle Pre/Post
            res_a, res_b = st.columns(2)
            with res_a:
                st.write(f"### 📊 Bilancio {sa}")
                st.write(f"**Valore Pacchetto Ceduto:** {ante_a:g}")
                st.write(f"**Valore Pacchetto Acquisito:** {post_a:.1f}")
                diff_a = post_a - ante_a
                st.metric("Impatto Patrimonio", f"{post_a:.1f}", delta=f"{diff_a:.1f}")
                for n in ga: st.caption(f"OUT: {n} (era {get_val_reale(n):g})")
                for n in gb: st.caption(f"IN: {n} (diventa {nuovo_val_unitario:.1f})")

            with res_b:
                st.write(f"### 📊 Bilancio {sb}")
                st.write(f"**Valore Pacchetto Ceduto:** {ante_b:g}")
                st.write(f"**Valore Pacchetto Acquisito:** {post_b:.1f}")
                diff_b = post_b - ante_b
                st.metric("Impatto Patrimonio", f"{post_b:.1f}", delta=f"{diff_b:.1f}")
                for n in gb: st.caption(f"OUT: {n} (era {get_val_reale(n):g})")
                for n in ga: st.caption(f"IN: {n} (diventa {nuovo_val_unitario:.1f})")
