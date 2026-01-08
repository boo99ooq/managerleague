import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V4.2", layout="wide", initial_sidebar_state="expanded")

# --- CSS INTEGRATO (Neretto 900 + Design Premium Roseagg + Box Golden) ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, p, div, span, label { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .stat-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 3px solid #333; text-align: center; box-shadow: 4px 4px 0px #333; }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; }
    .punto-incontro-box { background-color: #fff3e0; padding: 10px 30px; border-radius: 15px; border: 3px solid #ff9800; text-align: center; margin: 10px auto; width: fit-content; }
    .cut-box { background-color: #fdfdfd; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; text-align: center; }
    .cut-player-name { font-size: 3.5em; color: #d32f2f; text-transform: uppercase; line-height: 1; margin-bottom: 10px; }
    
    .golden-table { width: 100%; border-collapse: collapse; margin: 10px 0; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); }
    .golden-table thead tr { background-color: #f0f2f6; color: #000; }
    .golden-table th { padding: 12px 15px; border: 2px solid #333; text-align: center; text-transform: uppercase; }
    .golden-table td { padding: 10px 15px; border: 1px solid #ddd; text-align: center; }
    
    .status-ufficiale { color: #2e7d32; } .status-probabile { color: #ed6c02; }
    .refund-box { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 2px solid #333; text-align: center; min-height: 100px; }
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
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}
FILE_DB = "mercatone_gennaio.csv"

def load_all():
    if not os.path.exists("rose_complete.csv"): return None, None, None, None
    rs = pd.read_csv("rose_complete.csv", encoding='latin1', engine='python')
    rs.columns = [c.strip() for c in rs.columns]
    rs['Squadra_N'] = rs['Fantasquadra'].str.upper().str.strip().replace(map_n)
    rs['Match_Nome'] = rs['Nome'].apply(super_clean)
    rs['Prezzo_N'] = rs['Prezzo'].apply(to_num)
    rs['Ruolo_N'] = rs.apply(normalize_ruolo, axis=1)

    if os.path.exists("quotazioni.csv"):
        qt = pd.read_csv("quotazioni.csv", encoding='latin1', engine='python')
        qt.columns = [c.strip() for c in qt.columns]
        col_q = next((c for c in qt.columns if 'QT' in c.upper() or 'VAL' in c.upper()), 'Qt.A')
        qt['Match_Nome'] = qt['Nome'].apply(super_clean)
        rs = pd.merge(rs, qt[['Match_Nome', col_q]], on='Match_Nome', how='left').fillna({col_q: 0})
        rs = rs.rename(columns={col_q: 'Quotazione'}).drop_duplicates(subset=['Fantasquadra', 'Nome'])
    
    def simple_ld(f):
        if not os.path.exists(f): return None
        return pd.read_csv(f, engine='python', skip_blank_lines=True, encoding='latin1').dropna(how='all')

    vn = simple_ld("vincoli.csv")
    if vn is not None:
        vn.columns = [c.strip() for c in vn.columns]
        vn['Sq_N'] = vn['Squadra'].str.upper().str.strip().replace(map_n)
        vn['Giocatore_Match'] = vn['Giocatore'].apply(super_clean)
        v_cols = [c for c in vn.columns if '202' in c]
        for c in v_cols: vn[c] = vn[c].apply(to_num)
        vn['Tot_Vincolo'] = vn[v_cols].sum(axis=1)
        vn['Anni_T'] = vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

    return rs, vn, simple_ld("classificapunti.csv"), simple_ld("scontridiretti.csv")

f_rs, f_vn, f_pt, f_sc = load_all()
df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])
rimborsi_m = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- SIDEBAR (Ricerca Golden) ---
with st.sidebar:
    st.header("🔍 **RICERCA CALCIATORE**")
    if f_rs is not None:
        cerca_side = st.multiselect("**CERCA NELLA LEGA**", sorted(f_rs['Nome'].unique()))
        for n in cerca_side:
            d_g = f_rs[f_rs['Nome'] == n].iloc[0]
            vv = f_vn[f_vn['Giocatore_Match'] == super_clean(n)]['Tot_Vincolo'].sum() if f_vn is not None else 0
            r = str(d_g['Ruolo']).upper()
            bg_s = '#FCE4EC' if 'POR' in r else '#E8F5E9' if 'DIF' in r else '#E3F2FD' if 'CEN' in r else '#FFFDE7' if 'ATT' in r else '#f1f3f4'
            st.markdown(f'<div class="player-card" style="background-color:{bg_s};"><b>{n}</b> ({d_g["Squadra_N"]})<br>ASTA: {int(d_g["Prezzo_N"])} | VINC: {int(vv)}<br>QUOT: {int(d_g["Quotazione"])}</div>', unsafe_allow_html=True)

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

# TAB 0: CLASSIFICHE
with t[0]:
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 PUNTI")
            st.dataframe(f_pt.sort_values(f_pt.columns[0]), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ SCONTRI DIRETTI")
            st.dataframe(f_sc.sort_values(f_sc.columns[0]), hide_index=True, use_container_width=True)

# TAB 1: BUDGET DINAMICO
with t[1]:
    if f_rs is not None:
        st.subheader("💰 BUDGET E PATRIMONIO")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_s = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_s, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO'] = bu['Squadra_N'].map(rimborsi_m).fillna(0)
        bu['TOTALE'] = bu['SPESA ROSE'] + bu['SPESA VINCOLI'] + bu['CREDITI'] + bu['RECUPERO']
        st.dataframe(bu.sort_values('TOTALE', ascending=False), hide_index=True, use_container_width=True)

# TAB 2: ROSE PREMIUM
with t[2]:
    if f_rs is not None:
        sq_r = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="sq_rose_premium")
        df_team = f_rs[f_rs['Squadra_N'] == sq_r].copy()
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card">👥 TOTALI<br><b style="font-size:1.5em;">{len(df_team)}</b></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="border-color:#1a73e8;">💰 ASTA<br><b style="font-size:1.5em; color:#1a73e8;">{int(df_team["Prezzo_N"].sum())}</b></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card" style="border-color:#2e7d32;">📈 QUOT.<br><b style="font-size:1.5em; color:#2e7d32;">{int(df_team["Quotazione"].sum())}</b></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="stat-card" style="border-color:#9c27b0;">👶 GIOVANI<br><b style="font-size:1.5em; color:#9c27b0;">{len(df_team[df_team["Ruolo_N"]=="GIO"])}</b></div>', unsafe_allow_html=True)
        
        st.write("---"); st.markdown("#### 📊 RIPARTIZIONE PER RUOLO")
        riass = []
        for r in ['POR', 'DIF', 'CEN', 'ATT', 'GIO']:
            d_rep = df_team[df_team['Ruolo_N'] == r]
            riass.append({"RUOLO": r, "N°": len(d_rep), "ASTA": int(d_rep['Prezzo_N'].sum()), "VALORE": int(d_rep['Quotazione'].sum())})
        
        pal = {'POR': '#F06292', 'DIF': '#81C784', 'CEN': '#64B5F6', 'ATT': '#FFF176', 'GIO': '#AB47BC'}
        html_r = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>N°</th><th>ASTA</th><th>VALORE</th></tr></thead><tbody>'
        for row in riass:
            bg = pal.get(row['RUOLO'], '#fff'); txt = 'black' if row['RUOLO'] == 'ATT' else 'white'
            s_asta = row['ASTA'] if row['RUOLO'] != 'GIO' else "-"
            s_val = row['VALORE'] if row['RUOLO'] != 'GIO' else "-"
            html_r += f'<tr style="background-color:{bg}; color:{txt};"><td>{row["RUOLO"]}</td><td>{row["N°"]}</td><td>{s_asta}</td><td>{s_val}</td></tr>'
        st.markdown(html_r + '</tbody></table>', unsafe_allow_html=True)

        st.write("---"); st.markdown(f"#### 🏃 DETTAGLIO COMPLETO")
        shades = {'POR': ['#FCE4EC', '#F8BBD0', '#F48FB1', '#F06292'], 'DIF': ['#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784'], 'CEN': ['#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6'], 'ATT': ['#FFFDE7', '#FFF9C4', '#FFF59D', '#FFF176'], 'GIO': ['#F3E5F5', '#E1BEE7', '#CE93D8', '#AB47BC']}
        html_d = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>NOME</th><th>ASTA</th><th>QUOT</th></tr></thead><tbody>'
        for _, row in df_team.sort_values(['Ruolo_N', 'Prezzo_N'], ascending=[True, False]).iterrows():
            sh = shades.get(row['Ruolo_N'], ['#fff']*4)
            html_d += f'<tr><td style="background-color:{sh[0]}">{row["Ruolo"]}</td><td style="background-color:{sh[1]}">{row["Nome"]}</td><td style="background-color:{sh[2]}">{int(row["Prezzo_N"])}</td><td style="background-color:{sh[3]}">{int(row["Quotazione"])}</td></tr>'
        st.markdown(html_d + '</tbody></table>', unsafe_allow_html=True)

# TAB 3: VINCOLI
with t[3]:
    if f_vn is not None:
        st.subheader("📅 VINCOLI ATTIVI")
        st.dataframe(f_vn[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False), hide_index=True, use_container_width=True)

# TAB 4: SCAMBI (Formula Golden 3.2 Originale)
with t[4]:
    st.subheader("🔄 SIMULATORE SCAMBI GOLDEN")
    if f_rs is not None:
        col1, col2 = st.columns(2)
        with col1: sA = st.selectbox("SQUADRA A", sorted(f_rs['Squadra_N'].unique()), key="sA"); gA = st.multiselect("ESCONO DA A", f_rs[f_rs['Squadra_N']==sA]['Nome'].tolist())
        with col2: sB = st.selectbox("SQUADRA B", [s for s in sorted(f_rs['Squadra_N'].unique()) if s != sA], key="sB"); gB = st.multiselect("ESCONO DA B", f_rs[f_rs['Squadra_N']==sB]['Nome'].tolist())
        
        if gA and gB:
            def get_v(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
                vv = f_vn[f_vn['Giocatore_Match']==super_clean(n)]['Tot_Vincolo'].sum() if f_vn is not None else 0
                return {'t': p+vv, 'v': vv}
            da, db = {n: get_v(n) for n in gA}, {n: get_v(n) for n in gB}
            ta, tb = sum(d['t'] for d in da.values()), sum(d['t'] for d in db.values()); nt = round((ta+tb)/2); gap = ta-tb
            st.markdown(f'<div class="punto-incontro-box">GAP: {gap:g} | MEDIA: {nt:g}</div>', unsafe_allow_html=True)
            
            ra, rb = st.columns(2)
            with ra:
                for n, i in db.items():
                    ni = round((i['t']/tb)*nt) if tb>0 else nt
                    st.markdown(f'<div class="player-card" style="background-color:#e3f2fd; border:3px solid #1e88e5;"><b>{n}</b><br><small>NUOVO VALORE: {max(0, ni-int(i["v"])):g} + {i["v"]:g} (VINC) | ANTE: {i["t"]:g}</small></div>', unsafe_allow_html=True)
            with rb:
                for n, i in da.items():
                    ni = round((i['t']/ta)*nt) if ta>0 else nt
                    st.markdown(f'<div class="player-card" style="background-color:#fbe9e7; border:3px solid #e53935;"><b>{n}</b><br><small>NUOVO VALORE: {max(0, ni-int(i["v"])):g} + {i["v"]:g} (VINC) | ANTE: {i["t"]:g}</small></div>', unsafe_allow_html=True)
            
            pA = f_rs[f_rs['Squadra_N']==sA]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sA]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sA, 0)
            pB = f_rs[f_rs['Squadra_N']==sB]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sB]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sB, 0)
            cp1, cp2 = st.columns(2)
            cp1.markdown(f'<div class="patrimonio-box">NUOVO PATRIMONIO {sA}<br><h2>{int(pA + (nt-ta))}</h2><small>PRIMA: {int(pA)}</small></div>', unsafe_allow_html=True)
            cp2.markdown(f'<div class="patrimonio-box">NUOVO PATRIMONIO {sB}<br><h2>{int(pB - (nt-ta))}</h2><small>PRIMA: {int(pB)}</small></div>', unsafe_allow_html=True)

# TAB 5: TAGLI
with t[5]:
    if f_rs is not None:
        sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="sq_taglio")
        gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N']==sq_t]['Nome'].tolist())
        if gt:
            v_a = f_rs[(f_rs['Squadra_N']==sq_t) & (f_rs['Nome']==gt)]['Prezzo_N'].iloc[0]
            vv = f_vn[f_vn['Giocatore_Match']==super_clean(gt)]['Tot_Vincolo'].sum() if f_vn is not None else 0
            st.markdown(f'''<div class="cut-box"><div class="cut-player-name">{gt}</div><div style="font-size:2em; color:#2e7d32;">RIMBORSO: {round((v_a+vv)*0.6):g}</div></div>''', unsafe_allow_html=True)

# TAB 6: MERCATO
with t[6]:
    st.subheader("🚀 MERCATO CESSIONI")
    with st.expander("➕ AGGIUNGI CESSIONE"):
        sc_m = st.selectbox("Seleziona:", [""] + sorted(f_rs['Nome'].unique()) if f_rs is not None else [""])
        if st.button("INSERISCI"):
            info = f_rs[f_rs['Nome'] == sc_m].iloc[0]
            vv_m = f_vn[f_vn['Giocatore_Match'] == super_clean(sc_m)]['Tot_Vincolo'].sum() if f_vn is not None else 0
            nuova = pd.DataFrame([{"GIOCATORE": sc_m, "SQUADRA": info['Squadra_N'], "TOTALE": ((info['Prezzo_N'] + info['Quotazione'])*0.5)+vv_m, "STATO": "PROBABILE"}])
            df_mercato = pd.concat([df_mercato, nuova], ignore_index=True); df_mercato.to_csv(FILE_DB, index=False); st.rerun()
    
    if not df_mercato.empty:
        st.write("---")
        sq_m = df_mercato.groupby('SQUADRA')['TOTALE'].sum().sort_values(ascending=False)
        cols = st.columns(4)
        for i, (sq_n, t_n) in enumerate(sq_m.items()):
            with cols[i % 4]: st.markdown(f'<div class="refund-box"><small>{sq_n}</small><br><b>+{t_n:g}</b></div>', unsafe_allow_html=True)
