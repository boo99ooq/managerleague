import streamlit as st
import pandas as pd
import os
import altair as alt

# 1. SETUP UI E STILE (RIPRISTINO GOLDEN)
st.set_page_config(page_title="MuyFantaManager", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: white; }
    div[data-testid="stDataFrame"] * { color: #1a1a1a !important; font-weight: bold !important; }
</style>
""", unsafe_allow_html=True)

st.title("⚽ MuyFantaManager")

# Mappature Squadre
bg_ex = {"GIANNI":102.5,"DANI ROBI":164.5,"MARCO":131.0,"PIETRO":101.5,"PIERLUIGI":105.0,"GIGI":232.5,"ANDREA":139.0,"GIUSEPPE":136.5,"MATTEO":166.5,"NICHOLAS":113.0}
map_n = {"NICO FABIO": "NICHOLAS", "MATTEO STEFANO": "MATTEO", "NICHO": "NICHOLAS", "DANI ROBI": "DANI ROBI"}

# Funzione di caricamento intelligente (salta righe vuote e corregge errori)
def ld(f):
    if not os.path.exists(f): return None
    try:
        df = pd.read_csv(f, sep=',', engine='python', skip_blank_lines=True)
        if df.empty: return None
        # Se la prima colonna è Unnamed, significa che c'era una riga vuota vera e propria
        if df.columns[0].startswith('Unnamed'):
            df = pd.read_csv(f, sep=',', engine='python', skiprows=1)
        df.columns = [c.strip() for c in df.columns]
        return df.dropna(how='all')
    except:
        return None

def cv(v):
    if pd.isna(v): return 0.0
    try:
        return float(str(v).replace('"', '').replace(',', '.').strip())
    except: return 0.0

# 2. CARICAMENTO DATI
f_pt = ld("classificapunti.csv")
f_rs = ld("rose_complete.csv")
f_vn = ld("vincoli.csv")
f_sc = ld("scontridiretti.csv")

# 3. INTERFACCIA A SCHEDE (TABS)
# Usiamo un try/except generale per evitare che l'intera pagina sparisca
try:
    tabs = st.tabs(["🏆 Classifiche", "💰 Budget", "🏃 Rose", "📅 Vincoli", "🔄 Scambi"])

    # --- TAB 0: CLASSIFICHE ---
    with tabs[0]:
        if f_pt is not None:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🎯 Punti Totali")
                # Pulizia specifica per i tuoi dati (es: "1.074,5")
                f_pt['Punti_Clean'] = f_pt['Punti Totali'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).apply(cv)
                st.dataframe(f_pt[['Posizione','Giocatore','Punti_Clean']].sort_values('Posizione').style.background_gradient(subset=['Punti_Clean'], cmap='Greens'), hide_index=True)
            with c2:
                st.subheader("📈 Trend Classifica")
                p_min = f_pt['Punti_Clean'].min() - 10
                chart = alt.Chart(f_pt).mark_line(point=True, color='green').encode(
                    x=alt.X('Giocatore:N', sort='-y'),
                    y=alt.Y('Punti_Clean:Q', scale=alt.Scale(domainMin=p_min))
                ).properties(height=300)
                st.altair_chart(chart, use_container_width=True)
        else:
            st.warning("File 'classificapunti.csv' non trovato.")

    # --- TAB 1: BUDGET ---
    with tabs[1]:
        if f_rs is not None:
            st.subheader("💰 Bilancio Squadre")
            f_rs['Prezzo_N'] = f_rs['Prezzo'].apply(cv)
            f_rs['Squadra_N'] = f_rs['Fantasquadra'].str.upper().replace(map_n)
            bu = f_rs.groupby('Squadra_N')['Prezzo_N'].sum().reset_index()
            bu['Extra'] = bu['Squadra_N'].map(bg_ex).fillna(0)
            bu['Totale'] = bu['Prezzo_N'] + bu['Extra']
            st.dataframe(bu.sort_values('Totale', ascending=False).style.background_gradient(subset=['Totale'], cmap='YlOrRd'), hide_index=True)
        else:
            st.warning("File 'rose_complete.csv' non trovato.")

    # --- TAB 2: ROSE ---
    with tabs[2]:
        if f_rs is not None:
            lista_sq = sorted(f_rs['Squadra_N'].unique())
            sq_sel = st.selectbox("Scegli Squadra:", lista_sq)
            df_sq = f_rs[f_rs['Squadra_N'] == sq_sel].copy()
            
            def color_ruoli(row):
                r = str(row['Ruolo']).upper()
                bg = '#E3F2FD' if 'PORT' in r else '#E8F5E9' if 'DIF' in r else '#FFFDE7' if 'CEN' in r else '#FFEBEE' if 'ATT' in r else '#FFFFFF'
                return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)
            
            st.dataframe(df_sq[['Ruolo', 'Nome', 'Prezzo']].style.apply(color_ruoli, axis=1), hide_index=True, use_container_width=True)

    # --- TAB 3: VINCOLI ---
    with tabs[3]:
        if f_vn is not None:
            st.subheader("📅 Contratti Pluriennali")
            st.dataframe(f_vn.style.set_properties(**{'font-weight': 'bold'}), hide_index=True)

    # --- TAB 4: SCAMBI ---
    with tabs[4]:
        st.subheader("🔄 Simulatore Scambi")
        st.info("Usa questa sezione per calcolare il valore dei giocatori dopo uno scambio proporzionale.")
        # Logica semplificata per evitare crash
        if f_rs is not None:
            s_a = st.selectbox("Squadra A:", sorted(f_rs['Squadra_N'].unique()), key="sa_p")
            g_a = st.multiselect("Giocatori A:", f_rs[f_rs['Squadra_N']==s_a]['Nome'], key="ga_p")
            if g_a:
                st.write(f"Hai selezionato {len(g_a)} giocatori.")

except Exception as e:
    st.error(f"Si è verificato un errore nel caricamento dell'interfaccia: {e}")
