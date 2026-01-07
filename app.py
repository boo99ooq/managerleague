import streamlit as st
import pandas as pd
import os
import altair as alt

# 1. SETUP E STILE GOLDEN
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

# Configurazione Budget e Mappature
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}
map_r = {"P": "PORTIERE", "D": "DIFENSORE", "C": "CENTROCAMPISTA", "A": "ATTACCANTE"}

# --- UTILITY DI PULIZIA ---
def cv(v):
    if pd.isna(v): return 0.0
    try:
        s = str(v).replace('"', '').replace(',', '.').strip()
        return float(s) if s != "" else 0.0
    except: return 0.0

def clean_text(s):
    if pd.isna(s): return ""
    return " ".join(str(s).upper().replace('-', ' ').replace('.', '').split()).strip()

def get_match_key(name):
    """Estrae il cognome per il match (es. 'MARTINEZ' da 'MARTINEZ L.')"""
    s = clean_text(name)
    if not s: return ""
    parts = s.split()
    # Se abbiamo 'MARTINEZ L.', prendiamo 'MARTINEZ'
    # Se abbiamo 'LAUTARO MARTINEZ', prendiamo 'MARTINEZ'
    return parts[0] if len(parts[0]) > 2 else (parts[1] if len(parts) > 1 else parts[0])

def ld(f):
    if not os.path.exists(f): return None
    try:
        # Legge saltando righe vuote iniziali
        df = pd.read_csv(f, sep=',', engine='python', encoding='utf-8-sig', skip_blank_lines=True)
        # Se la prima colonna è "Unnamed", riprova saltando la prima riga
        if df.columns[0].startswith('Unnamed'):
            df = pd.read_csv(f, sep=',', engine='python', encoding='utf-8-sig', skiprows=1)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except: return None

# --- CARICAMENTO ---
f_rs, f_vn, f_qt = ld("rose_complete.csv"), ld("vincoli.csv"), ld("quotazioni.csv")
f_sc, f_pt = ld("scontridiretti.csv"), ld("classificapunti.csv")

# --- ELABORAZIONE ---
if f_rs is not None:
    f_rs['Nome_Match'] = f_rs['Nome'].apply(get_match_key)
    f_rs['Ruolo_Clean'] = f_rs['Ruolo'].apply(lambda x: map_r.get(str(x)[0].upper(), clean_text(x)))
    f_rs['Fantasquadra'] = f_rs['Fantasquadra'].apply(clean_text).replace(map_n)
    f_rs['Prezzo'] = f_rs['Prezzo'].apply(cv)

    if f_qt is not None:
        f_qt['Nome_Match'] = f_qt['Nome'].apply(get_match_key)
        f_qt['Ruolo_Match'] = f_qt['R'].map(map_r)
        f_qt['Quotazione'] = f_qt['Qt.A'].apply(cv)
        # Match intelligente su Cognome e Ruolo
        f_rs = pd.merge(f_rs, f_qt[['Nome_Match', 'Ruolo_Match', 'Quotazione']], 
                        left_on=['Nome_Match', 'Ruolo_Clean'], right_on=['Nome_Match', 'Ruolo_Match'], 
                        how='left').drop('Ruolo_Match', axis=1)
        f_rs['Quotazione'] = f_rs['Quotazione'].fillna(0)
        f_rs['Plusvalenza'] = f_rs['Quotazione'] - f_rs['Prezzo']

if f_vn is not None:
    f_vn['Squadra'] = f_vn['Squadra'].apply(clean_text).replace(map_n)
    v_cols = [c for c in ['Costo 2026-27', 'Costo 2027-28', 'Costo 2028-29'] if c in f_vn.columns]
    for c in v_cols: f_vn[c] = f_vn[c].apply(cv)
    f_vn['Spesa Complessiva'] = f_vn[v_cols].sum(axis=1)

# --- UI TABS ---
t = st.tabs(["🏆 Classifiche", "💰 Budget", "🧠 Strategia", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

with t[0]: # CLASSIFICHE
    c1, c2 = st.columns(2)
    if f_pt is not None:
        with c2:
            st.subheader("🎯 Punti")
            f_pt['Punti Totali'] = f_pt['Punti Totali'].apply(cv)
            st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali']].sort_values('Posizione').style.background_gradient(subset=['Punti Totali'], cmap='Greens'), hide_index=True)
        # Grafico Classifica
        p_min = f_pt['Punti Totali'].min() - 10
        chart = alt.Chart(f_pt).mark_line(point=True, color='green').encode(
            x=alt.X('Giocatore:N', sort='-y'), y=alt.Y('Punti Totali:Q', scale=alt.Scale(domainMin=p_min))
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)

with t[1]: # BUDGET
    if f_rs is not None:
        st.subheader("💰 Bilancio e Valore Rosa")
        eco = f_rs.groupby('Fantasquadra').agg({'Prezzo': 'sum', 'Quotazione': 'sum'}).reset_index()
        eco.columns = ['Squadra', 'Spesa Rose', 'Valore Mercato']
        eco['Crediti'] = eco['Squadra'].map(bg_ex).fillna(0)
        if f_vn is not None:
            v_sum = f_vn.groupby('Squadra')['Spesa Complessiva'].sum().reset_index()
            eco = pd.merge(eco, v_sum, left_on='Squadra', right_on='Squadra', how='left').fillna(0)
            eco.rename(columns={'Spesa Complessiva': 'Vincoli'}, inplace=True)
        eco['Patrimonio'] = eco['Valore Mercato'] + eco['Crediti'] + eco.get('Vincoli', 0)
        st.dataframe(eco.sort_values('Patrimonio', ascending=False).style.background_gradient(subset=['Valore Mercato'], cmap='YlGn').format({c: "{:g}" for c in eco.columns if c != 'Squadra'}), hide_index=True, use_container_width=True)

with t[3]: # ROSE COLORATE
    if f_rs is not None:
        sq = st.selectbox("Seleziona Squadra:", sorted(f_rs['Fantasquadra'].unique()))
        df_sq = f_rs[f_rs['Fantasquadra'] == sq].copy()
        
        def color_ruoli(row):
            bg = {'PORTIERE':'#E3F2FD','DIFENSORE':'#E8F5E9','CENTROCAMPISTA':'#FFFDE7','ATTACCANTE':'#FFEBEE'}.get(row['Ruolo_Clean'], '#FFFFFF')
            return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
            
        st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo', 'Quotazione', 'Plusvalenza']].style.apply(color_ruoli, axis=1).background_gradient(subset=['Plusvalenza'], cmap='RdYlGn').format({"Prezzo":"{:g}","Quotazione":"{:g}","Plusvalenza":"{:+g}"}), hide_index=True, use_container_width=True)
        st.metric("Plusvalenza Rosa", f"{df_sq['Plusvalenza'].sum():+g}")

with t[5]: # SCAMBI MERITOCRATICI
    st.subheader("🔄 Simulatore Scambi Proporzionale")
    if f_rs is not None:
        c1, c2 = st.columns(2)
        with c1:
            sa = st.selectbox("Squadra A:", sorted(f_rs['Fantasquadra'].unique()), key="sa")
            ga = st.multiselect("Cede da A:", f_rs[f_rs['Fantasquadra']==sa]['Nome'], key="ga")
        with c2:
            sb = st.selectbox("Squadra B:", [s for s in sorted(f_rs['Fantasquadra'].unique()) if s != sa], key="sb")
            gb = st.multiselect("Cede da B:", f_rs[f_rs['Fantasquadra']==sb]['Nome'], key="gb")
        
        if ga and gb:
            # Calcolo valori reali (Prezzo + Vincoli)
            def get_v(n):
                p = f_rs[f_rs['Nome']==n]['Prezzo'].iloc[0]
                v = f_vn[f_vn['Giocatore'].apply(clean_text)==clean_text(n)]['Spesa Complessiva'].sum() if f_vn is not None else 0
                return p + v
            v_a, v_b = sum(get_v(n) for n in ga), sum(get_v(n) for n in gb)
            target = (v_a + v_b) / 2
            ca, cb = target/v_a if v_a > 0 else 1, target/v_b if v_b > 0 else 1
            st.write("---")
            col_a, col_b = st.columns(2)
            with col_a:
                for n in ga: st.success(f"{n} -> Nuovo Valore: **{round(get_v(n)*ca)}**")
            with col_b:
                for n in gb: st.success(f"{n} -> Nuovo Valore: **{round(get_v(n)*cb)}**")
