import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager", layout="wide", initial_sidebar_state="expanded")

# CSS TOTALE: GRASSETTO, CARD SIDEBAR E LAYOUT TAGLI
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .search-card { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        margin-bottom: 15px; 
        border: 2px solid #1a73e8;
        color: #1a1a1a !important;
    }
    .card-header { border-bottom: 2px solid #eee; margin-bottom: 10px; padding-bottom: 5px; }
    .player-name { color: #1a73e8; font-size: 1.1em; }
    .team-name { color: #666; font-size: 0.8em; }
    .stat-row { display: block; width: 100%; margin-bottom: 4px; }
    .label { float: left; color: #555; font-size: 0.85em; }
    .valore { float: right; }
    .clearfix { clear: both; }
    .quot-box { margin-top: 10px; padding-top: 5px; border-top: 1px dashed #ccc; color: #2e7d32; }
    .tot-reale { background-color: #f8f9fa; padding: 5px; margin-top: 8px; border-radius: 5px; text-align: center; }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid; }
    .card-blue { background-color: #e3f2fd; border-color: #1a73e8; color: black; }
    .card-red { background-color: #fbe9e7; border-color: #d32f2f; color: black; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 2px solid #1a73e8; text-align: center; }
    .cut-info-box { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #ddd; color: black; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO ---
def clean_quotazioni_name(name):
    if not isinstance(name, str): return name
    name = name.replace('č', 'E').replace('ň', 'O').replace('ř', 'I').replace('ć', 'C').replace('Č', 'E').replace('Ň', 'O')
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8')
    name = name.upper().strip()
    mapping = {
        'MARTINEZ JO.': 'MARTINEZ JO', 'MILINKOVIC-SAVIC V.': 'MILINKOVIC SAVIC', 'N\'DICKA': 'NDICKA',
        'TAVARES N.': 'NUNO TAVARES', 'OSTIGARD': 'OSTIGAARD', 'PEZZELLA GIU.': 'PEZZELLA',
        'RODRIGUEZ J.': 'RODRIGUEZ J', 'DIMARCO': 'DIMARCO', 'CARLOS AUGUSTO': 'CARLOS AUGU',
        'KOSSOUNOU': 'KOSSOUNOU', 'THURAM K.': 'K THURAM', 'KONE M.': 'KONE', 'KONE M. (S)': 'KONE',
        'KAMARA': 'KAMAA', 'PELLEGRINI LO.': 'PELLEGRINI LORENZO', 'THORSTVEDT': 'THORSVEDT',
        'BERNABE': 'BERNABE', 'NORTON-CUFFY': 'NORTON CUFFY', 'NICOLUSSI CAVIGLIA': 'NICOLUSSI CAVIGLIA',
        'DELE-BASHIRU': 'DELE BASHIRU', 'AKINSANMIRO': 'NDRI AKINSAMIRO', 'LOFTUS-CHEEK': 'LOFTUS CHEEK',
        'MKHITARYAN': 'MKHTARYAN', 'SULEMANA I.': 'K SULEMANA', 'SULEMANA K.': 'K SULEMANA',
        'SOULE': 'SOULE K', 'DAVIS K.': 'DAVIS', 'DOUVIKAS': 'DOUVIKAS', 'SAELEMAEKERS': 'SAELEMAKERS',
        'ESPOSITO F.P.': 'PIO ESPOSITO', 'ESPOSITO SE.': 'ESPOSITO', 'MARTINELLI': 'MARTINELLI',
        'GABRIEL': 'GABRIEL', 'ZAMBO ANGUISSA': 'ANGUISSA', 'THURAM M.': 'THURAM M', 'MARTINEZ L.': 'LAUTARO'
    }
    if name in mapping: return mapping[name]
    name = re.sub(r'\s[A-Z]\.$', '', name)
    name = re.sub(r'\s[A-Z]\.[A-Z]\.$', '', name)
    return name

def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True, encoding='latin1')
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Nome_Match'] = df['Nome'].apply(clean_quotazioni_name)
            return df[['Nome_Match', 'Qt.A']].rename(columns={'Qt.A': 'Quotazione', 'Nome_Match': 'Nome'})
        return df.dropna(how='all')
    except: return None

def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip().upper()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

# --- CARICAMENTO DATI ---
f_rs, f_vn, f_pt, f_sc = ld("rose_complete.csv"), ld("vincoli.csv"), ld("classificapunti.csv"), ld("scontridiretti.csv")
f_qt = ld("quotazioni.csv", is_quot=True)

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Nome_N'] = f_rs['Nome'].apply(clean_string)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, left_on='Nome_N', right_on='Nome', how='left', suffixes=('', '_qt')).fillna({'Quotazione': 0})

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore_N'] = f_vn['Giocatore'].apply(clean_string)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 RICERCA GIOCATORE")
    if f_rs is not None:
        scelte = st.multiselect("SELEZIONA", sorted(f_rs['Nome_N'].unique()))
        st.write("---")
        for n in scelte:
            dr = f_rs[f_rs['Nome_N'] == n].iloc[0]
            v_info = f_vn[f_vn['Giocatore_N'] == n] if f_vn is not None else None
            val_vinc = v_info['Tot_Vincolo'].iloc[0] if (v_info is not None and not v_info.empty) else 0
            durata_vinc = v_info['Anni_T'].iloc[0] if (v_info is not None and not v_info.empty) else "NO"
            st.markdown(f"""
            <div class="search-card">
                <div class="card-header">
                    <span class="player-name"><b>{n}</b></span><br>
                    <span class="team-name">{dr['Squadra_N']} - {dr['Ruolo']}</span>
                </div>
                <div class="stat-row">
                    <span class="label">Acquisto:</span> <span class="valore"><b>{int(dr['Prezzo_N'])}</b></span>
                    <div class="clearfix"></div>
                </div>
                <div class="stat-row">
                    <span class="label">Vincolo:</span> <span class="valore"><b>{int(val_vinc)}</b> ({durata_vinc})</span>
                    <div class="clearfix"></div>
                </div>
                <div class="quot-box">
                    <span class="label" style="color:#2e7d32;">Quot. Attuale:</span> <span class="valore"><b>{int(dr['Quotazione'])}</b></span>
                    <div class="clearfix"></div>
                </div>
                <div class="tot-reale">
                    <span class="label">TOTALE REALE:</span> <span class="valore"><b>{int(dr['Prezzo_N'] + val_vinc)}</b></span>
                    <div class="clearfix"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# --- MAIN APP ---
st.title("⚽ MUYFANTAMANAGER GOLDEN V6.8")
t = st.tabs(["🏆 CLASSIFICHE", "💰 BUDGET", "🏃 ROSE", "📅 VINCOLI", "🔄 SCAMBI", "✂️ TAGLI"])

with t[0]: # TAB 0: CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 PUNTI")
            f_pt['P_N'], f_pt['FM'] = f_pt['Punti Totali'].apply(to_num), f_pt['Media'].apply(to_num)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N','FM']].sort_values('Posizione').style.background_gradient(subset=['P_N', 'FM'], cmap='YlGn').format({"P_N": "{:g}", "FM": "{:.2f}"}).set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ SCONTRI")
            f_sc['P_S'] = f_sc['Punti'].apply(to_num)
            f_sc['DR'] = f_sc['Gol Fatti'].apply(to_num) - f_sc['Gol Subiti'].apply(to_num)
            st.dataframe(f_sc[['Posizione','Giocatore','P_S','DR']].style.background_gradient(subset=['P_S'], cmap='Blues').background_gradient(subset=['DR'], cmap='RdYlGn').format({"P_S": "{:g}", "DR": "{:+g}"}).set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

with t[1]: # TAB 1: BUDGET
    if f_rs is not None:
        st.subheader("💰 BUDGET E PATRIMONIO")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'ROSE'})
        v_s = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_s, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1)
        bu['DISP'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['TOT'] = bu['ROSE'] + bu['Tot_Vincolo'] + bu['DISP']
        st.dataframe(bu.sort_values("TOT", ascending=False).style.background_gradient(cmap='YlOrRd', subset=['TOT']).background_gradient(cmap='Greens', subset=['DISP']).format({c: "{:g}" for c in bu.columns if c != 'Squadra_N'}).set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

with t[2]: # TAB 2: ROSE
    if f_rs is not None:
        mancanti = f_rs[f_rs['Quotazione'] == 0]['Nome_N'].unique()
        if len(mancanti) > 0:
            with st.expander(f"⚠️ {len(mancanti)} GIOCATORI SENZA QUOTAZIONE"):
                st.write(", ".join(sorted(mancanti)))
        sq = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="rs_v68")
        df_sq = f_rs[f_rs['Squadra_N'] == sq][['Ruolo', 'Nome_N', 'Prezzo_N', 'Quotazione']]
        def color_ruoli(row):
            bg = {'POR': '#FCE4EC', 'DIF': '#E8F5E9', 'CEN': '#E3F2FD', 'ATT': '#FFFDE7'}.get(str(row['Ruolo']).upper()[:3], '#FFFFFF')
            return [f'background-color: {bg}; color: black; font-weight: 900;'] * len(row)
        st.dataframe(df_sq.style.apply(color_ruoli, axis=1).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # TAB 3: VINCOLI
    if f_vn is not None:
        st.subheader("📅 VINCOLI PER SQUADRA")
        sq_v = st.selectbox("SELEZIONA SQUADRA", ["TUTTE"] + sorted(f_vn['Sq_N'].unique()), key="v_v68")
        df_v = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.dataframe(df_v[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False).style.background_gradient(cmap='Purples', subset=['Tot_Vincolo']).format({"Tot_Vincolo": "{:g}"}).set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

with t[4]: # TAB 4: SCAMBI
    st.subheader("🔄 SIMULATORE SCAMBI")
    if f_rs is not None:
        c1, c2 = st.columns(2)
        l_sq = sorted(f_rs['Squadra_N'].unique())
        with c1:
            sa = st.selectbox("SQUADRA A", l_sq, key="sa_68")
            ga = st.multiselect("DA A", f_rs[f_rs['Squadra_N']==sa]['Nome_N'].tolist(), key="ga_68")
        with c2:
            sb = st.selectbox("SQUADRA B", [s for s in l_sq if s != sa], key="sb_68")
            gb = st.multiselect("DA B", f_rs[f_rs['Squadra_N']==sb]['Nome_N'].tolist(), key="gb_68")
        if ga and gb:
            def get_v(n):
                p = f_rs[f_rs['Nome_N']==n]['Prezzo_N'].iloc[0]
                v = f_vn[f_vn['Giocatore_N']==n]['Tot_Vincolo'].iloc[0] if (f_vn is not None and n in f_vn['Giocatore_N'].values) else 0
                return p + v, v
            tot_a, tot_b = sum(get_v(n)[0] for n in ga), sum(get_v(n)[0] for n in gb)
            nuovo = round((tot_a + tot_b) / 2)
            st.divider()
            st.metric("Valore Scambio (Media)", f"{nuovo} cr")
            res_a, res_b = st.columns(2)
            with res_a:
                st.write(f"**{sa} RICEVE:**")
                for n in gb:
                    v_t, v_v = get_v(n); n_v = max(0, round((v_t/tot_b)*nuovo) - v_v)
                    st.markdown(f'<div class="player-card card-blue"><b>{n}</b><br>VAL: <b>{int(n_v)}</b> + VINC: {int(v_v)}</div>', unsafe_allow_html=True)
            with res_b:
                st.write(f"**{sb} RICEVE:**")
                for n in ga:
                    v_t, v_v = get_v(n); n_v = max(0, round((v_t/tot_a)*nuovo) - v_v)
                    st.markdown(f'<div class="player-card card-red"><b>{n}</b><br>VAL: <b>{int(n_v)}</b> + VINC: {int(v_v)}</div>', unsafe_allow_html=True)

with t[5]: # TAB 5: TAGLI
    st.subheader("✂️ SIMULATORE TAGLI")
    if f_rs is not None:
        sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="st_68")
        gi_t = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == sq_t]['Nome_N'].tolist(), key="gt_68")
        if gi_t:
            p_d = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome_N'] == gi_t)].iloc[0]
            v_d = f_vn[f_vn['Giocatore_N'] == gi_t] if f_vn is not None else pd.DataFrame()
            v_v = v_d['Tot_Vincolo'].iloc[0] if not v_d.empty else 0
            rimb = round((p_d['Prezzo_N'] + v_v) * 0.6)
            st.markdown(f"""
            <div class="cut-info-box">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h2>{gi_t}</h2> <span style="background: #eee; padding: 5px 15px; border-radius: 20px;">{p_d['Ruolo']}</span>
                </div><hr>
                <div style="display: flex; gap: 40px; flex-wrap: wrap;">
                    <div><span class="stat-label">Acquisto</span><br><b class="stat-value">{int(p_d['Prezzo_N'])}</b></div>
                    <div><span class="stat-label">Vincolo</span><br><b class="stat-value">{int(v_v)}</b></div>
                    <div><span class="stat-label">Quotazione</span><br><b class="stat-value" style="color:#1a73e8;">{int(p_d['Quotazione'])}</b></div>
                    <div style="background: #fff3f3; padding: 10px; border-radius: 8px; border: 1px solid #ff4b4b;">
                        <span style="color: #ff4b4b; font-size: 0.8em;">RIMBORSO</span><br><h2 style="color: #ff4b4b; margin:0;">{rimb}</h2>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
