import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V4.5", layout="wide", initial_sidebar_state="expanded")

# --- BLOCCO CSS DEFINITIVO (Neretto Totale, Gradienti e Tabelle) ---
st.markdown("""
<style>
    /* 1. FORZA NERETTO 900 OVUNQUE */
    html, body, [data-testid="stAppViewContainer"] *, p, div, span, label, table, td, th, .stMarkdown { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    
    /* 2. TABELLE HTML CUSTOM (Usate in Rose) */
    .golden-table { width: 100%; border-collapse: collapse; margin: 10px 0; border: 3px solid #333; }
    .golden-table th { padding: 12px; border: 2px solid #333; background-color: #f0f2f6; text-transform: uppercase; font-weight: 900 !important; }
    .golden-table td { padding: 10px; border: 1px solid #333; text-align: center; font-weight: 900 !important; }

    /* 3. GRADIENTI SOFT PER LE TABELLE STREAMLIT */
    [data-testid="stMetric"] { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border: 2px solid #333; border-radius: 10px; padding: 10px; }
    
    .grad-blue { background: linear-gradient(135deg, #e0f2fe 0%, #f1f5f9 100%); border: 3px solid #333; border-radius: 15px; padding: 20px; margin-bottom: 20px; }
    .grad-green { background: linear-gradient(135deg, #f0fdf4 0%, #fefce8 100%); border: 3px solid #333; border-radius: 15px; padding: 20px; margin-bottom: 20px; }

    /* 4. COMPONENTI GOLDEN */
    .stat-card { background-color: #fff; padding: 15px; border-radius: 10px; border: 3px solid #333; text-align: center; box-shadow: 4px 4px 0px #333; }
    .cut-box { background-color: #fff; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; text-align: center; }
    .cut-player-name { font-size: 3.5em; color: #d32f2f; text-transform: uppercase; line-height: 1; }
    .punto-incontro-box { background-color: #fff3e0; padding: 10px 30px; border-radius: 15px; border: 3px solid #ff9800; text-align: center; margin: 10px auto; width: fit-content; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO (LOGICA GOLDEN) ---
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

def normalize_ruolo(row):
    r = str(row['Ruolo']).upper().strip()
    p = to_num(row['Prezzo'])
    if 'GIOVANI' in r or r == 'G' or p == 0: return 'GIO'
    if r in ['P', 'POR', 'PORTIERE']: return 'POR'
    if r in ['D', 'DIF', 'DIFENSORE']: return 'DIF'
    if r in ['C', 'CEN', 'CENTROCAMPISTA']: return 'CEN'
    if r in ['A', 'ATT', 'ATTACCANTE']: return 'ATT'
    return r

# --- CARICAMENTO DATI ---
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS"}

def load_all():
    if not os.path.exists("rose_complete.csv"): return None, None, None, None
    rs = pd.read_csv("rose_complete.csv", encoding='latin1', engine='python')
    rs['Squadra_N'] = rs['Fantasquadra'].str.upper().str.strip().replace(map_n)
    rs['Match_Nome'] = rs['Nome'].apply(super_clean)
    rs['Prezzo_N'] = rs['Prezzo'].apply(to_num)
    rs['Ruolo_N'] = rs.apply(normalize_ruolo, axis=1)

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

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**"])

# TAB ROSE (Trapiantata da roseagg.py)
with t[2]:
    if f_rs is not None:
        sq_r = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()))
        df_team = f_rs[f_rs['Squadra_N'] == sq_r].copy()
        
        # 1. Box Statistiche
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card">👥 GIOCATORI<br><h2>{len(df_team)}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card">💰 ASTA<br><h2>{int(df_team["Prezzo_N"].sum())}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card">📈 VALORE<br><h2>{int(df_team["Quotazione"].sum())}</h2></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="stat-card">👶 GIOVANI<br><h2>{len(df_team[df_team["Ruolo_N"]=="GIO"])}</h2></div>', unsafe_allow_html=True)

        # 2. Tabella Riassuntiva (Stile roseagg.py)
        st.write("---"); st.markdown("#### 📊 RIASSUNTO REPARTI")
        riass = []
        for r in ['POR', 'DIF', 'CEN', 'ATT', 'GIO']:
            d_rep = df_team[df_team['Ruolo_N'] == r]
            riass.append({"RUOLO": r, "N°": len(d_rep), "ASTA": int(d_rep['Prezzo_N'].sum()), "ATTUALE": int(d_rep['Quotazione'].sum())})
        
        pal = {'POR': '#F06292', 'DIF': '#81C784', 'CEN': '#64B5F6', 'ATT': '#FFF176', 'GIO': '#AB47BC'}
        html_r = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>N°</th><th>SPESA ASTA</th><th>VALORE ATTUALE</th></tr></thead><tbody>'
        for row in riass:
            bg = pal.get(row['RUOLO'], '#fff')
            html_r += f'<tr style="background-color:{bg};"><td>{row["RUOLO"]}</td><td>{row["N°"]}</td><td>{row["ASTA"]}</td><td>{row["ATTUALE"]}</td></tr>'
        st.markdown(html_r + '</tbody></table>', unsafe_allow_html=True)

        # 3. Dettaglio Completo (Con Sfumature shades)
        st.write("---"); st.markdown("#### 🏃 DETTAGLIO CALCIATORI")
        shades = {'POR': ['#FCE4EC','#F8BBD0','#F48FB1','#F06292'], 'DIF': ['#E8F5E9','#C8E6C9','#A5D6A7','#81C784'], 'CEN': ['#E3F2FD','#BBDEFB','#90CAF9','#64B5F6'], 'ATT': ['#FFFDE7','#FFF9C4','#FFF59D','#FFF176'], 'GIO': ['#F3E5F5','#E1BEE7','#CE93D8','#AB47BC']}
        html_d = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>NOME</th><th>PREZZO</th><th>QUOTAZIONE</th></tr></thead><tbody>'
        for _, row in df_team.sort_values(['Ruolo_N', 'Prezzo_N'], ascending=[True, False]).iterrows():
            sh = shades.get(row['Ruolo_N'], ['#fff']*4)
            html_d += f'<tr><td style="background-color:{sh[0]}">{row["Ruolo"]}</td><td style="background-color:{sh[1]}">{row["Nome"]}</td><td style="background-color:{sh[2]}">{int(row["Prezzo_N"])}</td><td style="background-color:{sh[3]}">{int(row["Quotazione"])}</td></tr>'
        st.markdown(html_d + '</tbody></table>', unsafe_allow_html=True)

# TAB CLASSIFICHE (Con Gradiente e Neretto)
with t[0]:
    st.markdown('<div class="grad-blue">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    if f_pt is not None:
        with col1: st.subheader("🎯 CLASSIFICA PUNTI"); st.dataframe(f_pt, hide_index=True, use_container_width=True)
    if f_sc is not None:
        with col2: st.subheader("⚔️ SCONTRI DIRETTI"); st.dataframe(f_sc, hide_index=True, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# TAB BUDGET (Con Gradiente e Neretto)
with t[1]:
    st.markdown('<div class="grad-green">', unsafe_allow_html=True)
    if f_rs is not None:
        st.subheader("💰 PATRIMONIO DINAMICO")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_s = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_s, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI_INIZ'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['PATRIMONIO_TOT'] = bu['SPESA ROSE'] + bu['SPESA VINCOLI'] + bu['CREDITI_INIZ']
        st.dataframe(bu.sort_values('PATRIMONIO_TOT', ascending=False), hide_index=True, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# TAB VINCOLI
with t[3]:
    st.subheader("📅 VINCOLI ATTIVI")
    if f_vn is not None:
        st.dataframe(f_vn[['Squadra', 'Giocatore', 'Tot_Vincolo']].sort_values('Tot_Vincolo', ascending=False), hide_index=True, use_container_width=True)

# TAB SCAMBI (Formula Complessa)
with t[4]:
    st.subheader("🔄 SIMULATORE SCAMBI GOLDEN")
    if f_rs is not None:
        c1, c2 = st.columns(2)
        with c1: sA = st.selectbox("SQUADRA A", sorted(f_rs['Squadra_N'].unique()), key="sA")
        with c2: sB = st.selectbox("SQUADRA B", [s for s in sorted(f_rs['Squadra_N'].unique()) if s != sA], key="sB")
        
        gA = st.multiselect("ESCONO DA A", f_rs[f_rs['Squadra_N']==sA]['Nome'].tolist())
        gB = st.multiselect("ESCONO DA B", f_rs[f_rs['Squadra_N']==sB]['Nome'].tolist())
        
        if gA and gB:
            def get_v(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
                vv = f_vn[f_vn['Giocatore_Match']==super_clean(n)]['Tot_Vincolo'].sum() if f_vn is not None else 0
                return {'t': p+vv, 'v': vv}
            
            da, db = {n: get_v(n) for n in gA}, {n: get_v(n) for n in gB}
            ta, tb = sum(d['t'] for d in da.values()), sum(d['t'] for d in db.values())
            nt = round((ta+tb)/2); gap = ta - tb
            
            st.markdown(f'<div class="punto-incontro-box">MEDIA: {nt:g} | GAP: {gap:g}</div>', unsafe_allow_html=True)
            ra, rb = st.columns(2)
            with ra:
                st.markdown(f"#### INTRANO IN {sA}")
                for n, i in db.items():
                    val = round((i['t']/tb)*nt) if tb>0 else nt
                    st.markdown(f'<div class="stat-card" style="border-color:#1e88e5;"><b>{n}</b><br>ASTA: {max(0, val-int(i["v"])):g} + VINC: {i["v"]:g}</div>', unsafe_allow_html=True)
            with rb:
                st.markdown(f"#### ENTRANO IN {sB}")
                for n, i in da.items():
                    val = round((i['t']/ta)*nt) if ta>0 else nt
                    st.markdown(f'<div class="stat-card" style="border-color:#e53935;"><b>{n}</b><br>ASTA: {max(0, val-int(i["v"])):g} + VINC: {i["v"]:g}</div>', unsafe_allow_html=True)

# TAB TAGLI (Super Dettagliata)
with t[5]:
    st.subheader("✂️ GESTIONE TAGLI")
    sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="sq_taglio")
    gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N']==sq_t]['Nome'].tolist())
    if gt:
        info_g = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt)].iloc[0]
        val_v = f_vn[(f_vn['Sq_N'] == sq_t) & (f_vn['Giocatore_Match'] == super_clean(gt))]['Tot_Vincolo'].sum() if f_vn is not None else 0
        rimborso = round((info_g['Prezzo_N'] + val_v) * 0.6, 1)
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="stat-card">🎭 {info_g["Ruolo"]}</div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card">💰 ASTA: {int(info_g["Prezzo_N"])}</div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card">📈 QUOT: {int(info_g["Quotazione"])}</div>', unsafe_allow_html=True)
        
        st.markdown(f'<div class="cut-box"><div class="cut-player-name">{gt}</div><div style="font-size:2.8em; color:#d32f2f;">RIMBORSO (60%): {rimborso:g}</div></div>', unsafe_allow_html=True)
