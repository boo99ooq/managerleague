import streamlit as st
import pandas as pd
import os
import unicodedata
import re
from datetime import datetime

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V4.0", layout="wide", initial_sidebar_state="expanded")

# --- CSS INTEGRATO: Neretto 900 + Stile Tabelle Premium ---
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
    
    /* Tabelle Premium Rose */
    .golden-table { width: 100%; border-collapse: collapse; margin: 10px 0; }
    .golden-table th { padding: 12px 15px; border: 2px solid #333; text-align: center; background-color: #f0f2f6; text-transform: uppercase; }
    .golden-table td { padding: 10px 15px; border: 1px solid #ddd; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI DI SUPPORTO (Dalla Golden Version) ---
def to_num(val):
    if pd.isna(val) or str(val).strip().lower() == 'x' or str(val).strip() == '': return 0.0
    s = str(val).replace('€', '').replace('.', '').replace(',', '.').strip()
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

def ld(f, is_quot=False):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, engine='python', skip_blank_lines=True, encoding='latin1')
        df.columns = [c.strip() for c in df.columns]
        if is_quot:
            df['Match_Nome'] = df['Nome'].apply(super_clean)
            return df
        return df.dropna(how='all')
    except: return None

# --- CARICAMENTO DATI ---
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS"}
FILE_DB = "mercatone_gennaio.csv"

f_sc, f_pt, f_rs_base, f_vn = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv")
f_qt = ld("quotazioni.csv", is_quot=True)

if f_rs_base is not None:
    f_rs = f_rs_base.copy()
    f_rs['Squadra_N'] = f_rs['Fantasquadra'].str.upper().str.strip().replace(map_n)
    f_rs['Match_Nome'] = f_rs['Nome'].apply(super_clean)
    f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(to_num)
    f_rs['Ruolo_N'] = f_rs.apply(normalize_ruolo, axis=1)
    if f_qt is not None:
        col_q = next((c for c in f_qt.columns if 'QT' in c.upper() or 'VAL' in c.upper()), f_qt.columns[-1])
        f_rs = pd.merge(f_rs, f_qt[['Match_Nome', col_q]], on='Match_Nome', how='left').fillna({col_q: 0})
        f_rs = f_rs.rename(columns={col_q: 'Quotazione'}).drop_duplicates(subset=['Fantasquadra', 'Nome'])
else:
    f_rs = None

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].str.upper().str.strip().replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean)
    v_cols = [c for c in f_vn.columns if '202' in c]
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)

df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])
rimborsi_m = df_mercato.groupby("SQUADRA")["TOTALE"].sum().to_dict() if not df_mercato.empty else {}

# --- SIDEBAR (Ricerca Rapida) ---
with st.sidebar:
    st.header("🔍 RICERCA RAPIDA")
    cerca = st.text_input("Nome Giocatore").upper()
    if cerca and f_rs is not None:
        ris = f_rs[f_rs['Match_Nome'].str.contains(cerca)]
        for _, r in ris.iterrows():
            st.markdown(f'<div class="player-card"><b>{r["Nome"]}</b><br>{r["Fantasquadra"]} | {r["Ruolo"]}<br>Asta: {r["Prezzo_N"]} | Quot: {r.get("Quotazione",0)}</div>', unsafe_allow_html=True)

# --- TABS PRINCIPALI ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

# TAB 0: CLASSIFICHE
with t[0]:
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c1:
            st.subheader("🎯 PUNTI")
            f_pt['P_N'] = f_pt['Punti Totali'].apply(to_num)
            st.dataframe(f_pt[['Posizione','Giocatore','P_N']].sort_values('Posizione'), hide_index=True)
    if f_sc is not None:
        with c2:
            st.subheader("⚔️ SCONTRI DIRETTI")
            st.dataframe(f_sc[['Posizione','Giocatore','Punti','Gol Fatti']].sort_values('Posizione'), hide_index=True)

# TAB 1: BUDGET DINAMICO
with t[1]:
    if f_rs is not None:
        st.subheader("💰 SITUAZIONE ECONOMICA")
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO'] = bu['Squadra_N'].map(rimborsi_m).fillna(0)
        bu['TOTALE'] = bu['SPESA ROSE'] + bu['SPESA VINCOLI'] + bu['CREDITI'] + bu['RECUPERO']
        st.dataframe(bu.sort_values('TOTALE', ascending=False), hide_index=True, use_container_width=True)

# TAB 2: ROSE PREMIUM (Grafica integrata)
with t[2]:
    if f_rs is not None:
        sq_r = st.selectbox("**SQUADRA**", sorted(f_rs['Squadra_N'].unique()))
        df_team = f_rs[f_rs['Squadra_N'] == sq_r].copy()
        
        # Statistiche in alto
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="stat-card">👥 GIOCATORI<br><b style="font-size:1.5em;">{len(df_team)}</b></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="stat-card" style="border-color:#1a73e8;">💰 SPESA ASTA<br><b style="font-size:1.5em; color:#1a73e8;">{int(df_team["Prezzo_N"].sum())}</b></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="stat-card" style="border-color:#2e7d32;">📈 VAL. ATTUALE<br><b style="font-size:1.5em; color:#2e7d32;">{int(df_team["Quotazione"].sum())}</b></div>', unsafe_allow_html=True)
        with c4: 
            n_gio = len(df_team[df_team['Ruolo_N'] == 'GIO'])
            st.markdown(f'<div class="stat-card" style="border-color:#9c27b0;">👶 GIOVANI<br><b style="font-size:1.5em; color:#9c27b0;">{n_gio}</b></div>', unsafe_allow_html=True)

        # Tabella Riassuntiva HTML
        st.write("---")
        pal_piena = {'POR': '#F06292', 'DIF': '#81C784', 'CEN': '#64B5F6', 'ATT': '#FFF176', 'GIOVANI': '#AB47BC'}
        html_riass = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>N°</th><th>ASTA</th><th>VALORE</th></tr></thead><tbody>'
        for r_label in ['POR', 'DIF', 'CEN', 'ATT', 'GIO']:
            d_rep = df_team[df_team['Ruolo_N'] == r_label]
            bg = pal_piena.get('GIOVANI' if r_label=='GIO' else r_label, '#fff')
            html_riass += f'<tr style="background-color:{bg};"><td>{r_label}</td><td>{len(d_rep)}</td><td>{int(d_rep["Prezzo_N"].sum())}</td><td>{int(d_rep["Quotazione"].sum())}</td></tr>'
        st.markdown(html_riass + '</tbody></table>', unsafe_allow_html=True)

        # Tabella Dettaglio HTML
        st.write("---")
        pal_shades = {'POR': ['#FCE4EC', '#F8BBD0', '#F48FB1', '#F06292'], 'DIF': ['#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784'], 'CEN': ['#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6'], 'ATT': ['#FFFDE7', '#FFF9C4', '#FFF59D', '#FFF176'], 'GIO': ['#F3E5F5', '#E1BEE7', '#CE93D8', '#AB47BC']}
        html_dett = '<table class="golden-table"><thead><tr><th>RUOLO</th><th>NOME</th><th>ASTA</th><th>QUOT</th></tr></thead><tbody>'
        for _, row in df_team.sort_values(['Ruolo_N', 'Prezzo_N'], ascending=[True, False]).iterrows():
            sh = pal_shades.get(row['Ruolo_N'], ['#fff']*4)
            html_dett += f'<tr><td style="background-color:{sh[0]}">{row["Ruolo"]}</td><td style="background-color:{sh[1]}">{row["Nome"]}</td><td style="background-color:{sh[2]}">{int(row["Prezzo_N"])}</td><td style="background-color:{sh[3]}">{int(row["Quotazione"])}</td></tr>'
        st.markdown(html_dett + '</tbody></table>', unsafe_allow_html=True)

# TAB 4: SCAMBI (RIPRISTINO LOGICA GOLDEN)
with t[4]:
    st.subheader("🔄 SIMULATORE SCAMBI (Logica Golden)")
    if f_rs is not None:
        c1, c2 = st.columns(2)
        with c1:
            sA = st.selectbox("SQUADRA A", sorted(f_rs['Squadra_N'].unique()), key="sA")
            gA = st.multiselect("ESCONO DA A", f_rs[f_rs['Squadra_N']==sA]['Nome'].tolist())
        with c2:
            sB = st.selectbox("SQUADRA B", [s for s in sorted(f_rs['Squadra_N'].unique()) if s != sA], key="sB")
            gB = st.multiselect("ESCONO DA B", f_rs[f_rs['Squadra_N']==sB]['Nome'].tolist())
        
        if gA and gB:
            # Calcolo Valori A (Asta + Vincolo)
            vA = 0
            for gn in gA:
                base = f_rs[(f_rs['Squadra_N']==sA) & (f_rs['Nome']==gn)]['Prezzo_N'].iloc[0]
                vinc = f_vn[(f_vn['Sq_N']==sA) & (f_vn['Giocatore_Match']==super_clean(gn))]['Tot_Vincolo'].sum() if f_vn is not None else 0
                vA += (base + vinc)
            
            # Calcolo Valori B (Asta + Vincolo)
            vB = 0
            for gn in gB:
                base = f_rs[(f_rs['Squadra_N']==sB) & (f_rs['Nome']==gn)]['Prezzo_N'].iloc[0]
                vinc = f_vn[(f_vn['Sq_N']==sB) & (f_vn['Giocatore_Match']==super_clean(gn))]['Tot_Vincolo'].sum() if f_vn is not None else 0
                vB += (base + vinc)
            
            incontro = (vA + vB) / 2
            gap = incontro - vA # Se positivo, B deve dare crediti a A
            
            st.markdown(f'<div class="punto-incontro-box"><h3>PUNTO INCONTRO: {incontro:g}</h3></div>', unsafe_allow_html=True)
            
            cc1, cc2 = st.columns(2)
            with cc1: 
                st.metric(f"Valore Uscente {sA}", f"{vA:g}")
                st.write(f"Nuovo Valore del blocco in {sB}: **{incontro:g}**")
            with cc2: 
                st.metric(f"Valore Uscente {sB}", f"{vB:g}")
                st.write(f"Nuovo Valore del blocco in {sA}: **{incontro:g}**")
            
            if gap != 0:
                msg = f"**{sB}** deve versare **{abs(gap):g}** crediti a **{sA}**" if gap > 0 else f"**{sA}** deve versare **{abs(gap):g}** crediti a **{sB}**"
                st.warning(msg)

# TAB 5: TAGLI
with t[5]:
    if f_rs is not None:
        sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="tag_sq")
        gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N']==sq_t]['Nome'].tolist())
        if gt:
            v_asta = f_rs[(f_rs['Squadra_N']==sq_t) & (f_rs['Nome']==gt)]['Prezzo_N'].iloc[0]
            st.markdown(f'<div class="cut-box"><h2>{gt}</h2><h3 style="color:green;">RIMBORSO (60%): {round(v_asta*0.6, 1)}</h3></div>', unsafe_allow_html=True)

# TAB 6: MERCATO (Gestione CSV)
with t[6]:
    st.subheader("🚀 MERCATO CESSIONI")
    with st.expander("Aggiungi Giocatore Ceduto"):
        sq_m = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="m_sq")
        gio_m = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N']==sq_m]['Nome'].tolist(), key="m_gio")
        if st.button("Registra Cessione"):
            info = f_rs[(f_rs['Squadra_N']==sq_m) & (f_rs['Nome']==gio_m)].iloc[0]
            vv_m = f_vn[(f_vn['Sq_N']==sq_m) & (f_vn['Giocatore_Match']==super_clean(gio_m))]['Tot_Vincolo'].sum() if f_vn is not None else 0
            tot_m = ((info['Prezzo_N'] + info['Quotazione']) * 0.5) + vv_m
            nuova = pd.DataFrame([{"GIOCATORE": gio_m, "SQUADRA": sq_m, "TOTALE": tot_m, "STATO": "PROBABILE"}])
            df_mercato = pd.concat([df_mercato, nuova], ignore_index=True)
            df_mercato.to_csv(FILE_DB, index=False)
            st.rerun()
    
    if not df_mercato.empty:
        st.table(df_mercato)
