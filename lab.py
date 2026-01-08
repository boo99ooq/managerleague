import streamlit as st
import pandas as pd
import os
import unicodedata
import re

# 1. SETUP UI
st.set_page_config(page_title="MuyFantaManager Golden V3.2", layout="wide", initial_sidebar_state="expanded")

# --- BLOCCO CSS DEFINITIVO ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"] *, .stDataFrame td, .stDataFrame th, p, div, span, label { 
        font-weight: 900 !important; 
        color: #000 !important; 
    }
    .player-card { padding: 12px; border-radius: 8px; margin-bottom: 10px; border-left: 6px solid #333; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .patrimonio-box { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 3px solid #1a73e8; text-align: center; }
    .punto-incontro-box { background-color: #fff3e0; padding: 10px 30px; border-radius: 15px; border: 3px solid #ff9800; text-align: center; margin: 10px auto; width: fit-content; }
    .cut-box { background-color: #fdfdfd; padding: 25px; border-radius: 15px; border: 4px solid #333; box-shadow: 6px 6px 0px #ff4b4b; text-align: center; }
    .refund-box-pastello { padding: 15px; border-radius: 12px; border: 3px solid #333; text-align: center; min-height: 135px; box-shadow: 4px 4px 0px #333; margin-bottom: 15px; }
    .bg-azzurro { background-color: #E3F2FD !important; }
    .bg-verde { background-color: #E8F5E9 !important; }
    .bg-rosa { background-color: #FCE4EC !important; }
    .bg-giallo { background-color: #FFFDE7 !important; }
    .bg-arancio { background-color: #FFF3E0 !important; }
    .bg-viola { background-color: #F3E5F5 !important; }
    .status-ufficiale { color: #ffffff !important; background-color: #2e7d32; padding: 4px 10px; border-radius: 6px; font-size: 0.9em; }
    .status-probabile { color: #ffffff !important; background-color: #ed6c02; padding: 4px 10px; border-radius: 6px; font-size: 0.9em; }
    .text-ufficiale { color: #2e7d32; }
    .text-probabile { color: #ed6c02; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONI SUPPORTO ---
def bold_df(df):
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
    if f_qt is not None: f_rs = pd.merge(f_rs, f_qt, on='Match_Nome', how='left').fillna({'Quotazione': 0})

if f_vn is not None:
    f_vn['Sq_N'] = f_vn['Squadra'].str.upper().str.strip().replace(map_n)
    f_vn['Giocatore_Match'] = f_vn['Giocatore'].apply(super_clean_match)
    v_cols = [c for c in f_vn.columns if '202' in c]
    for c in v_cols: f_vn[c] = f_vn[c].apply(to_num)
    f_vn['Tot_Vincolo'] = f_vn[v_cols].sum(axis=1)
    f_vn['Anni_T'] = f_vn[v_cols].gt(0).sum(axis=1).astype(str) + " ANNI"

df_mercato = pd.read_csv(FILE_DB) if os.path.exists(FILE_DB) else pd.DataFrame(columns=["GIOCATORE", "SQUADRA", "TOTALE", "STATO"])

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔍 **RICERCA CALCIATORE**")
    if f_rs is not None:
        cerca_side = st.multiselect("**CERCA NELLA LEGA**", sorted(f_rs['Nome'].unique()))
        for n in cerca_side:
            d_g = f_rs[f_rs['Nome'] == n].iloc[0]
            v_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(n)] if f_vn is not None else pd.DataFrame()
            vv = v_m['Tot_Vincolo'].iloc[0] if not v_m.empty else 0
            st.markdown(f'''<div class="player-card"><b>{n}</b> ({d_g['Squadra_N']})<br>ASTA: {int(d_g['Prezzo_N'])} | VINC: {int(vv)}<br>QUOT: {int(d_g['Quotazione'])}</div>''', unsafe_allow_html=True)

# --- TABS ---
t = st.tabs(["🏆 **CLASSIFICHE**", "💰 **BUDGET**", "🏃 **ROSE**", "📅 **VINCOLI**", "🔄 **SCAMBI**", "✂️ **TAGLI**", "🚀 **MERCATO**"])

with t[0]: # TAB 0: CLASSIFICHE
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
            for col in ['Punti', 'Gol Fatti', 'Gol Subiti']: f_sc[col] = f_sc[col].apply(to_num)
            f_sc['DR'] = f_sc['Gol Fatti'] - f_sc['Gol Subiti']
            st.dataframe(bold_df(f_sc[['Posizione','Giocatore','Punti','Gol Fatti','Gol Subiti','DR']].sort_values('Posizione')).background_gradient(subset=['Punti'], cmap='Blues').format({c: "{:g}" for c in ['Punti','Gol Fatti','Gol Subiti','DR']}), hide_index=True, use_container_width=True)

with t[1]: # TAB 1: BUDGET (CON SELETTORE COLONNE)
    if f_rs is not None:
        st.subheader("💰 **BUDGET AGGIORNATO**")
        
        # Calcolo componenti budget
        rimborsi_uff = df_mercato[df_mercato['STATO'] == 'UFFICIALE'].groupby('SQUADRA')['TOTALE'].sum().to_dict()
        bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index().rename(columns={'Prezzo_N': 'SPESA ROSE'})
        v_sum = f_vn.groupby('Sq_N')['Tot_Vincolo'].sum().reset_index() if f_vn is not None else pd.DataFrame(columns=['Sq_N', 'Tot_Vincolo'])
        bu = pd.merge(bu, v_sum, left_on='Squadra_N', right_on='Sq_N', how='left').fillna(0).drop('Sq_N', axis=1).rename(columns={'Tot_Vincolo': 'SPESA VINCOLI'})
        bu['CREDITI DISPONIBILI'] = bu['Squadra_N'].map(bg_ex).fillna(0)
        bu['RECUPERO CESSIONI'] = bu['Squadra_N'].map(rimborsi_uff).fillna(0)
        
        # Menu selezione colonne
        opzioni = ['SPESA ROSE', 'SPESA VINCOLI', 'CREDITI DISPONIBILI', 'RECUPERO CESSIONI']
        sel_cols = st.multiselect("**SELEZIONA VOCI DA SOMMARE:**", opzioni, default=opzioni)
        
        if sel_cols:
            bu['TOTALE'] = bu[sel_cols].sum(axis=1)
            # Mostra tabella ordinata
            cols_to_show = ['Squadra_N'] + sel_cols + ['TOTALE']
            num_cols = bu[sel_cols + ['TOTALE']].columns
            st.dataframe(bold_df(bu[cols_to_show].sort_values('TOTALE', ascending=False)).background_gradient(cmap='YlOrRd', subset=['TOTALE']).format({c: "{:g}" for c in num_cols}), hide_index=True, use_container_width=True)
        else:
            st.warning("Seleziona almeno una voce per visualizzare il budget.")

with t[2]: # TAB 2: ROSE
    if f_rs is not None:
        st.subheader("🏃 GESTIONE ROSE")
        sq_r = st.selectbox("**SQUADRA**", ["TUTTE"] + sorted(f_rs['Squadra_N'].unique()), key="sq_rose")
        df_r = f_rs.copy()
        if sq_r != "TUTTE": df_r = df_r[df_r['Squadra_N'] == sq_r]
        
        def color_ruolo(val):
            v = str(val).upper()
            if 'POR' in v: return 'background-color: #FCE4EC'
            if 'DIF' in v: return 'background-color: #E8F5E9'
            if 'CEN' in v: return 'background-color: #E3F2FD'
            if 'ATT' in v: return 'background-color: #FFFDE7'
            return ''
        st.dataframe(bold_df(df_r[['Ruolo', 'Nome', 'Prezzo_N', 'Quotazione']]).applymap(color_ruolo, subset=['Ruolo']).format({"Prezzo_N":"{:g}", "Quotazione":"{:g}"}), hide_index=True, use_container_width=True)

with t[3]: # TAB 3: VINCOLI
    if f_vn is not None:
        st.subheader("📅 DETTAGLIO VINCOLI ATTIVI")
        sq_v = st.selectbox("**SQUADRA**", ["TUTTE"] + sorted(f_vn['Sq_N'].unique()), key="v_fil")
        df_v = f_vn if sq_v == "TUTTE" else f_vn[f_vn['Sq_N'] == sq_v]
        st.dataframe(bold_df(df_v[['Squadra', 'Giocatore', 'Tot_Vincolo', 'Anni_T']].sort_values('Tot_Vincolo', ascending=False)).format({"Tot_Vincolo":"{:g}"}), hide_index=True, use_container_width=True)

with t[4]: # TAB 4: SCAMBI ANALITICI
    st.subheader("🔄 **SIMULATORE SCAMBI ANALITICO**")
    if f_rs is not None:
        col_a, col_b = st.columns(2)
        with col_a:
            sq_a = st.selectbox("SQUADRA A", sorted(f_rs['Squadra_N'].unique()), key="sa")
            gioc_a = st.multiselect("ESCONO DA A", f_rs[f_rs['Squadra_N']==sq_a]['Nome'].tolist())
        with col_b:
            sq_b = st.selectbox("SQUADRA B", [s for s in sorted(f_rs['Squadra_N'].unique()) if s != sq_a], key="sb")
            gioc_b = st.multiselect("ESCONO DA B", f_rs[f_rs['Squadra_N']==sq_b]['Nome'].tolist())

        if gioc_a and gioc_b:
            def get_full_val(n):
                prezzo = f_rs[f_rs['Nome']==n]['Prezzo_N'].iloc[0]
                vinc_m = f_vn[f_vn['Giocatore_Match']==super_clean_match(n)] if f_vn is not None else pd.DataFrame()
                vinc_t = vinc_m['Tot_Vincolo'].iloc[0] if not vinc_m.empty else 0
                return {'tot': prezzo + vinc_t, 'vinc': vinc_t}

            val_a = {n: get_full_val(n) for n in gioc_a}
            val_b = {n: get_full_val(n) for n in gioc_b}
            tot_a, tot_b = sum(v['tot'] for v in val_a.values()), sum(v['tot'] for v in val_b.values())
            media_scambio = round((tot_a + tot_b) / 2)
            
            st.markdown(f'<div class="punto-incontro-box">GAP: {tot_a - tot_b:g} | PUNTO INCONTRO: {media_scambio:g}</div>', unsafe_allow_html=True)
            
            res_a, res_b = st.columns(2)
            with res_a:
                st.write(f"**ENTRANO IN {sq_a}:**")
                for n, dati in val_b.items():
                    nuovo_v = round((dati['tot'] / tot_b) * media_scambio) if tot_b > 0 else media_scambio
                    st.markdown(f'''<div class="player-card" style="background-color:#e3f2fd; border:3px solid #1e88e5;">
                        <b>{n}</b><br>
                        <small>NUOVO: {max(0, nuovo_v - int(dati['vinc'])):g} + {dati['vinc']:g} (VINC) | ANTE: {dati['tot']:g}</small>
                    </div>''', unsafe_allow_html=True)
            with res_b:
                st.write(f"**ENTRANO IN {sq_b}:**")
                for n, dati in val_a.items():
                    nuovo_v = round((dati['tot'] / tot_a) * media_scambio) if tot_a > 0 else media_scambio
                    st.markdown(f'''<div class="player-card" style="background-color:#fbe9e7; border:3px solid #e53935;">
                        <b>{n}</b><br>
                        <small>NUOVO: {max(0, nuovo_v - int(dati['vinc'])):g} + {dati['vinc']:g} (VINC) | ANTE: {dati['tot']:g}</small>
                    </div>''', unsafe_allow_html=True)

            pat_a = f_rs[f_rs['Squadra_N']==sq_a]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sq_a]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sq_a, 0)
            pat_b = f_rs[f_rs['Squadra_N']==sq_b]['Prezzo_N'].sum() + (f_vn[f_vn['Sq_N']==sq_b]['Tot_Vincolo'].sum() if f_vn is not None else 0) + bg_ex.get(sq_b, 0)
            shift = media_scambio - tot_a
            
            c_p1, c_p2 = st.columns(2)
            c_p1.markdown(f'<div class="patrimonio-box">NUOVO {sq_a}<br><h2>{int(pat_a + shift)}</h2><small>PRIMA: {int(pat_a)}</small></div>', unsafe_allow_html=True)
            c_p2.markdown(f'<div class="patrimonio-box">NUOVO {sq_b}<br><h2>{int(pat_b - shift)}</h2><small>PRIMA: {int(pat_b)}</small></div>', unsafe_allow_html=True)

with t[5]: # TAB 5: TAGLI
    st.subheader("✂️ TAGLI GOLDEN")
    if f_rs is not None:
        sq_t = st.selectbox("SQUADRA", sorted(f_rs['Squadra_N'].unique()), key="st_tag")
        gt = st.selectbox("GIOCATORE", f_rs[f_rs['Squadra_N'] == sq_t]['Nome'].tolist())
        if gt:
            v_a = f_rs[(f_rs['Squadra_N'] == sq_t) & (f_rs['Nome'] == gt)]['Prezzo_N'].iloc[0]
            vm = f_vn[f_vn['Giocatore_Match'] == super_clean_match(gt)] if f_vn is not None else pd.DataFrame()
            vv = vm['Tot_Vincolo'].iloc[0] if not vm.empty else 0
            st.markdown(f'''<div class="cut-box"><div class="cut-player-name">{gt}</div><div style="font-size:2.2em; color:#2e7d32;">RIMBORSO: {round((v_a+vv)*0.6):g}</div><br>ASTA: {v_a:g} | VINCOLI: {vv:g}</div>''', unsafe_allow_html=True)

with t[6]: # TAB 6: MERCATO PASTELLO
    st.subheader("🚀 MERCATO GENNAIO")
    with st.expander("➕ AGGIUNGI CESSIONE"):
        sc = st.selectbox("Seleziona:", [""] + sorted(f_rs['Nome'].unique()) if f_rs is not None else [""])
        if st.button("INSERISCI"):
            if sc != "" and sc not in df_mercato['GIOCATORE'].values:
                info = f_rs[f_rs['Nome'] == sc].iloc[0]
                vm_m = f_vn[f_vn['Giocatore_Match'] == super_clean_match(sc)] if f_vn is not None else pd.DataFrame()
                vv = vm_m['Tot_Vincolo'].iloc[0] if not vm_m.empty else 0
                nuova = pd.DataFrame([{"GIOCATORE": sc, "SQUADRA": info['Squadra_N'], "TOTALE": ((info['Prezzo_N'] + info['Quotazione'])*0.5)+vv, "STATO": "PROBABILE"}])
                df_mercato = pd.concat([df_mercato, nuova], ignore_index=True); df_mercato.to_csv(FILE_DB, index=False); st.rerun()

    if not df_mercato.empty:
        st.write("---")
        for idx, row in df_mercato.iterrows():
            mc1, mc2, mc3, mc4 = st.columns([2, 1, 1, 1])
            with mc1: st.write(f"**{row['GIOCATORE']}** ({row['SQUADRA']})")
            with mc2: st.write(f"RIMB: **{row['TOTALE']:g}**")
            with mc3: 
                cl = "status-ufficiale" if row['STATO'] == "UFFICIALE" else "status-probabile"
                st.markdown(f'<span class="{cl}">{row["STATO"]}</span>', unsafe_allow_html=True)
            with mc4:
                if row['STATO'] == "PROBABILE" and st.button("✅", key=f"u_{idx}"):
                    df_mercato.at[idx, 'STATO'] = "UFFICIALE"; df_mercato.to_csv(FILE_DB, index=False); st.rerun()
                if st.button("🗑️", key=f"d_{idx}"):
                    df_mercato = df_mercato.drop(idx).to_csv(FILE_DB, index=False); st.rerun()
        
        st.write("---")
        st.markdown("### 💰 **RECUPERO CREDITI PER SQUADRA**")
        colori_pastello = ["bg-azzurro", "bg-verde", "bg-rosa", "bg-giallo", "bg-arancio", "bg-viola"]
        sq_m = df_mercato.groupby(['SQUADRA', 'STATO'])['TOTALE'].sum().unstack(fill_value=0)
        if 'UFFICIALE' not in sq_m.columns: sq_m['UFFICIALE'] = 0
        if 'PROBABILE' not in sq_m.columns: sq_m['PROBABILE'] = 0
        sq_m['TOT_GEN'] = sq_m['UFFICIALE'] + sq_m['PROBABILE']
        
        cols_m = st.columns(4)
        for i, (sq_n, data) in enumerate(sq_m.sort_values('TOT_GEN', ascending=False).iterrows()):
            colore_classe = colori_pastello[i % len(colori_pastello)]
            with cols_m[i % 4]:
                st.markdown(f'''
                <div class="refund-box-pastello {colore_classe}">
                    <div style="font-size: 0.9em; margin-bottom: 5px;">{sq_n}</div>
                    <div style="font-size: 1.8em;"><b>+{data['TOT_GEN']:g}</b></div>
                    <hr style="margin:8px 0; border:0; border-top:2px solid rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; font-size: 0.85em;">
                        <span class="text-ufficiale">Uff: {data['UFFICIALE']:g}</span>
                        <span class="text-probabile">Prob: {data['PROBABILE']:g}</span>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
