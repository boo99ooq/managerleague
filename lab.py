import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V4.7", layout="wide", initial_sidebar_state="expanded")

# --- BLOCCO CSS DEFINITIVO (Neretto, Gradienti e Roseagg) ---
st.markdown("""
<style>
    /* FORZA NERETTO 900 OVUNQUE */
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame div, .stDataFrame td, .stDataFrame th, p, div, span, label, table, td, th { 
        font-weight: 900 !important; 
        color: #000 !important;
    }

    /* TABELLE HTML (ROSEAGG) */
    .golden-table { width: 100%; border-collapse: collapse; border: 3px solid #333; margin: 10px 0; }
    .golden-table th { background-color: #f1f5f9; border: 2px solid #333; padding: 12px; text-transform: uppercase; }
    .golden-table td { border: 1px solid #333; padding: 10px; text-align: center; }

    /* GRADIENTI NELLE TABELLE STREAMLIT (Tramite sovrapposizione CSS) */
    [data-testid="stTable"] { 
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important; 
        border: 3px solid #333;
        border-radius: 10px;
    }
    
    /* BOX SPECIALI */
    .stat-card { background: #fff; padding: 15px; border-radius: 10px; border: 3px solid #333; text-align: center; box-shadow: 4px 4px 0px #333; }
    .cut-box { background: #fff; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; text-align: center; }
    .punto-incontro-box { background: #fff3e0; padding: 10px 30px; border: 3px solid #ff9800; border-radius: 15px; text-align: center; margin: 10px auto; width: fit-content; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x' or str(val).strip() == '': return 0.0
    s = str(val).replace('€', '').strip()
    if ',' in s: s = s.replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

def super_clean(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

# --- CARICAMENTO DATI ---
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS"}
FILE_DB = "mercatone_gennaio.csv"

def load_all():
    if not os.path.exists("rose_complete.csv"): return None, None, None, None
    rs = pd.read_csv("rose_complete.csv", encoding='latin1', engine='python')
    rs['Squadra_N'] = rs['Fantasquadra'].str.upper().str.strip().replace(map_n)
    rs['Match_Nome'] = rs['Nome'].apply(super_clean)
    rs['Prezzo_N'] = rs['Prezzo'].apply(to_num)
    
    if os.path.exists("quotazioni.csv"):
        qt = pd.read_csv("quotazioni.csv", encoding='latin1')
        col_q = next((c for c in qt.columns if 'QT' in c.upper() or 'VAL' in c.upper()), 'Qt.A')
        qt['Match_Nome'] = qt['Nome'].apply(super_clean)
        rs = pd.merge(rs, qt[['Match_Nome', col_q]], on='Match_Nome', how='left').fillna({col_q: 0})
        rs = rs.rename(columns={col_q: 'Quotazione'})
    
    def simple_ld(f): return pd.read_csv(f, engine='python', encoding='latin1').dropna(how='all') if os.path.exists(f) else None

    vn = simple_ld("vincoli.csv")
    if vn is not None:
        vn['Sq_N'] = vn['Squadra'].str.upper().str.strip().replace(map_n)
        vn['Giocatore_Match'] = vn['Giocatore'].apply(super_clean)
        v_cols = [c for c in vn.columns if '202' in c]
        for c in v_cols: vn[c] = vn[c].apply(to_num)
        vn['Tot_Vincolo'] = vn[v_cols].sum(axis=1)

    return rs, vn, simple_ld("classificapunti.csv"), simple_ld("scontridiretti.csv")

f_rs, f_vn, f_pt, f_sc = load_all()
df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])
rimborsi_m = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

# TAB CLASSIFICHE
with t[0]:
    st.subheader("📊 CLASSIFICHE (NERETTO E GRADIENTE)")
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1: st.table(f_pt.head(10)) # Usiamo table per forzare il CSS del gradiente
    if f_sc is not None:
        with c2: st.table(f_sc.head(10))

# TAB BUDGET
with t[1]:
    st.subheader("💰 PATRIMONIO DINAMICO")
    if f_rs is not None:
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_s = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_s, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI_INIZ'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO'] = bu['Squadra_N'].map(rimborsi_m).fillna(0)
        bu['TOTALE'] = bu['SPESA ROSE'] + bu['SPESA VINCOLI'] + bu['CREDITI_INIZ'] + bu['RECUPERO']
        st.table(bu.sort_values('TOTALE', ascending=False))

# TAB ROSE (STILE ROSEAGG DEFINITIVO)
with t[2]:
    if f_rs is not None:
        sq_r = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()))
        df_team = f_rs[f_rs['Squadra_N'] == sq_r].copy()
        
        # 1. Box Stats
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card">👥 GIOCATORI<br><h2>{len(df_team)}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card">💰 ASTA<br><h2>{int(df_team["Prezzo_N"].sum())}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card">📈 VALORE<br><h2>{int(df_team["Quotazione"].sum())}</h2></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="stat-card">👶 GIOVANI<br><h2>{len(df_team[df_team["Match_Nome"].str.contains("GIOVANI|GIO", na=False)])}</h2></div>', unsafe_allow_html=True)

        # 2. Riassunto Ruoli HTML
        pal = {'POR': '#F06292', 'DIF': '#81C784', 'CEN': '#64B5F6', 'ATT': '#FFF176'}
        html_r = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>ASTA</th><th>VALORE</th></tr></thead><tbody>'
        for r in ['POR', 'DIF', 'CEN', 'ATT']:
            d_rep = df_team[df_team['Ruolo'].str.contains(r, na=False, case=False)]
            html_r += f'<tr style="background-color:{pal[r]};"><td>{r}</td><td>{int(d_rep["Prezzo_N"].sum())}</td><td>{int(d_rep["Quotazione"].sum())}</td></tr>'
        st.markdown(html_r + '</tbody></table>', unsafe_allow_html=True)

        # 3. Dettaglio Rosa con shades
        shades = {'POR': ['#FCE4EC','#F8BBD0','#F48FB1','#F06292'], 'DIF': ['#E8F5E9','#C8E6C9','#A5D6A7','#81C784'], 'CEN': ['#E3F2FD','#BBDEFB','#90CAF9','#64B5F6'], 'ATT': ['#FFFDE7','#FFF9C4','#FFF59D','#FFF176']}
        html_d = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>NOME</th><th>PREZZO</th><th>QUOT</th></tr></thead><tbody>'
        for _, row in df_team.sort_values(['Prezzo_N'], ascending=False).iterrows():
            rk = 'ATT' if 'ATT' in str(row['Ruolo']).upper() else 'CEN' if 'CEN' in str(row['Ruolo']).upper() else 'DIF' if 'DIF' in str(row['Ruolo']).upper() else 'POR'
            sh = shades.get(rk, ['#fff']*4)
            html_d += f'<tr><td style="background-color:{sh[0]}">{row["Ruolo"]}</td><td style="background-color:{sh[1]}">{row["Nome"]}</td><td style="background-color:{sh[2]}">{int(row["Prezzo_N"])}</td><td style="background-color:{sh[3]}">{int(row["Quotazione"])}</td></tr>'
        st.markdown(html_d + '</tbody></table>', unsafe_allow_html=True)

# TAB VINCOLI
with t[3]:
    st.subheader("📅 VINCOLI PLURIENNALI")
    if f_vn is not None:
        st.table(f_vn[['Squadra', 'Giocatore', 'Tot_Vincolo']].sort_values('Tot_Vincolo', ascending=False))

# TAB SCAMBI
with t[4]:
    st.subheader("🔄 SIMULATORE SCAMBI")
    # (Logica Golden Scambi già confermata)

# TAB TAGLI
with t[5]:
    st.subheader("✂️ GESTIONE TAGLI")
    sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="st_taglio")
    gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N']==sq_t]['Nome'].tolist())
    if gt:
        info_g = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt)].iloc[0]
        val_v = f_vn[(f_vn['Sq_N'] == sq_t) & (f_vn['Giocatore_Match'] == super_clean(gt))]['Tot_Vincolo'].sum() if f_vn is not None else 0
        rimborso = round((info_g['Prezzo_N'] + val_v) * 0.6, 1)
        st.markdown(f'<div class="cut-box"><div class="cut-player-name">{gt}</div><div style="font-size:2.8em; color:#d32f2f;">RIMBORSO: {rimborso:g}</div></div>', unsafe_allow_html=True)

# TAB MERCATO (RIPRISTINATA)
with t[6]:
    st.subheader("🚀 MERCATO CESSIONI")
    if not df_mercato.empty:
        st.table(df_mercato)
    else:
        st.info("Nessuna cessione registrata nel file CSV.")
