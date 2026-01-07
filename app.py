import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# CSS DEFINITIVO PER GRASSETTO TOTALE
st.markdown("""
<style>
    /* 1. Forza il grassetto su tutto il testo dell'app */
    * {
        font-weight: bold !important;
    }

    /* 2. Forza il grassetto specifico sulle tabelle e i loro contenuti */
    div[data-testid="stDataFrame"] div[data-testid="styled-table-container"] * {
        font-weight: bold !important;
        color: black !important;
    }
    
    /* 3. Forza il grassetto nei menu a tendina (nomi squadre) e bottoni */
    div[data-baseweb="select"] * {
        font-weight: bold !important;
    }
    
    button p {
        font-weight: bold !important;
    }

    /* 4. Forza il grassetto nelle card e nei box ricalcolo */
    .player-card, .patrimonio-box, .cut-box {
        font-weight: bold !important;
        border-width: 3px !important;
    }
    
    .card-blue { background-color: #e3f2fd; border-color: #1a73e8; color: black; }
    .card-red { background-color: #fbe9e7; border-color: #d32f2f; color: black; }
    .card-grey { background-color: #f1f3f4; border-color: #9e9e9e; color: black; }
    
    .patrimonio-box { 
        background-color: #f0f2f6; 
        padding: 15px; 
        border-radius: 10px; 
        border: 2px solid #1a73e8; 
        text-align: center;
    }
    
    /* 5. Forza il grassetto sui numeri nelle metriche */
    [data-testid="stMetricValue"] {
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI PULIZIA ---
def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str.upper()

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try:
        return float(str(val).replace(',', '.'))
    except:
        return 0.0

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True)
        if df.columns[0].startswith('Unnamed') or df.empty:
            df = pd.read_csv(f, skiprows=1, engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# --- CARICAMENTO E MAPPATURA ---
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Nome'] = f_rs['Nome'].apply(clean_string)
    f_rs = f_rs.dropna(subset=['Squadra_N', 'Nome'])
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore'] = f_vn['Giocatore'].apply(clean_string)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- SIDEBAR: CONFRONTO ---
with st.sidebar:
    st.header("🔍 CONFRONTO")
    if f_rs is not None:
        scelte = st.multiselect("CERCA GIOCATORI", sorted(f_rs['Nome'].unique()))
        for n in scelte:
            dr = f_rs[f_rs['Nome'] == n].iloc[0]
            vv = f_vn[f_vn['Giocatore'] == n]['Tot_Vincolo'].iloc[0] if (f_vn is not None and n in f_vn['Giocatore'].values) else 0
            st.markdown(f"""
            <div class="player-card card-grey">
                {n} ({dr['Squadra_N']})<br>
                VALUTAZIONE: {int(dr['Prezzo_N'])} | VINC: {int(vv)}<br>
                TOT REALE: {int(dr['Prezzo_N'] + vv)}
            </div>
            """, unsafe_allow_html=True)

# --- MAIN ---
st.title("⚽ MUYFANTAMANAGER")
t = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "✂️ TAGLI"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 CLASSIFICA PUNTI")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            f_pt['FM'] = f_pt['Media'].apply(to_num)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N','FM']].sort_values('Posizione').style.background_gradient(subset=['P_N', 'FM'], cmap='YlGn').format({"P_N": "{:g}", "FM": "{:.2f}"}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ SCONTRI DIRETTI")
            f_sc['P_S'] = f_sc['Punti'].apply(to_num)
            st.dataframe(f_sc[['Posizione','Giocatore','P_S','Gol Fatti','Gol Subiti']].style.background_gradient(subset=['P_S'], cmap='Blues').format({"P_S": "{:g}"}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        st.subheader("💰 BUDGET E PATRIMONIO")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI EXTRA'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['PATRIMONIO TOTALE'] = bu['SPESA ROSE'] + bu['SPESA VINCOLI'] + bu['CREDITI EXTRA']
        
        st.bar_chart(bu.set_index("Squadra_N")[['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI EXTRA']], color=["#1a73e8", "#9c27b0", "#ff9800"])
        st.dataframe(bu.sort_values("PATRIMONIO TOTALE", ascending=False).style.background_gradient(cmap='YlOrRd', subset=['PATRIMONIO TOTALE']).format({c: "{:g}" for c in bu.columns if c != 'Squadra_N'}), hide_index=True, use_container_width=True)

with t[2]: # ROSE
    if f_rs is not None:
        sq = st.selectbox("SELEZIONA SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="rose_sel")
        df_sq = f_rs[f_rs['Squadra_N'] == sq]
        st.bar_chart(df_sq.groupby("Ruolo")["Prezzo_N"].sum())
        def color_ruoli(row):
            r = str(row['Ruolo']).upper()
            bg = '#E3F2FD' if 'PORT' in r else '#E8F5E9' if 'DIF' in r else '#FFFDE7' if 'CEN' in r else '#FFEBEE' if 'ATT' in r else '#FFFFFF'
            return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo_N']].style.apply(color_ruoli, axis=1).format({"Prezzo_N":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 DETTAGLIO VINCOLI")
        sq_v = st.selectbox("FILTRA SQUADRA", ["TUTTE"] + sorted([s for s in f_vn['Sq_N'].unique() if s]), key="vinc_sel")
        df_v_display = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.dataframe(df_v_display[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False).style.background_gradient(subset=['Tot_Vincolo'], cmap='Purples').format({"Tot_Vincolo": "{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI
    st.subheader("🔄 SIMULATORE SCAMBI")
    c1, c2 = st.columns(2)
    lista_n_sq = sorted([s for s in f_rs['Squadra_N'].unique() if s])
    with c1:
        sa = st.selectbox("SQUADRA A", lista_n_sq, key="sa_f")
        ga = st.multiselect("ESCONO DA A", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist(), key="ga_f")
    with c2:
        sb = st.selectbox("SQUADRA B", [s for s in lista_n_sq if s != sa], key="sb_f")
        gb = st.multiselect("ESCONO DA B", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist(), key="gb_f")
    
    if ga and gb:
        def get_info(nome):
            p = f_rs[f_rs['Nome']==nome]['Prezzo_N'].iloc[0] if nome in f_rs['Nome'].values else 0
            v = f_vn[f_vn['Giocatore']==nome]['Tot_Vincolo'].iloc[0] if (f_vn is not None and nome in f_vn['Giocatore'].values) else 0
            return {'p': p, 'v': v, 't': p + v}
        dict_a = {n: get_info(n) for n in ga}; dict_b = {n: get_info(n) for n in gb}
        tot_ante_a, tot_ante_b = sum(d['t'] for d in dict_a.values()), sum(d['t'] for d in dict_b.values())
        nuovo_tot_scambio = round((tot_ante_a + tot_ante_b) / 2)

        def get_patrimonio(sq):
            rose = f_rs[f_rs['Squadra_N']==sq]['Prezzo_N'].sum()
            vinc = f_vn[f_vn['Sq_N']==sq]['Tot_Vincolo'].sum() if f_vn is not None else 0
            extra = bg_ex.get(sq, 0)
            return rose + vinc + extra

        pat_a_v, pat_b_v = get_patrimonio(sa), get_patrimonio(sb)
        diff = nuovo_tot_scambio - tot_ante_a
        
        st.divider()
        p1, p2 = st.columns(2)
        with p1:
            st.markdown(f"""<div class="patrimonio-box">NUOVO PATRIMONIO {sa}<br><h2 style="margin:0;">{int(pat_a_v + diff)}</h2><small>PRIMA: {int(pat_a_v)}</small></div>""", unsafe_allow_html=True)
        with p2:
            st.markdown(f"""<div class="patrimonio-box">NUOVO PATRIMONIO {sb}<br><h2 style="margin:0;">{int(pat_b_v - diff)}</h2><small>PRIMA: {int(pat_b_v)}</small></div>""", unsafe_allow_html=True)
        st.divider()

        if st.button("📋 GENERA VERBALE SCAMBIO"):
            report = f"📜 VERBALE SCAMBIO - {datetime.now().strftime('%d/%m/%Y')}\n{sa} <-> {sb}\n\n"
            report += f"✅ VERSO {sa}:\n"
            for n, info in dict_b.items():
                peso = info['t']/tot_ante_b if tot_ante_b > 0 else 1/len(gb)
                report += f"- {n}: VALUTAZIONE {round(peso*nuovo_tot_scambio-info['v'])} + VINC {int(info['v'])}\n"
            report += f"\n✅ VERSO {sb}:\n"
            for n, info in dict_a.items():
                peso = info['t']/tot_ante_a if tot_ante_a > 0 else 1/len(ga)
                report += f"- {n}: VALUTAZIONE {round(peso*nuovo_tot_scambio-info['v'])} + VINC {int(info['v'])}\n"
            st.code(report)

        res_a, res_b = st.columns(2)
        with res_a:
            for n, info in dict_b.items():
                peso = info['t']/tot_ante_b if tot_ante_b > 0 else 1/len(gb); nuovo_t = round(peso*nuovo_tot_scambio)
                st.markdown(f"""<div class="player-card card-blue">{n}<br>VALUTAZIONE: {max(0, nuovo_t-int(info['v']))} + VINC: {int(info['v'])}</div>""", unsafe_allow_html=True)
        with res_b:
            for n, info in dict_a.items():
                peso = info['t']/tot_ante_a if tot_ante_a > 0 else 1/len(ga); nuovo_t = round(peso*nuovo_tot_scambio)
                st.markdown(f"""<div class="player-card card-red">{n}<br>VALUTAZIONE: {max(0, nuovo_t-int(info['v']))} + VINC: {int(info['v'])}</div>""", unsafe_allow_html=True)

with t[5]: # TAGLI
    st.subheader("✂️ SIMULATORE TAGLI")
    sq_t = st.selectbox("SELEZIONA SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="sq_tag")
    gioc_t = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist(), key="gioc_tag")
    if gioc_t:
        v_p = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gioc_t)]['Prezzo_N'].iloc[0]
        v_v = f_vn[f_vn['Giocatore'] == gioc_t]['Tot_Vincolo'].iloc[0] if (f_vn is not None and gioc_t in f_vn['Giocatore'].values) else 0
        rimborso = round((v_p + v_v) * 0.6)
        st.markdown(f"""<div class="cut-box"><h3>💰 RIMBORSO: {rimborso} CREDITI</h3>VALUTAZIONE: {int(v_p)} | VINCOLI: {int(v_v)}</div>""", unsafe_allow_html=True)
        if st.button("📋 GENERA VERBALE TAGLIO"):
            st.code(f"✂️ TAGLIO UFFICIALE - {sq_t}\nGIOCATORE: {gioc_t}\nRIMBORSO: {rimborso} CREDITI")
