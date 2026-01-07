import streamlit as st
import pandas as pd
import os

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; color: #1a1a1a; border-left: 6px solid; }
    .card-blue { background-color: #e3f2fd; border-color: #1a73e8; }
    .card-red { background-color: #fbe9e7; border-color: #d32f2f; }
    .card-grey { background-color: #f1f3f4; border-color: #9e9e9e; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI CARICAMENTO ---
def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    return s_str.upper() if s_str and "*" not in s_str else None

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True)
        if df.columns[0].startswith('Unnamed') or df.empty:
            df = pd.read_csv(f, skiprows=1, engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# CARICAMENTO DATI
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}

# ELABORAZIONE
if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace({"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"})
    f_rs['Nome'] = f_rs['Nome'].apply(clean_string)
    f_rs['Prezzo_N'] = pd.to_numeric(f_rs['Prezzo'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace({"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"})
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_string)
    v_cols = [c for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29'] if c in f_vn.columns]
    for c in v_cols: f_vn[c] = pd.to_numeric(f_vn[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)

# --- SIDEBAR: CERCA E GRAFICO CONFRONTO ---
with st.sidebar:
    st.header("🔍 Confronto Rapido")
    if f_rs is not None:
        scelte = st.multiselect("Seleziona giocatori:", sorted(f_rs['Nome'].unique()))
        if scelte:
            chart_data = []
            for n in scelte:
                dr = f_rs[f_rs['Nome'] == n].iloc[0]
                vv = f_vn[f_vn['Giocatore'] == n]['Tot_Vincolo'].iloc[0] if (f_vn is not None and n in f_vn['Giocatore'].values) else 0
                st.markdown(f"""<div class="player-card card-grey"><b>{n}</b><br>Totale: {int(dr['Prezzo_N']+vv)}</div>""", unsafe_allow_html=True)
                chart_data.append({"Nome": n, "Valore": dr['Prezzo_N']+vv})
            
            if len(chart_data) > 0:
                st.bar_chart(pd.DataFrame(chart_data).set_index("Nome"))

# --- MAIN ---
st.title("⚽ MuyFantaManager Dashboard")
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli", "🔄 Scambi", "✂️ Tagli"])

with t[0]: # CLASSIFICHE
    if f_pt is not None:
        st.subheader("📊 Performance Punti")
        f_pt['P_N'] = pd.to_numeric(f_pt['Punti Totali'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        st.bar_chart(f_pt.set_index("Giocatore")["P_N"])
        st.dataframe(f_pt[['Posizione','Giocatore','P_N','Media']], hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        st.subheader("💰 Distribuzione Ricchezza")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index()
        bu.columns = ['Squadra', 'Spesa Rose']
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1)
        bu['Patrimonio Reale'] = bu['Spesa Rose'] + bu['Tot_Vincolo'] + bu['Squadra'].map(bg_ex).fillna(0)
        
        st.bar_chart(bu.set_index("Squadra")["Patrimonio Reale"])
        st.dataframe(bu.sort_values("Patrimonio Reale", ascending=False), hide_index=True, use_container_width=True)

with t[2]: # ROSE
    if f_rs is not None:
        sq = st.selectbox("Squadra:", sorted(f_rs['Squadra_N'].unique()))
        df_sq = f_rs[f_rs['Squadra_N'] == sq]
        st.subheader(f"⚖️ Peso economico ruoli: {sq}")
        st.bar_chart(df_sq.groupby("Ruolo")["Prezzo_N"].sum())
        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo_N']], hide_index=True, use_container_width=True)

with t[3]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 Impegno Vincoli per Squadra")
        v_total = f_vn.groupby("Sq_N")["Tot_Vincolo"].sum()
        st.area_chart(v_total)
        st.dataframe(f_vn[['Squadra', 'Giocatore', 'Tot_Vincolo']], hide_index=True, use_container_width=True)

with t[4]: # SCAMBI
    st.info("Usa questa pagina per simulare le valutazioni ricalcolate. I grafici di confronto sono disponibili nella Sidebar a sinistra.")
    # ... (Logica scambi precedente rimane invariata)
    c1, c2 = st.columns(2)
    lista_n_sq = sorted([s for s in f_rs['Squadra_N'].unique() if s])
    with c1:
        sa = st.selectbox("Squadra A:", lista_n_sq, key="sa_f")
        ga = st.multiselect("Escono da A:", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist(), key="ga_f")
    with c2:
        sb = st.selectbox("Squadra B:", [s for s in lista_n_sq if s != sa], key="sb_f")
        gb = st.multiselect("Escono da B:", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist(), key="gb_f")
    
    if ga and gb:
        def get_info(nome):
            p = f_rs[f_rs['Nome']==nome]['Prezzo_N'].iloc[0] if nome in f_rs['Nome'].values else 0
            v = f_vn[f_vn['Giocatore']==nome]['Tot_Vincolo'].iloc[0] if (f_vn is not None and nome in f_vn['Giocatore'].values) else 0
            return {'p': p, 'v': v, 't': p + v}
        dict_a = {n: get_info(n) for n in ga}; dict_b = {n: get_info(n) for n in gb}
        tot_ante_a, tot_ante_b = sum(d['t'] for d in dict_a.values()), sum(d['t'] for d in dict_b.values())
        nuovo_tot = round((tot_ante_a + tot_ante_b) / 2)
        st.divider()
        res_a, res_b = st.columns(2)
        with res_a:
            for n, info in dict_b.items():
                peso = info['t'] / tot_ante_b if tot_ante_b > 0 else 1/len(gb); nuovo_t = round(peso * nuovo_tot)
                st.markdown(f"""<div class="player-card card-blue"><b>{n}</b><br>POST: Valutazione <b>{max(0, nuovo_t-int(info['v']))}</b> + Vinc <b>{int(info['v'])}</b></div>""", unsafe_allow_html=True)
        with res_b:
            for n, info in dict_a.items():
                peso = info['t'] / tot_ante_a if tot_ante_a > 0 else 1/len(ga); nuovo_t = round(peso * nuovo_tot)
                st.markdown(f"""<div class="player-card card-red"><b>{n}</b><br>POST: Valutazione <b>{max(0, nuovo_t-int(info['v']))}</b> + Vinc <b>{int(info['v'])}</b></div>""", unsafe_allow_html=True)

with t[5]: # TAGLI
    st.subheader("✂️ Analisi Tagli")
    sq_t = st.selectbox("Squadra:", sorted(f_rs['Squadra_N'].unique()), key="sq_t")
    gioc_t = st.selectbox("Giocatore:", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist(), key="gioc_t")
    if gioc_t:
        v_p = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gioc_t)]['Prezzo_N'].iloc[0]
        v_v = f_vn[f_vn['Giocatore'] == gioc_t]['Tot_Vincolo'].iloc[0] if (f_vn is not None and gioc_t in f_vn['Giocatore'].values) else 0
        rimborso = round((v_p + v_v) * 0.6)
        st.markdown(f"""<div class="cut-box"><h2>Rimborso: {rimborso}</h2><p>Calcolato sul 60% di {int(v_p+v_v)} totali</p></div>""", unsafe_allow_html=True)
