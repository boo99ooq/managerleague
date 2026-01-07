import streamlit as st
import pandas as pd
import os
import altair as alt

# 1. SETUP UI E STILE (GOLDEN UI)
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

# Configurazione Budget Extra e Mappature
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}
map_r = {"P": "PORTIERE", "D": "DIFENSORE", "C": "CENTROCAMPISTA", "A": "ATTACCANTE", 
         "PORTIERE": "PORTIERE", "DIFENSORE": "DIFENSORE", "CENTROCAMPISTA": "CENTROCAMPISTA", "ATTACCANTE": "ATTACCANTE"}

# --- FUNZIONI DI PULIZIA ---
def cv(v):
    """Converte '1.074,5' o '15,0' in float 1074.5 o 15.0"""
    if pd.isna(v) or str(v).strip() == "": return 0.0
    s = str(v).replace('"', '').strip()
    if "." in s and "," in s: s = s.replace(".", "")
    s = s.replace(",", ".")
    try: return float(s)
    except: return 0.0

def clean_s(s):
    return str(s).strip().upper() if not pd.isna(s) else ""

def get_match_key(name):
    """Estrae la parte principale del cognome per il match"""
    s = clean_s(name).replace("-", " ")
    parts = [p for p in s.split() if len(p) > 1]
    return parts[-1] if parts else s

def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, skip_blank_lines=True, engine='python')
        if df.columns[0].startswith('Unnamed'):
            df = pd.read_csv(f, skiprows=1, engine='python')
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# --- CARICAMENTO ---
f_sc, f_pt, f_rs, f_vn, f_qt = ld("scontridiretti.csv"), ld("classificapunti.csv"), ld("rose_complete.csv"), ld("vincoli.csv"), ld("quotazioni.csv")

# --- ELABORAZIONE DATI ---
if f_rs is not None:
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)
    f_rs['Ruolo_C'] = f_rs['Ruolo'].apply(lambda x: map_r.get(clean_s(x)[0], clean_s(x)))
    f_rs['Squadra_C'] = f_rs['Fantasquadra'].apply(clean_s).replace(map_n)
    f_rs['MatchKey'] = f_rs['Nome'].apply(get_match_key)

    if f_qt is not None:
        f_qt['MatchKey'] = f_qt['Nome'].apply(get_match_key)
        f_qt['Ruolo_QT'] = f_qt['R'].map(map_r)
        f_qt['Quotazione'] = f_qt['Qt.A'].apply(cv)
        # Unione intelligente
        f_rs = pd.merge(f_rs, f_qt[['MatchKey', 'Ruolo_QT', 'Quotazione']], 
                        left_on=['MatchKey', 'Ruolo_C'], right_on=['MatchKey', 'Ruolo_QT'], 
                        how='left').drop('Ruolo_QT', axis=1)
        f_rs['Quotazione'] = f_rs['Quotazione'].fillna(0)
        f_rs['Plusvalenza'] = f_rs['Quotazione'] - f_rs['Prezzo']

if f_vn is not None:
    f_vn['Sq_C'] = f_vn['Squadra'].apply(clean_s).replace(map_n)
    v_cols = [c for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29'] if c in f_vn.columns]
    for c in v_cols: f_vn[c] = f_vn[c].apply(cv)
    f_vn['Spesa_V'] = f_vn[v_cols].sum(axis=1)

# --- TABS ---
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

with t[0]: # CLASSIFICA + GRAFICO TREND
    if f_pt is not None:
        f_pt['Punti_N'] = f_pt['Punti Totali'].apply(cv)
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🎯 Punti")
            st.dataframe(f_pt[['Posizione','Giocatore','Punti_N']].sort_values('Posizione').style.background_gradient(subset=['Punti_N'], cmap='Greens'), hide_index=True)
        with c2:
            st.subheader("📈 Trend")
            chart = alt.Chart(f_pt).mark_line(point=True, color='green').encode(
                x=alt.X('Giocatore:N', sort='-y'), y=alt.Y('Punti_N:Q', scale=alt.Scale(domainMin=f_pt['Punti_N'].min()-10))
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)

with t[1]: # BUDGET + GRAFICO BARRE
    if f_rs is not None:
        st.subheader("💰 Bilancio e Patrimonio")
        eco = f_rs.groupby('Squadra_C').agg({'Prezzo': 'sum', 'Quotazione': 'sum'}).reset_index()
        eco.columns = ['Squadra', 'Spesa Rosa', 'Valore Mercato']
        eco['Extra'] = eco['Squadra'].map(bg_ex).fillna(0)
        if f_vn is not None:
            v_sum = f_vn.groupby('Sq_C')['Spesa_V'].sum().reset_index()
            eco = pd.merge(eco, v_sum, left_on='Squadra', right_on='Sq_C', how='left').fillna(0).drop('Sq_C', axis=1)
            eco.rename(columns={'Spesa_V': 'Vincoli'}, inplace=True)
        eco['Patrimonio'] = eco['Valore Mercato'] + eco['Extra'] + eco.get('Vincoli', 0)
        
        st.dataframe(eco.sort_values('Patrimonio', ascending=False).style.background_gradient(subset=['Valore Mercato'], cmap='YlGn').format({c: "{:g}" for c in eco.columns if c != 'Squadra'}), hide_index=True, use_container_width=True)
        
        # Grafico Barre Impilate
        eco_m = eco.melt(id_vars='Squadra', value_vars=['Valore Mercato', 'Extra', 'Vincoli'])
        st.altair_chart(alt.Chart(eco_m).mark_bar().encode(y=alt.Y('Squadra:N', sort='-x'), x='sum(value):Q', color='variable:N').properties(height=400), use_container_width=True)

with t[3]: # ROSE COLORATE
    if f_rs is not None:
        sq = st.selectbox("Seleziona Squadra:", sorted(f_rs['Squadra_C'].unique()), key="sq_r")
        df_sq = f_rs[f_rs['Squadra_C'] == sq].copy()
        def style_r(row):
            bg = {'PORTIERE':'#E3F2FD','DIFENSORE':'#E8F5E9','CENTROCAMPISTA':'#FFFDE7','ATTACCANTE':'#FFEBEE'}.get(row['Ruolo_C'], '#FFFFFF')
            return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
        
        cols = ['Ruolo', 'Nome', 'Prezzo']
        if 'Quotazione' in df_sq.columns: cols += ['Quotazione', 'Plusvalenza']
        st.dataframe(df_sq[cols].style.apply(style_r, axis=1).background_gradient(subset=['Plusvalenza'], cmap='RdYlGn') if 'Plusvalenza' in df_sq.columns else df_sq[cols].style.apply(style_r, axis=1), hide_index=True, use_container_width=True)
        if 'Plusvalenza' in df_sq.columns: st.metric("Plusvalenza Rosa", f"{df_sq['Plusvalenza'].sum():+g}")

with t[5]: # SCAMBI MERITOCRATICI
    st.subheader("🔄 Simulatore Scambi Proporzionale")
    if f_rs is not None:
        c1, c2 = st.columns(2)
        with c1:
            sa = st.selectbox("Squadra A:", sorted(f_rs['Squadra_C'].unique()), key="sa")
            ga = st.multiselect("Cede da A:", f_rs[f_rs['Squadra_C']==sa]['Nome'], key="ga")
        with c2:
            sb = st.selectbox("Squadra B:", [s for s in sorted(f_rs['Squadra_C'].unique()) if s != sa], key="sb")
            gb = st.multiselect("Cede da B:", f_rs[f_rs['Squadra_C']==sb]['Nome'], key="gb")
        
        if ga and gb:
            def get_v(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo'].iloc[0]
                v = f_vn[f_vn['Giocatore'].apply(clean_s)==clean_s(n)]['Spesa_V'].sum() if f_vn is not None else 0
                return p + v
            v_a, v_b = sum(get_v(n) for n in ga), sum(get_v(n) for n in gb)
            target = (v_a + v_b) / (len(ga) + len(gb))
            st.success(f"🤝 Punto di incontro unitario: **{target:g} crediti**")
            # Calcolo coefficienti
            ca, cb = (target * len(ga))/v_a if v_a > 0 else 1, (target * len(gb))/v_b if v_b > 0 else 1
            res1, res2 = st.columns(2)
            with res1:
                for n in ga: st.info(f"{n} -> Nuovo Valore: **{round(get_v(n)*ca)}**")
            with res2:
                for n in gb: st.info(f"{n} -> Nuovo Valore: **{round(get_v(n)*cb)}**")
