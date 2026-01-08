import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# CSS GOLDEN DEFINITIVO: Forza neretto 900, colori ruoli e layout box
st.markdown("""
<style>
    /* Forza il neretto 900 ovunque */
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame td, .stDataFrame th, p, div, span, label { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    /* Card Sidebar */
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    /* Box Scambi e Patrimonio */
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; }
    .punto-incontro-box { background-color: #fff3e0; padding: 10px 30px; border-radius: 15px; border: 3px solid #ff9800; text-align: center; margin: 10px auto; width: fit-content; }
    /* Box Tagli */
    .cut-box { background-color: #fdfdfd; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; text-align: center; }
    .cut-player-name { font-size: 3.5em; color: #d32f2f; text-transform: uppercase; line-height: 1; margin-bottom: 10px; }
    /* Box Mercato */
    .refund-box { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 2px solid #333; text-align: center; min-height: 120px; }
    .status-ufficiale { color: #2e7d32; } .status-probabile { color: #ed6c02; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def bold_df(df):
    """Applica il neretto direttamente alle celle del DataFrame tramite Styler"""
    return df.style.set_properties(**{'font-weight': '900', 'color': 'black'})

def super_clean_match(name):
    if not isinstance(name, str): return ""
    mappa_err = {'Ã²': 'Ò', 'Ã³': 'Ó', 'Ã¨': 'È', 'Ã©': 'É', 'Ã¹': 'Ù', 'Ã¬': 'Ì', 'Ã\x88': 'È', 'Ã\x80': 'À'}
    for err, corr in mappa_err.items(): name = name.replace(err, corr)
    name = unicodedata.normalize('NFD', name).encode('ascii', 'ignore').decode('utf-8').upper().strip()
    return re.sub(r'\s[A-Z]\.$', '', name)

def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x' or str(val).strip() == '': return 0.0
    try: return float(str(val).replace(',', '.'))
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

df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])
rimborsi_mercato = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 **RICERCA CALCIATORE**")
    if f_rs is not None:
        cerca_side = st.multiselect("**CERCA NELLA LEGA**", sorted(f_rs['Nome'].unique()))
        for n in cerca_side:
            d_g = f_rs[f_rs['Nome'] == n].iloc[0]
            v_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(n)] if f_vn is not None else pd.DataFrame()
            vv = v_m['Tot_Vincolo'].iloc[0] if not v_m.empty else 0
            r = str(d_g['Ruolo']).upper()
            bg_side = '#FCE4EC' if 'POR' in r else '#E8F5E9' if 'DIF' in r else '#E3F2FD' if 'CEN' in r else '#FFFDE7' if 'ATT' in r else '#f1f3f4'
            st.markdown(f'''<div class="player-card" style="background-color: {bg_side};"><b>{n}</b> ({d_g['Squadra_N']})<br>ASTA: {int(d_g['Prezzo_N'])} | VINC: {int(vv)}<br>QUOT: {int(d_g['Quotazione'])}</div>''', unsafe_allow_html=True)

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

with t[0]: # CLASSIFICHE COMPLETE (DETTAGLIO GOL INCLUSO)
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 PUNTI")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            f_pt['FM'] = f_pt['Media'].apply(to_num) if 'Media' in f_pt.columns else 0.0
            st.dataframe(bold_df(f_pt[['Posizione','Giocatore','P_N','FM']].sort_values('Posizione')).background_gradient(subset=['P_N','FM'], cmap='YlGn').format({"P_N":"{:g}", "FM":"{:.2f}"}), hide_index=True, use_container_width=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ SCONTRI DIRETTI")
            # Calcolo dettaglio Gol Fatti (GF), Gol Subiti (GS) e Diff Reti (DR)
            for col in ['Punti', 'Gol Fatti', 'Gol Subiti']: f_sc[col] = f_sc[col].apply(to_num)
            f_sc['DR'] = f_sc['Gol Fatti'] - f_sc['Gol Subiti']
            st.dataframe(bold_df(f_sc[['Posizione','Giocatore','Punti','Gol Fatti','Gol Subiti','DR']].sort_values('Posizione')).background_gradient(subset=['Punti'], cmap='Blues').format({c: "{:g}" for c in ['Punti','Gol Fatti','Gol Subiti','DR']}), hide_index=True, use_container_width=True)

with t[1]: # BUDGET DINAMICO
    if f_rs is not None:
        st.subheader("💰 BUDGET E PATRIMONIO")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO'] = bu['Squadra_N'].map(rimborsi_mercato).fillna(0)
        sel = st.multiselect("**FILTRA VOCI:**", ['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI', 'RECUPERO'], default=['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI', 'RECUPERO'])
        bu['TOTALE'] = bu[sel].sum(axis=1) if sel else 0
        num_cols = bu.select_dtypes(include=['number']).columns
        st.dataframe(bold_df(bu[['Squadra_N'] + sel + ['TOTALE']].sort_values('TOTALE', ascending=False)).background_gradient(cmap='YlOrRd', subset=['TOTALE']).format({c: "{:g}" for c in num_cols}), hide_index=True, use_container_width=True)

with t[2]: # ROSE CON COLORAZIONE
    if f_rs is not None:
        c1, c2 = st.columns([1, 2])
        with c1: sq_r = st.selectbox("**SQUADRA**", ["TUTTE"] + sorted(f_rs['Squadra_N'].unique()), key="sq_rose_final")
        with c2: cerca_r = st.text_input("🔍 **CERCA CALCIATORE**", "").upper()
        df_r = f_rs.copy()
        if sq_r != "TUTTE": df_r = df_r[df_r['Squadra_N'] == sq_r]
        if cerca_r: df_r = df_r[df_r['Nome'].str.upper().str.contains(cerca_r, na=False)]
        
        def color_ruolo(val):
            v = str(val).upper()
            if 'POR' in v: return 'background-color: #FCE4EC'
            if 'DIF' in v: return 'background-color: #E8F5E9'
            if 'CEN' in v: return 'background-color: #E3F2FD'
            if 'ATT' in v: return 'background-color: #FFFDE7'
            return ''
        st.dataframe(bold_df(df_r[['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']]).applymap(color_ruolo, subset=['Ruolo']).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # VINCOLI (RIPRISTINATO)
    if f_vn is not None:
        st.subheader("📅 DETTAGLIO VINCOLI ATTIVI")
        sq_v = st.selectbox("**FILTRA SQUADRA**", ["TUTTE"] + sorted(f_vn['Sq_N'].unique()), key="vinc_filter_final")
        df_v = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.dataframe(bold_df(df_v[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False)).format({"Tot_Vincolo":"{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # SCAMBI ANALITICI (CON ANTE/POST E PATRIMONI)
    st.subheader("🔄 SIMULATORE SCAMBI GOLDEN")
    if f_rs is not None:
        col1, col2 = st.columns(2)
        with col1: sA = st.selectbox("SQUADRA A", sorted(f_rs['Squadra_N'].unique()), key="sA_final"); gA = st.multiselect("ESCONO DA A", f_rs[f_rs['Squadra_N']==sA]['Nome'].tolist())
        with col2: sB = st.selectbox("SQUADRA B", [s for s in sorted(f_rs['Squadra_N'].unique()) if s != sA], key="sB_final"); gB = st.multiselect("ESCONO DA B", f_rs[f_rs['Squadra_N']==sB]['Nome'].tolist())
        
        if gA and gB:
            def get_v(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
                vm = f_vn[f_vn['Giocatore_Match']==super_clean_match(n)] if f_vn is not None else pd.DataFrame()
                v = vm['Tot_Vincolo'].iloc[0] if not vm.empty else 0
                return {'t': p+v, 'v': v}
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

with t[5]: # TAGLI GIGANTI
    st.subheader("✂️ TAGLI GOLDEN")
    if f_rs is not None:
        sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="sq_tag_p")
        gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist())
        if gt:
            v_a = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt)]['Prezzo_N'].iloc[0]
            vm = f_vn[f_vn['Giocatore_Match'] == super_clean_match(gt)] if f_vn is not None else pd.DataFrame()
            vv = vm['Tot_Vincolo'].iloc[0] if not vm.empty else 0
            st.markdown(f'''<div class="cut-box"><div class="cut-player-name">{gt}</div><div style="font-size:2.2em; color:#2e7d32;">RIMBORSO: {round((v_a+vv)*0.6):g} CREDITI</div><br>ASTA: {v_a:g} | VINCOLI: {vv:g}</div>''', unsafe_allow_html=True)

with t[6]: # MERCATO CESSIONI (LAB)
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
            with c2: st.write(f"TOTALE: {row['TOTALE']:g}")
            with c3: st.write(f"<span class='{'status-ufficiale' if row['STATO']=='UFFICIALE' else 'status-probabile'}'>{row['STATO']}</span>", unsafe_allow_html=True)
            with c4:
                if row['STATO'] == "PROBABILE" and st.button("✅", key=f"u_{idx}"):
                    df_mercato.at[idx, 'STATO'] = "UFFICIALE"; df_mercato.to_csv(FILE_DB, index=False); st.rerun()
                if st.button("🗑️", key=f"d_{idx}"):
                    df_mercato = df_mercato.drop(idx); df_mercato.to_csv(FILE_DB, index=False); st.rerun()
        
        st.write("---")
        st.markdown("### 💰 RIEPILOGO RIMBORSI PER SQUADRA")
        sq_m = df_mercato.groupby('SQUADRA')['TOTALE'].sum().sort_values(ascending=False)
        cols_m = st.columns(4)
        for i, (sq_n, t_n) in enumerate(sq_m.items()):
            with cols_m[i % 4]: st.markdown(f'<div class="refund-box"><small>{sq_n}</small><br><b style="font-size:1.5em;">+{t_n:g}</b></div>', unsafe_allow_html=True)
