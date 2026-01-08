import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V5.1", layout="wide", initial_sidebar_state="expanded")

# --- BLOCCO CSS TOTALE (Headers, Neretto 900, Gradienti e Tabelle HTML) ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, p, div, span, label { 
        font-weight: 900 !important; color: #000 !important; 
    }
    .golden-table {
        width: 100%; border-collapse: collapse; margin: 10px 0;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); border: 2px solid #333;
    }
    .golden-table th {
        padding: 12px 15px; font-weight: 900 !important; text-transform: uppercase !important;
        border: 2px solid #333; text-align: center; background-color: #f0f2f6;
    }
    .golden-table td {
        padding: 10px 15px; border: 1px solid #ddd; text-align: center; font-weight: 900 !important;
    }
    .stat-card { 
        background-color: #f8f9fa; padding: 15px; border-radius: 10px; 
        border: 3px solid #333; text-align: center; box-shadow: 4px 4px 0px #333; 
    }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); background-color: white; }
    .refund-box-pastello { padding: 15px; border-radius: 12px; border: 3px solid #333; text-align: center; min-height: 130px; box-shadow: 4px 4px 0px #333; margin-bottom: 15px; }
    .bg-azzurro { background-color: #E3F2FD !important; } .bg-verde { background-color: #E8F5E9 !important; }
    .bg-rosa { background-color: #FCE4EC !important; } .bg-giallo { background-color: #FFFDE7 !important; }
    .bg-arancio { background-color: #FFF3E0 !important; } .bg-viola { background-color: #F3E5F5 !important; }
    .status-ufficiale { color: white !important; background-color: #2e7d32; padding: 3px 8px; border-radius: 5px; }
    .status-probabile { color: white !important; background-color: #ed6c02; padding: 3px 8px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def to_num(val):
    if pd.isna(val) or str(val).strip().lower() in ['x', '', '-']: return 0.0
    try: return float(str(val).replace('.', '').replace(',', '.'))
    except: return 0.0

def super_clean(name):
    if not isinstance(name, str): return ""
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

def normalize_ruolo_v5(row):
    r = str(row.get('Ruolo', '')).upper().strip()
    p = to_num(row.get('Prezzo', 1))
    if 'GIOVANI' in r or r == 'G' or p == 0: return 'GIO'
    if r in ['P', 'POR']: return 'POR'
    if r in ['D', 'DIF']: return 'DIF'
    if r in ['C', 'CEN']: return 'CEN'
    if r in ['A', 'ATT']: return 'ATT'
    return r

# --- CARICAMENTO DATI (Integrazione Totale lab(1) + roseagg) ---
def load_all():
    def ld_std(f):
        if not os.path.exists(f): return None
        df = pd.read_csv(f, encoding='latin1', engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df

    f_sc, f_pt, f_vn = ld_std("scontridiretti.csv"), ld_std("classificapunti.csv"), ld_std("vincoli.csv")
    f_rs = ld_std("rose_complete.csv")
    
    if f_rs is not None:
        map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}
        f_rs['Squadra_N'] = f_rs['Fantasquadra'].str.upper().str.strip().replace(map_n)
        f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean)
        f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
        f_rs['Ruolo_N'] = f_rs.apply(lambda x: normalize_ruolo_v5({'Ruolo': x['Ruolo'], 'Prezzo': x['Prezzo']}), axis=1)
        
        rank_map = {'POR':0, 'DIF':1, 'CEN':2, 'ATT':3, 'GIO':4}
        f_rs['Ruolo_Rank'] = f_rs['Ruolo_N'].map(rank_map).fillna(99)

        # FIX QUOTAZIONI: Ricerca flessibile colonne
        f_qt = ld_std("quotazioni.csv")
        if f_qt is not None:
            c_v_qt = next((c for c in f_qt.columns if any(x in c.upper() for x in ['QT', 'VAL', 'QUOT'])), None)
            c_r_qt = next((c for c in f_qt.columns if c.upper() in ['RUOLO', 'R', 'POS']), 'Ruolo')
            if c_v_qt:
                f_qt['Match_Nome'] = f_qt['Nome'].apply(super_clean)
                f_qt['Ruolo_QT_Norm'] = f_qt[c_r_qt].apply(lambda x: normalize_ruolo_v5({'Ruolo':x, 'Prezzo':10}))
                
                # Merge per Ferguson (CEN 5 vs ATT 15)
                f_rs['Ruolo_Merge'] = f_rs['Ruolo'].apply(lambda x: normalize_ruolo_v5({'Ruolo':x, 'Prezzo':10}))
                f_rs = pd.merge(f_rs, f_qt[['Match_Nome', 'Ruolo_QT_Norm', c_v_qt]], 
                              left_on=['Match_Nome', 'Ruolo_Merge'], 
                              right_on=['Match_Nome', 'Ruolo_QT_Norm'], how='left')
                f_rs['Quotazione'] = f_rs[c_v_qt].apply(to_num)
                f_rs = f_rs.drop_duplicates(subset=['Fantasquadra', 'Nome', 'Ruolo'])
            else: f_rs['Quotazione'] = 0
        else: f_rs['Quotazione'] = 0
    
    if f_vn is not None:
        f_vn['Sq_N'] = f_vn['Squadra'].str.upper().str.strip().replace(map_n)
        f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean)
        v_cols = [c for c in f_vn.columns if '202' in c]
        for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
        f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
        f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

    return f_sc, f_pt, f_rs, f_vn

f_sc, f_pt, f_rs, f_vn = load_all()
FILE_DB = "mercatone_gennaio.csv"
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])

# --- INTERFACCIA ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

with t[0]: # CLASSIFICHE (Con Gradienti)
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 PUNTI")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N']].style.set_properties(**{'font-weight': '900'}).background_gradient(subset=['P_N'], cmap='YlGn'), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ SCONTRI")
            f_sc['P_N'] = f_sc['Punti'].apply(to_num)
            st.dataframe(f_sc[['Posizione','Giocatore','Punti']].style.set_properties(**{'font-weight': '900'}).background_gradient(subset=['Punti'], cmap='Blues'), hide_index=True, use_container_width=True)

with t[1]: # BUDGET (Con Multiselect)
    if f_rs is not None:
        st.subheader("💰 PATRIMONIO")
        rim_u = df_mercato[df_mercato['STATO'] == 'UFFICIALE'].groupby('SQUADRA')['TOTALE'].sum().to_dict()
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO'] = bu['Squadra_N'].map(rim_u).fillna(0)
        sel = st.multiselect("**FILTRA VOCI:**", ['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI', 'RECUPERO'], default=['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI', 'RECUPERO'])
        if sel:
            bu['TOTALE'] = bu[sel].sum(axis=1)
            st.dataframe(bu[['Squadra_N'] + sel + ['TOTALE']].style.set_properties(**{'font-weight': '900'}).background_gradient(subset=['TOTALE'], cmap='YlOrRd').format("{:g}"), hide_index=True, use_container_width=True)

with t[2]: # ROSE (GOLDEN UI roseagg.py)
    if f_rs is not None:
        sq_r = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="sq_rose_main")
        df_team = f_rs[f_rs['Squadra_N'] == sq_r].copy()
        
        # Metric Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card">👥 TOTALI<br><b style="font-size:1.5em;">{len(df_team)}</b></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="border-color:#1a73e8;">💰 ASTA<br><b style="font-size:1.5em;">{int(df_team["Prezzo_N"].sum())}</b></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card" style="border-color:#2e7d32;">📈 QUOT.<br><b style="font-size:1.5em;">{int(df_team["Quotazione"].sum())}</b></div>', unsafe_allow_html=True)
        with c4: 
            n_gio = len(df_team[df_team['Ruolo_N'] == 'GIO'])
            st.markdown(f'<div class="stat-card" style="border-color:#9c27b0;">👶 GIOVANI<br><b style="font-size:1.5em; color:#9c27b0;">{n_gio}</b></div>', unsafe_allow_html=True)

        st.write("---"); st.markdown("#### 📊 RIPARTIZIONE")
        riass_list = []
        for r in ['POR', 'DIF', 'CEN', 'ATT', 'GIO']:
            d_rep = df_team[df_team['Ruolo_N'] == r]
            label = "GIOVANI" if r == 'GIO' else r
            riass_list.append({"RUOLO": label, "N°": len(d_rep), "ASTA": int(d_rep['Prezzo_N'].sum()) if r != 'GIO' else "-", "QUOT": int(d_rep['Quotazione'].sum()) if r != 'GIO' else "-"})
        
        pal = {'POR': '#F06292', 'DIF': '#81C784', 'CEN': '#64B5F6', 'ATT': '#FFF176', 'GIOVANI': '#AB47BC'}
        html_r = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>N°</th><th>ASTA</th><th>QUOT</th></tr></thead><tbody>'
        for row in riass_list:
            bg, txt = pal.get(row['RUOLO'], '#fff'), ('black' if row['RUOLO'] == 'ATT' else 'white')
            html_r += f'<tr style="background-color:{bg}; color:{txt};"><td>{row["RUOLO"]}</td><td>{row["N°"]}</td><td>{row["ASTA"]}</td><td>{row["QUOT"]}</td></tr>'
        st.markdown(html_r + '</tbody></table>', unsafe_allow_html=True)

        st.write("---"); st.markdown(f"#### 🏃 DETTAGLIO")
        ord_type = st.radio("**ORDINA PER:**", ["REPARTO", "PREZZO"], horizontal=True)
        df_team_s = df_team.sort_values(['Ruolo_Rank', 'Prezzo_N'], ascending=[True, False]) if "REPARTO" in ord_type else df_team.sort_values('Prezzo_N', ascending=False)
        
        pal_s = {'POR':['#FCE4EC','#F8BBD0','#F48FB1','#F06292'], 'DIF':['#E8F5E9','#C8E6C9','#A5D6A7','#81C784'], 'CEN':['#E3F2FD','#BBDEFB','#90CAF9','#64B5F6'], 'ATT':['#FFFDE7','#FFF9C4','#FFF59D','#FFF176'], 'GIO':['#F3E5F5','#E1BEE7','#CE93D8','#AB47BC']}
        html_d = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>NOME</th><th>PREZZO</th><th>QUOT</th></tr></thead><tbody>'
        for _, row in df_team_s.iterrows():
            sh = pal_s.get(row['Ruolo_N'], ['#fff']*4)
            html_d += f'<tr><td style="background-color:{sh[0]}">{row["Ruolo"]}</td><td style="background-color:{sh[1]}">{row["Nome"]}</td><td style="background-color:{sh[2]}">{int(row["Prezzo_N"])}</td><td style="background-color:{sh[3]}">{int(row["Quotazione"])}</td></tr>'
        st.markdown(html_d + '</tbody></table>', unsafe_allow_html=True)

# --- ALTRE TAB (lab(1) COMPLETE) ---
with t[3]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 VINCOLI")
        sq_v = st.selectbox("**SQUADRA**", ["TUTTE"] + sorted(f_vn['Sq_N'].unique()))
        df_v = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.dataframe(df_v[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].style.set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI
    if f_rs is not None:
        st.subheader("🔄 SIMULATORE SCAMBI")
        c_a, c_b = st.columns(2)
        with c_a: sA = st.selectbox("SQUADRA A", sorted(f_rs['Squadra_N'].unique()), key="sA"); gA = st.multiselect("ESCONO A", f_rs[f_rs['Squadra_N']==sA]['Nome'].tolist())
        with c_b: sB = st.selectbox("SQUADRA B", [s for s in sorted(f_rs['Squadra_N'].unique()) if s != sA], key="sB"); gB = st.multiselect("ESCONO B", f_rs[f_rs['Squadra_N']==sB]['Nome'].tolist())
        if gA and gB:
            def get_v(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
                vm = f_vn[f_vn['Giocatore_Match']==super_clean(n)]['Tot_Vincolo'].sum() if f_vn is not None else 0
                return {'t': p+vm, 'v': vm}
            da, db = {n: get_v(n) for n in gA}, {n: get_v(n) for n in gB}
            ta, tb = sum(i['t'] for i in da.values()), sum(i['t'] for i in db.values()); nt = round((ta+tb)/2)
            st.markdown(f'<div class="punto-incontro-box">GAP: {ta-tb:g} | MEDIA: {nt:g}</div>', unsafe_allow_html=True)
            ra, rb = st.columns(2)
            with ra:
                for n, i in db.items(): st.markdown(f'<div class="player-card"><b>{n}</b><br><small>NUOVO: {max(0, round(i["t"]/tb*nt if tb>0 else nt)-int(i["v"])):g}+{i["v"]:g}(V)</small></div>', unsafe_allow_html=True)
            with rb:
                for n, i in da.items(): st.markdown(f'<div class="player-card"><b>{n}</b><br><small>NUOVO: {max(0, round(i["t"]/ta*nt if ta>0 else nt)-int(i["v"])):g}+{i["v"]:g}(V)</small></div>', unsafe_allow_html=True)

with t[6]: # MERCATO (Box Pastello)
    st.subheader("🚀 MERCATO")
    if not df_mercato.empty:
        sq_m = df_mercato.groupby(['SQUADRA','STATO'])['TOTALE'].sum().unstack(fill_value=0)
        sq_m['TOT'] = sq_m.get('UFFICIALE',0) + sq_m.get('PROBABILE',0)
        cols = st.columns(4); colori = ["bg-azzurro", "bg-verde", "bg-rosa", "bg-giallo"]
        for i, (sn, d) in enumerate(sq_m.sort_values('TOT', ascending=False).iterrows()):
            with cols[i%4]: st.markdown(f'<div class="refund-box-pastello {colori[i%len(colori)]}">{sn}<br><b>+{d["TOT"]:g}</b><br><small>Uff: {d.get("UFFICIALE",0):g} | Prob: {d.get("PROBABILE",0):g}</small></div>', unsafe_allow_html=True)
