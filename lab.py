import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# CSS GOLDEN (Neretto 900 totale, Card, Box e Tabelle)
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame td, .stDataFrame th { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; color: black; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; }
    .punto-incontro-box { background-color: #fff3e0; padding: 10px 30px; border-radius: 15px; border: 3px solid #ff9800; text-align: center; margin: 10px auto; width: fit-content; }
    .cut-box { background-color: #fdfdfd; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; text-align: center; }
    .cut-player-name { font-size: 3.5em; color: #d32f2f; text-transform: uppercase; line-height: 1; margin-bottom: 10px; }
    .refund-box { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 2px solid #333; text-align: center; min-height: 120px; }
    .status-ufficiale { color: #2e7d32; } .status-probabile { color: #ed6c02; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def super_clean_match(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x' or str(val).strip() == '': return 0.0
    try:
        return float(str(val).replace(',', '.'))
    except: return 0.0

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
FILE_DB = "mercatone_gennaio.csv"

bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

if f_rs is not None:
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].str.upper().str.strip().replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean_match)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    if f_qt is not None:
        f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].str.upper().str.strip().replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    v_cols = [c for c in f_vn.columns if '202' in c]
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

# Mercato Database
if os.path.exists(FILE_DB):
    df_mercato = pd.read_csv(FILE_DB)
else:
    df_mercato = pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])
rimborsi_mercato = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- SIDEBAR RIPRISTINATA ---
with st.sidebar:
    st.header("🔍 **RICERCA CALCIATORE**")
    if f_rs is not None:
        scelte = st.multiselect("**CERCA NELLA LEGA**", sorted(f_rs['Nome'].unique()))
        for n in scelte:
            d_g = f_rs[f_rs['Nome'] == n].iloc[0]
            v_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(n)] if f_vn is not None else pd.DataFrame()
            vv = v_m['Tot_Vincolo'].iloc[0] if not v_m.empty else 0
            r = str(d_g['Ruolo']).upper()
            bg_side = '#FCE4EC' if 'POR' in r else '#E8F5E9' if 'DIF' in r else '#E3F2FD' if 'CEN' in r else '#FFFDE7' if 'ATT' in r else '#f1f3f4'
            st.markdown(f'''<div class="player-card" style="background-color: {bg_side};"><b>{n}</b> ({d_g['Squadra_N']})<br>ASTA: {int(d_g['Prezzo_N'])} | VINC: {int(vv)}<br>QUOT: {int(d_g['Quotazione'])}</div>''', unsafe_allow_html=True)

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

with t[0]: # CLASSIFICHE ORIGINALI
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 PUNTI")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N']].style.background_gradient(subset=['P_N'], cmap='YlGn').format({"P_N":"{:g}"}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ SCONTRI")
            f_sc['P_S'] = f_sc['Punti'].apply(to_num); f_sc['GF'] = f_sc['Gol Fatti'].apply(to_num); f_sc['GS'] = f_sc['Gol Subiti'].apply(to_num); f_sc['DR'] = f_sc['GF'] - f_sc['GS']
            st.dataframe(f_sc[['Posizione','Giocatore','P_S','GF','GS','DR']].style.background_gradient(subset=['P_S'], cmap='Blues').format({c: "{:g}" for c in ['P_S','GF','GS','DR']}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET DINAMICO
    if f_rs is not None:
        st.subheader("💰 BUDGET E PATRIMONIO")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO'] = bu['Squadra_N'].map(rimborsi_mercato).fillna(0)
        
        voci = ['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI', 'RECUPERO']
        sel = st.multiselect("**VOCI PATRIMONIO:**", voci, default=voci)
        bu['TOTALE'] = bu[sel].sum(axis=1) if sel else 0
        
        # FIX ValueError: formattiamo solo colonne numeriche
        num_cols = bu.select_dtypes(include=['number']).columns
        st.dataframe(bu[['Squadra_N'] + sel + ['TOTALE']].sort_values('TOTALE', ascending=False).style.background_gradient(cmap='YlOrRd', subset=['TOTALE']).format({c: "{:g}" for c in num_cols}), hide_index=True, use_container_width=True)

with t[2]: # ROSE COLORATE
    if f_rs is not None:
        c_r1, c_r2 = st.columns([1, 2])
        with c_r1: sq = st.selectbox("**SQUADRA**", ["TUTTE"] + sorted(f_rs['Squadra_N'].unique()))
        with c_r2: cerca = st.text_input("🔍 **CERCA GIOCATORE**", "").upper()
        df_r = f_rs.copy()
        if sq != "TUTTE": df_r = df_r[df_r['Squadra_N'] == sq]
        if cerca: df_r = df_r[df_r['Nome'].str.upper().str.contains(cerca, na=False)]
        
        def color_ruolo(val):
            v = str(val).upper()
            if 'POR' in v: return 'background-color: #FCE4EC'
            if 'DIF' in v: return 'background-color: #E8F5E9'
            if 'CEN' in v: return 'background-color: #E3F2FD'
            if 'ATT' in v: return 'background-color: #FFFDE7'
            return ''
        st.dataframe(df_r[['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']].style.applymap(color_ruolo, subset=['Ruolo']).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI FILTRABILI
    if f_vn is not None:
        sq_v = st.selectbox("**FILTRA SQUADRA VINCOLI**", ["TUTTE"] + sorted(f_vn['Sq_N'].unique()))
        df_v = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.dataframe(df_v[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False).style.format({"Tot_Vincolo":"{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI COMPLETI
    st.subheader("🔄 SIMULATORE SCAMBI GOLDEN")
    if f_rs is not None:
        s1, s2 = st.columns(2)
        with s1: sa = st.selectbox("SQUADRA A", sorted(f_rs['Squadra_N'].unique()), key="sa"); ga = st.multiselect("ESCONO DA A", f_rs[f_rs['Squadra_N']==sa]['Nome'].tolist())
        with s2: sb = st.selectbox("SQUADRA B", [s for s in sorted(f_rs['Squadra_N'].unique()) if s != sa], key="sb"); gb = st.multiselect("ESCONO DA B", f_rs[f_rs['Squadra_N']==sb]['Nome'].tolist())
        
        if ga and gb:
            def get_v(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
                vm = f_vn[f_vn['Giocatore_Match']==super_clean_match(n)] if f_vn is not None else pd.DataFrame()
                v = vm['Tot_Vincolo'].iloc[0] if not vm.empty else 0
                return {'t': p+v, 'v': v}
            da, db = {n: get_v(n) for n in ga}, {n: get_v(n) for n in gb}
            ta, tb = sum(d['t'] for d in da.values()), sum(d['t'] for d in db.values()); nt = round((ta+tb)/2); gap = ta-tb
            st.markdown(f'<div class="punto-incontro-box">GAP: {gap:g} | MEDIA: {nt:g}</div>', unsafe_allow_html=True)
            
            r_a, r_b = st.columns(2)
            with r_a:
                for n, i in db.items():
                    ni = round((i['t']/tb)*nt) if tb>0 else nt
                    st.markdown(f'<div class="player-card" style="background-color:#e3f2fd; border:3px solid #1e88e5;"><b>{n}</b><br><small>VAL: {max(0, ni-int(i["v"])):g} + {i["v"]:g} (VINC) | ANTE: {i["t"]:g}</small></div>', unsafe_allow_html=True)
            with r_b:
                for n, i in da.items():
                    ni = round((i['t']/ta)*nt) if ta>0 else nt
                    st.markdown(f'<div class="player-card" style="background-color:#fbe9e7; border:3px solid #e53935;"><b>{n}</b><br><small>VAL: {max(0, ni-int(i["v"])):g} + {i["v"]:g} (VINC) | ANTE: {i["t"]:g}</small></div>', unsafe_allow_html=True)
            
            p_a_v = f_rs[f_rs['Squadra_N']==sa]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sa]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sa, 0)
            p_b_v = f_rs[f_rs['Squadra_N']==sb]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sb]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sb, 0)
            d_p = nt - ta
            cp1, cp2 = st.columns(2)
            cp1.markdown(f'<div class="patrimonio-box">NUOVO PATRIMONIO {sa}<br><h2>{int(p_a_v+d_p)}</h2><small>PRIMA: {int(p_a_v)}</small></div>', unsafe_allow_html=True)
            cp2.markdown(f'<div class="patrimonio-box">NUOVO PATRIMONIO {sb}<br><h2>{int(p_b_v-d_p)}</h2><small>PRIMA: {int(p_b_v)}</small></div>', unsafe_allow_html=True)

with t[5]: # TAGLI GIGANTI
    st.subheader("✂️ TAGLI GOLDEN")
    if f_rs is not None:
        sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="st_t_p")
        gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist())
        if gt:
            v_a = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt)]['Prezzo_N'].iloc[0]
            vm = f_vn[f_vn['Giocatore_Match'] == super_clean_match(gt)] if f_vn is not None else pd.DataFrame()
            vv = vm['Tot_Vincolo'].iloc[0] if not vm.empty else 0
            st.markdown(f'''<div class="cut-box"><div class="cut-player-name">{gt}</div><div style="font-size:2em; color:#2e7d32;">RIMBORSO: {round((v_a+vv)*0.6):g}</div><br>ASTA: {v_a:g} | VINCOLI: {vv:g}</div>''', unsafe_allow_html=True)

with t[6]: # MERCATO GENNAIO
    st.subheader("🚀 MERCATO CESSIONI")
    with st.expander("➕ AGGIUNGI CESSIONE"):
        sc_m = st.selectbox("Seleziona:", [""] + sorted(f_rs['Nome'].unique()) if f_rs is not None else [""])
        if st.button("INSERISCI"):
            if sc_m != "" and sc_m not in df_mercato['GIOCATORE'].values:
                info = f_rs[f_rs['Nome'] == sc_m].iloc[0]
                vm_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(sc_m)] if f_vn is not None else pd.DataFrame()
                vv_m = vm_m['Tot_Vincolo'].iloc[0] if not vm_m.empty else 0
                nuova = pd.DataFrame([{"GIOCATORE": sc_m, "SQUADRA": info['Squadra_N'], "TOTALE": ((info['Prezzo_N'] + info['Quotazione'])*0.5)+vv_m, "STATO": "PROBABILE"}])
                df_mercato = pd.concat([df_mercato, nuova], ignore_index=True); df_mercato.to_csv(FILE_DB, index=False); st.rerun()
    
    if not df_mercato.empty:
        for idx, row in df_mercato.iterrows():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            with c1: st.write(f"**{row['GIOCATORE']}** ({row['SQUADRA']})")
            with c2: st.write(f"TOT: {row['TOTALE']:g}")
            with c3: st.write(f"<span class='status-probabile'>{row['STATO']}</span>" if row['STATO']=="PROBABILE" else f"<span class='status-ufficiale'>{row['STATO']}</span>", unsafe_allow_html=True)
            with c4:
                if row['STATO'] == "PROBABILE" and st.button("✅", key=f"u_{idx}"):
                    df_mercato.at[idx, 'STATO'] = "UFFICIALE"; df_mercato.to_csv(FILE_DB, index=False); st.rerun()
                if st.button("🗑️", key=f"d_{idx}"):
                    df_mercato.drop(idx).to_csv(FILE_DB, index=False); st.rerun()
        st.write("---")
        sq_stats = df_mercato.groupby('SQUADRA')['TOTALE'].sum().sort_values(ascending=False)
        cols_m = st.columns(4)
        for i, (sq_m, t_m) in enumerate(sq_stats.items()):
            with cols_m[i % 4]: st.markdown(f'<div class="refund-box"><small>{sq_m}</small><br><b style="font-size:1.4em;">+{t_m:g}</b></div>', unsafe_allow_html=True)
