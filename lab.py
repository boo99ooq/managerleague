import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaLAB - Test Area", layout="wide", initial_sidebar_state="expanded")

# CSS AGGIORNATO (Bordo scuro completo e ombra)
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] * { font-weight: 900 !important; }
    .player-card { 
        padding: 12px; 
        border-radius: 10px; 
        margin-bottom: 12px; 
        border: 3px solid #333; 
        box-shadow: 4px 4px 8px rgba(0,0,0,0.2); 
        color: black; 
    }
    .patrimonio-box { 
        background-color: #f0f2f6; 
        padding: 15px; 
        border-radius: 10px; 
        border: 3px solid #1a73e8; 
        text-align: center; 
    }
    .refund-box { 
        background-color: #e8f5e9; 
        padding: 15px; 
        border-radius: 10px; 
        border: 3px solid #2e7d32; 
        color: #1b5e20; 
        margin-bottom: 10px; 
        box-shadow: 3px 3px 6px rgba(0,0,0,0.1);
    }
    .cut-box { 
        background-color: #f8f9fa; 
        padding: 20px; 
        border-radius: 10px; 
        border: 3px solid #ff4b4b; 
        color: #1a1a1a; 
    }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO ---
def super_clean_match(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items():
        name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    mapping = {
        'ZAMBO ANGUISSA': 'ANGUISSA', 'MARTINEZ L.': 'LAUTARO', 
        'PAZ N.': 'NICO PAZ', 'CASTELLANOS T.': 'CASTELLANOS',
        'MARTINELLI T.': 'MARTINELLI'
    }
    if name in mapping: return mapping[name]
    return re.sub(r'\s[A-Z]\.$', '', name)

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x': return 0.0
    try: return float(str(val).replace(',', '.'))
    except: return 0.0

def clean_string(s):
    if pd.isna(s): return None
    s_str = str(s).strip()
    if "*" in s_str or ":" in s_str or s_str == "" or "RIEPILOGO" in s_str: return None
    return s_str.upper()

def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True, encoding='latin1')
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Match_Nome'] = df['Nome'].apply(super_clean_match)
            return df[['Match_Nome', 'Qt.A']].rename(columns={'Qt.A': 'Quotazione'})
        return df.dropna(how='all')
    except: return None

# --- CARICAMENTO DATI ---
f_sc, f_pt, f_rs, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# --- ELABORAZIONE INIZIALE ---
rimborsi_squadre = {}

if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].apply(clean_string).replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean_match)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    v_cols = [c for c in f_vn.columns if '202' in c]
    f_vn['Sq_N'] = f_vn['Squadra'].apply(clean_string).replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# --- MAIN APP ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🆕 **MERCATO GENNAIO**"])

# --- TAB 6: MERCATO GENNAIO ---
with t[6]:
    st.subheader("🚀 **CALCOLO RIMBORSI CALCIOMERCATO ESTERO**")
    st.info("Regola: 50% di (Quotazione + Prezzo Asta) + 100% dei Vincoli pagati.")
    partenti = st.multiselect("**SELEZIONA I GIOCATORI USCITI:**", sorted(f_rs['Nome'].unique()) if f_rs is not None else [], key="mercato_lab")
    
    if partenti:
        dati_per_tabella = []
        for nome in partenti:
            info = f_rs[f_rs['Nome'] == nome].iloc[0]
            sq = info['Squadra_N']
            p_asta = info['Prezzo_N']
            quot = info['Quotazione']
            v_match = f_vn[f_vn['Giocatore_Match'] == super_clean_match(nome)] if f_vn is not None else pd.DataFrame()
            vv = v_match['Tot_Vincolo'].iloc[0] if not v_match.empty else 0
            rimborso = ((p_asta + quot) * 0.5) + vv
            rimborsi_squadre[sq] = rimborsi_squadre.get(sq, 0) + rimborso
            dati_per_tabella.append({"GIOCATORE": nome, "SQUADRA": sq, "ASTA": p_asta, "QUOT.": quot, "VINCOLO": vv, "RIMBORSO": rimborso})
        
        st.markdown("### 📋 DETTAGLIO PER GIOCATORE")
        st.dataframe(pd.DataFrame(dati_per_tabella).style.format({"ASTA":"{:g}", "QUOT.":"{:g}", "VINCOLO":"{:g}", "RIMBORSO":"{:g}"}), use_container_width=True, hide_index=True)
        
        st.markdown("### 💰 TOTALE RECUPERATO PER SQUADRA")
        df_riepilogo = pd.DataFrame(list(rimborsi_squadre.items()), columns=['SQUADRA', 'TOTALE']).sort_values('TOTALE', ascending=False)
        cols = st.columns(4)
        for i, (index, row) in enumerate(df_riepilogo.iterrows()):
            with cols[i % 4]:
                st.markdown(f"""<div class="refund-box"><small>{row['SQUADRA']}</small><br><b>+{int(row['TOTALE'])} crediti</b></div>""", unsafe_allow_html=True)
        st.dataframe(df_riepilogo.style.format({"TOTALE": "{:g}"}).background_gradient(cmap='Greens'), use_container_width=True, hide_index=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 **RICERCA GIOCATORE**")
    if f_rs is not None:
        scelte = st.multiselect("**CERCA NELLA LEGA**", sorted(f_rs['Nome'].unique()))
        for n in scelte:
            dr = f_rs[f_rs['Nome'] == n].iloc[0]
            v_match = f_vn[f_vn['Giocatore_Match'] == super_clean_match(n)] if f_vn is not None else pd.DataFrame()
            vv = v_match['Tot_Vincolo'].iloc[0] if not v_match.empty else 0
            r = str(dr['Ruolo']).upper()
            bg = '#FCE4EC' if 'POR' in r else '#E8F5E9' if 'DIF' in r else '#E3F2FD' if 'CEN' in r else '#FFFDE7' if 'ATT' in r else '#f1f3f4'
            st.markdown(f'<div class="player-card" style="background-color: {bg};"><b>{n}</b> ({dr["Squadra_N"]})<br>ASTA: {int(dr["Prezzo_N"])} | VINC: {int(vv)}<br>QUOT: {int(dr["Quotazione"])}</div>', unsafe_allow_html=True)

# --- TAB 1: BUDGET (Dinamico) ---
with t[1]:
    if f_rs is not None:
        st.subheader("💰 **BUDGET E PATRIMONIO DINAMICO**")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI DISPONIBILI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO MERCATO'] = bu['Squadra_N'].map(rimborsi_squadre).fillna(0)
        
        voci_disp = ['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISPONIBILI', 'RECUPERO MERCATO']
        voci_sel = st.multiselect("Seleziona voci patrimonio:", options=voci_disp, default=voci_disp)
        
        bu['PATRIMONIO TOTALE'] = bu[voci_sel].sum(axis=1) if voci_sel else 0
        if voci_sel: st.bar_chart(bu.set_index("Squadra_N")[voci_sel])
        
        col_mostra = ['Squadra_N'] + voci_sel + ['PATRIMONIO TOTALE']
        st.dataframe(bu[col_mostra].sort_values("PATRIMONIO TOTALE", ascending=False).style\
            .background_gradient(cmap='YlOrRd', subset=['PATRIMONIO TOTALE'])\
            .format({c: "{:g}" for c in bu.columns if c != 'Squadra_N'}), hide_index=True, use_container_width=True)

# --- TAB 0: CLASSIFICHE (FIXED FORMAT ERROR) ---
with t[0]:
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 **CLASSIFICA PUNTI**")
            # Forza la conversione a numero per evitare il ValueError del formattatore
            f_pt['Punti Totali'] = pd.to_numeric(f_pt['Punti Totali'], errors='coerce').fillna(0)
            st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali']].sort_values('Posizione').style\
                .background_gradient(subset=['Punti Totali'], cmap='YlGn')\
                .format({"Punti Totali": "{:g}"}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ **SCONTRI DIRETTI**")
            f_sc['Punti'] = pd.to_numeric(f_sc['Punti'], errors='coerce').fillna(0)
            st.dataframe(f_sc[['Posizione','Giocatore','Punti']].sort_values('Posizione').style\
                .background_gradient(subset=['Punti'], cmap='Blues')\
                .format({"Punti": "{:g}"}), hide_index=True, use_container_width=True)

with t[2]: # ROSE
    if f_rs is not None:
        sq = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="rose_sel")
        df_sq = f_rs[f_rs['Squadra_N'] == sq][['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']]
        def color_ruoli(row):
            r = str(row['Ruolo']).upper()
            bg = '#FCE4EC' if 'POR' in r else '#E8F5E9' if 'DIF' in r else '#E3F2FD' if 'CEN' in r else '#FFFDE7' if 'ATT' in r else '#FFFFFF'
            return [f'background-color: {bg}; color: black; font-weight: 900;'] * len(row)
        st.dataframe(df_sq.style.apply(color_ruoli, axis=1).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 **VINCOLI**")
        f_vn['Tot_Vincolo'] = pd.to_numeric(f_vn['Tot_Vincolo'], errors='coerce').fillna(0)
        st.dataframe(f_vn[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False).style\
            .background_gradient(subset=['Tot_Vincolo'], cmap='Purples')\
            .format({"Tot_Vincolo":"{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI
    st.subheader("🔄 **SCAMBI**")
    if f_rs is not None:
        c1, c2 = st.columns(2)
        lista_sq = sorted(f_rs['Squadra_N'].unique())
        with c1: sa = st.selectbox("SQUADRA A", lista_sq, key="sa"); ga = st.multiselect("ESCONO DA A", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist())
        with c2: sb = st.selectbox("SQUADRA B", sorted([s for s in lista_sq if s != sa]), key="sb"); gb = st.multiselect("ESCONO DA B", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist())
        if ga and gb:
            def get_i(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
                v_row = f_vn[f_vn['Giocatore_Match']==super_clean_match(n)] if f_vn is not None else pd.DataFrame()
                v = v_row['Tot_Vincolo'].iloc[0] if not v_row.empty else 0
                return {'t': p + v, 'v': v}
            dict_a = {n: get_i(n) for n in ga}; dict_b = {n: get_i(n) for n in gb}
            tot_a, tot_b = sum(d['t'] for d in dict_a.values()), sum(d['t'] for d in dict_b.values()); nuovo_tot = round((tot_a + tot_b) / 2)
            st.divider(); res_a, res_b = st.columns(2)
            with res_a:
                for n, info in dict_b.items():
                    peso = info['t']/tot_b if tot_b > 0 else 1/len(gb)
                    st.markdown(f'<div class="player-card" style="background-color: #e3f2fd;"><b>{n}</b><br>VAL: <b>{int(max(0, round(peso*nuovo_tot)-info["v"]))}</b></div>', unsafe_allow_html=True)
            with res_b:
                for n, info in dict_a.items():
                    peso = info['t']/tot_a if tot_a > 0 else 1/len(ga)
                    st.markdown(f'<div class="player-card" style="background-color: #fbe9e7;"><b>{n}</b><br>VAL: <b>{int(max(0, round(peso*nuovo_tot)-info["v"]))}</b></div>', unsafe_allow_html=True)

with t[5]: # TAGLI
    st.subheader("✂️ **TAGLI**")
    if f_rs is not None:
        sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="sqt"); gioc_t = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist())
        if gioc_t:
            v_p = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gioc_t)]['Prezzo_N'].iloc[0]
            v_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(gioc_t)] if f_vn is not None else pd.DataFrame()
            v_v = v_m['Tot_Vincolo'].iloc[0] if not v_m.empty else 0
            st.markdown(f'<div class="cut-box"><h3>💰 RIMBORSO: {int(round((v_p + v_v) * 0.6))} CREDITI</h3></div>', unsafe_allow_html=True)
