import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fantalega Manageriale", layout="wide")
st.title("⚽ Centro Direzionale Fantalega")

# 1. Budget assegnati (per calcoli economici correnti)
budgets_fisso = {
    "GIANNI": 164, "DANI ROBI": 162, "MARCO": 194, "PIETRO": 164,
    "PIERLUIGI": 240, "GIGI": 222, "ANDREA": 165, "GIUSEPPE": 174,
    "MATTEO": 166, "NICHOLAS": 162
}

# 2. Caricamento File nella sidebar
st.sidebar.header("Caricamento Database")
file_rose = st.sidebar.file_uploader("1. Carica Rose Attuali (CSV)", type="csv")
file_vincoli = st.sidebar.file_uploader("2. Carica File Vincoli (CSV)", type="csv")

# FUNZIONE PER LEGGERE I FILE IN MODO SICURO
def carica_dati(file):
    if file is not None:
        file.seek(0)
        return pd.read_csv(file, sep=',', skip_blank_lines=True, encoding='utf-8')
    return None

df_rose = carica_dati(file_rose)
df_vincoli = carica_dati(file_vincoli)

if df_rose is not None:
    # Pulizia Rose
    df_rose.columns = df_rose.columns.str.strip()
    df_rose['Fantasquadra'] = df_rose['Fantasquadra'].str.strip().str.upper()
    df_rose['Prezzo'] = pd.to_numeric(df_rose['Prezzo'], errors='coerce').fillna(0)

    # Creazione Tab (La terza appare solo se carichi il secondo file)
    nomi_tab = ["📊 Potenziale Economico", "🏃 Dettaglio Rose"]
    if df_vincoli is not None:
        nomi_tab.append("📅 Vincoli e Futuro")
    
    tabs = st.tabs(nomi_tab)

    # --- TAB 1: ECONOMIA CORRENTE ---
    with tabs[0]:
        analisi = df_rose.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        analisi.columns = ['Fantasquadra', 'Valore Rosa']
        analisi['Budget Febbraio'] = analisi['Fantasquadra'].map(budgets_fisso).fillna(0)
        analisi['Potenziale Totale'] = analisi['Valore Rosa'] + analisi['Budget Febbraio']
        st.dataframe(analisi.sort_values('Potenziale Totale', ascending=False), hide_index=True, use_container_width=True)
        st.bar_chart(data=analisi, x='Fantasquadra', y=['Valore Rosa', 'Budget Febbraio'])

    # --- TAB 2: DETTAGLIO ROSE ---
    with tabs[1]:
        squadre = sorted(df_rose['Fantasquadra'].unique())
        scelta = st.selectbox("Seleziona Squadra:", squadre)
        rosa = df_rose[df_rose['Fantasquadra'] == scelta].copy()
        st.dataframe(rosa[['Ruolo', 'Nome', 'Prezzo']], use_container_width=True, hide_index=True)

    # --- TAB 3: VINCOLI (Se il file è presente) ---
    if df_vincoli is not None:
        with tabs[2]:
            st.subheader("Analisi Contratti e Scadenze")
            
            # Pulizia Vincoli
            df_vincoli.columns = df_vincoli.columns.str.strip()
            df_vincoli['Squadra'] = df_vincoli['Squadra'].str.strip().str.upper()
            
            # Calcolo impegno per la prossima stagione (2026-27)
            impegno_futuro = df_vincoli.groupby('Squadra')['Costo 2026-27'].sum().reset_index()
            impegno_futuro.columns = ['Squadra', 'Impegno 26/27 (Crediti)']
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.write("**Impegni Già Presi (26/27):**")
                st.dataframe(impegno_futuro, hide_index=True)
            
            with col2:
                # Mostriamo i dettagli dei vincoli per la squadra selezionata
                vincoli_team = df_vincoli[df_vincoli['Squadra'] == scelta]
                st.write(f"**Giocatori Vincolati per {scelta}:**")
                st.table(vincoli_team[['Giocatore', 'Costo 2026-27', 'Durata (anni)']])

else:
    st.info("👋 Per iniziare, carica il file delle Rose nella barra laterale.")
