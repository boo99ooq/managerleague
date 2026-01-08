import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden Ultimate V4.2", layout="wide", initial_sidebar_state="expanded")

# --- BLOCCO CSS DEFINITIVO (Headers Blindati, Neretto 900 e Allineamento) ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, p, div, span, label { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    
    /* Tabelle HTML Custom (Senza indici, Headers Bold/Maiuscoli) */
    .golden-table {
        width: 100%; border-collapse: collapse; margin: 10px 0;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); border: 2px solid #333;
    }
    .golden-table th {
        padding: 12px 15px; font-weight: 900 !important; text-transform: uppercase !important;
        border: 2px solid #333; text-align: center; background-color: #f0f2f6; color: #000;
    }
    .golden-table td {
        padding: 10px 15px; border: 1px solid #ddd; text-align: center; font-weight: 900 !important;
    }

    /* Card Statistiche */
    .stat-card { 
        background-color: #f8f9fa; padding: 15px; border-radius: 10px; 
        border: 3px solid #333; text-align: center; box-shadow: 4px 4px 0px #333; 
    }
    
    /* Box Mercato Pastello */
    .refund-box-pastello {
        padding: 15px; border-radius: 12px; border: 3px solid #333; text-align: center;
        min-height: 130px; box-shadow: 4px 4px 0px #333; margin-bottom: 15px;
    }
    .bg-azzurro { background-color: #E3F2FD !important; } .bg-verde { background-color: #E8F5E9 !important; }
    .bg-rosa { background-color: #FCE4EC !important; } .bg-giallo { background-color: #FFFDE7 !important; }
    .bg-arancio { background-color: #FFF3E0 !important; } .bg-viola { background-color: #F3E5F5 !important; }

    /* Status Mercato */
    .status-ufficiale { color: white !important; background-color: #2e7d32; padding: 3px 8px; border-radius: 5px; }
    .status-probabile { color: white !important; background-color: #ed6c02; padding: 3px 8px; border-radius: 5px; }
    
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); background-color: white; }
    .punto-incontro-box { background-color: #fff3e0; padding: 10px 30px; border-radius: 15px; border: 3px solid #ff9800; text-align: center; margin: 10px auto; width: fit-content; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def to_num(val):
    if pd.isna(val): return 0.0
    s = str(val).replace('€', '').strip()
    if s == '' or s == '-' or s.lower() == 'x': return 0.0
    if ',' in s: s = s.replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

def super_clean(name):
    if not isinstance(name, str): return ""
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

def normalize_ruolo_v4(row):
    """Logica Giovani: Miretti/Gnonto ecc. hanno ruolo 'G' o 'Giovani'"""
    r = str(row.get('Ruolo', '')).upper().strip()
    p = to_num(row.get('Prezzo', 1))
    if 'GIOVANI' in r or r == 'G' or p == 0: return 'GIO'
    if r in ['P', 'POR']: return 'POR'
    if r in ['D', 'DIF']: return 'DIF'
    if r in ['C', 'CEN']: return 'CEN'
    if r in ['A', 'ATT']: return 'ATT'
    return r

# --- CARICAMENTO DATI ---
def load_all():
    def ld_std(f):
        if not os.path.exists(f): return None
        df = pd.read_csv(f, encoding='latin1', engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df

    f_sc, f_pt, f_vn = ld_std("scontridiretti.csv"), ld_std("classificapunti.csv"), ld_std("vincoli.csv")
    f_rs_raw = ld_std("rose_complete.csv")
    
    if f_rs_raw is not None:
        map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}
        c_r_rs = next((c for c in f_rs_raw.columns if c.upper() in ['RUOLO', 'R']), 'Ruolo')
        c_p_rs = next((c for c in f_rs_raw.columns if c.upper() in ['PREZZO', 'P']), 'Prezzo')
        
        f_rs_raw['Squadra_N'] = f_rs_raw['Fantasquadra'].str.upper().str.strip().replace(map_n)
        f_rs_raw['Match_Nome'] = f_rs_raw['Nome'].apply(super_clean)
        f_rs_raw['Prezzo_N'] = f_rs_raw[c_p_rs].apply(to_num)
        f_rs_raw['Ruolo_N'] = f_rs_raw.apply(lambda x: normalize_ruolo_v4({'Ruolo': x[c_r_rs], 'Prezzo': x[c_p_rs]}), axis=1)
        
        # Ordine P-D-C-A-G
        rank_map = {'POR':0, 'DIF':1, 'CEN':2, 'ATT':3, 'GIO':4}
        f_rs_raw['Ruolo_Rank'] = f_rs_raw['Ruolo_N'].map(rank_map).fillna(99)

        # Quotazioni e Ferguson
        f_qt = ld_std("quotazioni.csv")
        if f_qt is not None:
            c_n_qt = next((c for c in f_qt.columns if c.upper() in ['NOME', 'CALCIATORE']), 'Nome')
            c_r_qt = next((c for c in f_qt.columns if c.upper() in ['RUOLO', 'R', 'POS']), 'Ruolo')
            c_v_qt = next((c for c in f_qt.columns if 'QT' in c.upper() or 'VAL' in c.upper()), None)
            
            if c_v_qt:
                f_qt['Match_Nome'] = f_qt[c_n_qt].apply(super_clean)
                f_qt['Ruolo_QT_Norm'] = f_qt[c_r_qt].apply(lambda x: normalize_ruolo_v4({'Ruolo':x, 'Prezzo':10}))
                f_rs_raw['Ruolo_Merge'] = f_rs_raw[c_r_rs].apply(lambda x: normalize_ruolo_v4({'Ruolo':x, 'Prezzo':10}))
                
                f_rs_raw = pd.merge(f_rs_raw, f_qt[['Match_Nome', 'Ruolo_QT_Norm', c_v_qt]], 
                                  left_on=['Match_Nome', 'Ruolo_Merge'], 
                                  right_on=['Match_Nome', 'Ruolo_QT_Norm'], how='left')
                f_rs_raw['Quotazione'] = f_rs_raw[c_v_qt].apply(to_num)
        else: f_rs_raw['Quotazione'] = 0
    
    if f_vn is not None:
        f_vn['Sq_N'] = f_vn['Squadra'].str.upper().str.strip().replace(map_n)
        f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean)
        v_cols = [c for c in f_vn.columns if '202' in c]
        for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
        f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
        f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

    return f_sc, f_pt, f_rs_raw, f_vn

f_sc, f_pt, f_rs, f_vn = load_all()
FILE_DB = "mercatone_gennaio.csv"
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 **RICERCA CALCIATORE**")
    if f_rs is not None:
        cerca = st.multiselect("**CERCA NELLA LEGA**", sorted(f_rs['Nome'].unique()))
        for n in cerca:
            d = f_rs[f_rs['Nome'] == n].iloc[0]
            st.markdown(f'<div class="player-card"><b>{n}</b> ({d["Squadra_N"]})<br>ASTA: {int(d["Prezzo_N"])} | QUOT: {int(d.get("Quotazione",0))}</div>', unsafe_allow_html=True)

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 PUNTI")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N']].style.set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ SCONTRI")
            st.dataframe(f_sc[['Posizione','Giocatore','Punti']].style.set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        st.subheader("💰 **SITUAZIONE PATRIMONIALE**")
        rim_u = df_mercato[df_mercato['STATO'] == 'UFFICIALE'].groupby('SQUADRA')['TOTALE'].sum().to_dict()
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO'] = bu['Squadra_N'].map(rim_u).fillna(0)
        sel = st.multiselect("**VOCI DA SOMMARE:**", ['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI', 'RECUPERO'], default=['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI', 'RECUPERO'])
        if sel:
            bu['TOTALE'] = bu[sel].sum(axis=1)
            st.dataframe(bu[['Squadra_N'] + sel + ['TOTALE']].sort_values('TOTALE', ascending=False).style.set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

with t[2]: # ROSE (GOLDEN UI)
    if f_rs is not None:
        sq_r = st.selectbox("**SELEZIONA SQUADRA**", sorted(f_rs['Squadra_N'].unique()), key="sq_rose_main")
        df_team = f_rs[f_rs['Squadra_N'] == sq_r].copy()
        
        # 1. Metric Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card">👥 TOTALI<br><b style="font-size:1.5em;">{len(df_team)}</b></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="border-color:#1a73e8;">💰 ASTA<br><b style="font-size:1.5em; color:#1a73e8;">{int(df_team["Prezzo_N"].sum())}</b></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card" style="border-color:#2e7d32;">📈 QUOT.<br><b style="font-size:1.5em; color:#2e7d32;">{int(df_team["Quotazione"].sum())}</b></div>', unsafe_allow_html=True)
        with c4: 
            n_gio = len(df_team[df_team['Ruolo_N'] == 'GIO'])
            st.markdown(f'<div class="stat-card" style="border-color:#9c27b0;">👶 GIOVANI<br><b style="font-size:1.5em; color:#9c27b0;">{n_gio}</b></div>', unsafe_allow_html=True)

        # 2. Tabella Ripartizione (HTML)
        st.write("---"); st.markdown("#### 📊 RIPARTIZIONE PER RUOLO")
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

        # 3. Tabella Dettaglio (HTML)
        st.write("---"); st.markdown(f"#### 🏃 DETTAGLIO COMPLETO: {sq_r}")
        pal_s = {'POR':['#FCE4EC','#F8BBD0','#F48FB1','#F06292'], 'DIF':['#E8F5E9','#C8E6C9','#A5D6A7','#81C784'], 'CEN':['#E3F2FD','#BBDEFB','#90CAF9','#64B5F6'], 'ATT':['#FFFDE7','#FFF9C4','#FFF59D','#FFF176'], 'GIO':['#F3E5F5','#E1BEE7','#CE93D8','#AB47BC']}
        html_d = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>NOME</th><th>PREZZO</th><th>QUOT</th></tr></thead><tbody>'
        for _, row in df_team.sort_values(['Ruolo_Rank', 'Prezzo_N'], ascending=[True, False]).iterrows():
            sh = pal_s.get(row['Ruolo_N'], ['#fff']*4)
            html_d += f'<tr><td style="background-color:{sh[0]}">{row["Ruolo"]}</td><td style="background-color:{sh[1]}">{row["Nome"]}</td><td style="background-color:{sh[2]}">{int(row["Prezzo_N"])}</td><td style="background-color:{sh[3]}">{int(row["Quotazione"])}</td></tr>'
        st.markdown(html_d + '</tbody></table>', unsafe_allow_html=True)

with t[3]: # VINCOLI
    if f_vn is not None:
        st.subheader("📅 DETTAGLIO VINCOLI")
        sq_v = st.selectbox("**SQUADRA**", ["TUTTE"] + sorted(f_vn['Sq_N'].unique()))
        df_v = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.dataframe(df_v[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].style.set_properties(**{'font-weight': '900'}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI ANALITICI
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
                for n, i in db.items():
                    nv = round((i['t']/tb)*nt) if tb>0 else nt
                    st.markdown(f'<div class="player-card" style="background-color:#e3f2fd; border:3px solid #1e88e5;"><b>{n}</b><br><small>NUOVO: {max(0, nv-int(i["v"])):g}+{i["v"]:g} (V) | ANTE: {i["t"]:g}</small></div>', unsafe_allow_html=True)
            with rb:
                for n, i in da.items():
                    nv = round((i['t']/ta)*nt) if ta>0 else nt
                    st.markdown(f'<div class="player-card" style="background-color:#fbe9e7; border:3px solid #e53935;"><b>{n}</b><br><small>NUOVO: {max(0, nv-int(i["v"])):g}+{i["v"]:g} (V) | ANTE: {i["t"]:g}</small></div>', unsafe_allow_html=True)

with t[5]: # TAGLI
    if f_rs is not None:
        st.subheader("✂️ TAGLI")
        sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="st_t")
        gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N']==sq_t]['Nome'].tolist())
        if gt:
            v_a = f_rs[(f_rs['Squadra_N']==sq_t)&(f_rs['Nome']==gt)]['Prezzo_N'].iloc[0]
            vv = f_vn[f_vn['Giocatore_Match']==super_clean(gt)]['Tot_Vincolo'].sum() if f_vn is not None else 0
            st.markdown(f'<div class="stat-card" style="border-color:#ff4b4b;"><h3>{gt}</h3>RIMBORSO: <b>{round((v_a+vv)*0.6):g}</b><br><small>ASTA: {v_a:g} | VINC: {vv:g}</small></div>', unsafe_allow_html=True)

with t[6]: # MERCATO PASTELLO
    st.subheader("🚀 MERCATO")
    with st.expander("➕ AGGIUNGI CESSIONE"):
        sc = st.selectbox("Calciatore:", [""] + sorted(f_rs['Nome'].unique()))
        if st.button("INSERISCI") and sc != "":
            info = f_rs[f_rs['Nome'] == sc].iloc[0]
            vv_m = f_vn[f_vn['Giocatore_Match']==super_clean(sc)]['Tot_Vincolo'].sum() if f_vn is not None else 0
            nuova = pd.DataFrame([{"GIOCATORE": sc, "SQUADRA": info['Squadra_N'], "TOTALE": ((info['Prezzo_N'] + info['Quotazione'])*0.5)+vv_m, "STATO": "PROBABILE"}])
            df_mercato = pd.concat([df_mercato, nuova], ignore_index=True); df_mercato.to_csv(FILE_DB, index=False); st.rerun()
    if not df_mercato.empty:
        for idx, row in df_mercato.iterrows():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            with c1: st.write(f"**{row['GIOCATORE']}**")
            with c2: st.write(f"RIMB: {row['TOTALE']:g}")
            with c3: st.markdown(f"<span class='{'status-ufficiale' if row['STATO']=='UFFICIALE' else 'status-probabile'}'>{row['STATO']}</span>", unsafe_allow_html=True)
            with c4:
                if row['STATO']=="PROBABILE" and st.button("✅", key=f"u_{idx}"):
                    df_mercato.at[idx, 'STATO']="UFFICIALE"; df_mercato.to_csv(FILE_DB, index=False); st.rerun()
                if st.button("🗑️", key=f"d_{idx}"):
                    df_mercato = df_mercato.drop(idx); df_mercato.to_csv(FILE_DB, index=False); st.rerun()
        st.write("---"); st.markdown("### 💰 RECUPERO CREDITI")
        colori = ["bg-azzurro", "bg-verde", "bg-rosa", "bg-giallo", "bg-arancio", "bg-viola"]
        sq_m = df_mercato.groupby(['SQUADRA','STATO'])['TOTALE'].sum().unstack(fill_value=0)
        if 'UFFICIALE' not in sq_m: sq_m['UFFICIALE'] = 0
        if 'PROBABILE' not in sq_m: sq_m['PROBABILE'] = 0
        sq_m['TOT'] = sq_m['UFFICIALE'] + sq_m['PROBABILE']
        cols = st.columns(4)
        for i, (sn, d) in enumerate(sq_m.sort_values('TOT', ascending=False).iterrows()):
            with cols[i%4]: st.markdown(f'<div class="refund-box-pastello {colori[i%len(colori)]}">{sn}<br><b>+{d["TOT"]:g}</b><hr><small>Uff: {d["UFFICIALE"]:g} | Prob: {d["PROBABILE"]:g}</small></div>', unsafe_allow_html=True)
