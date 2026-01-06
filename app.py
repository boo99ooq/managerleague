import streamlit as st
import pandas as pd

# 1. Configurazione della pagina
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")
st.title("⚽ La mia Fantalega Manageriale")

# 2. Definizione dei Budget di Febbraio
# Nota: ho aggiornato i nomi in MAIUSCOLO per combaciare con il nuovo file
# "Dany Roby" del file precedente ora è "DANI ROBI"
budgets_fisso = {
    "GIANNI": 164,
    "DANI ROBI": 162,
    "MARCO": 194,
    "PIETRO": 164,
    "PIERLUIGI": 240,
    "GIGI": 222,
    "ANDREA": 165,
    "GIUSEPPE": 174,
    "MATTEO": 166,
    "NICHOLAS": 162
}

# 3. Caricamento file nella barra laterale
st.sidebar.header("Gestione Dati")
file_caricato = st.sidebar.file_uploader("Carica il file: nuove rose muynov25.csv", type="csv")

if file_caricato is not None:
    try:
        # Lettura flessibile del file
        file_caricato.seek(0)
        df = pd.read_csv(file_caricato, sep=None, engine='python', encoding='utf-8')
        
        # PULIZIA DATI
        df = df.dropna(how='all').reset_index(drop=True)
        df.columns = df.columns.str.strip() # Toglie spazi dai nomi delle colonne
        
        # Mappatura per adattare il nuovo file (Nome -> Calciatore, Prezzo -> Valore Rosa)
        mappa_colonne = {
            'Nome': 'Calciatore',
            'Prezzo': 'Valore Rosa'
        }
        df = df.rename(columns=mappa_colonne)

        # Uniformiamo i nomi delle squadre (tutto maiuscolo e senza spazi extra)
        if 'Fantasquadra' in df.columns:
            df['Fantasquadra'] = df['Fantasquadra'].astype(str).str.strip().str.upper()

        # Convertiamo il valore della rosa in numero
        if 'Valore Rosa' in df.columns:
            df['Valore Rosa'] = pd.to_numeric(df['Valore Rosa'], errors='coerce').fillna(0)

        # Creazione delle Tab
        tab1, tab2 = st.tabs(["📊 Potenziale Economico", "🏃 Dettaglio Rose"])

        with tab1:
            st.subheader("Analisi Finanziaria Febbraio")
            
            # Calcolo valore attuale delle rose
            analisi = df.groupby('Fantasquadra')['Valore Rosa'].sum().reset_index()
            
            # Aggiungiamo il Budget di Febbraio incrociando i nomi
            analisi['Budget Febbraio'] = analisi['Fantasquadra'].map(budgets_fisso).fillna(0)
            
            # Calcolo Potenziale Totale
            analisi['Potenziale Totale'] = analisi['Valore Rosa'] + analisi['Budget Febbraio']
            analisi = analisi.sort_values(by='Potenziale Totale', ascending=False)
            
            col_graf, col_tab = st.columns([2, 1.5])
            with col_graf:
                st.write("### Composizione (Rosa + Budget)")
                # Grafico a barre sovrapposte
                st.bar_chart(data=analisi, x='Fantasquadra', y=['Valore Rosa', 'Budget Febbraio'])
            with col_tab:
                st.write("### Riepilogo Crediti")
                st.dataframe(analisi, hide_index=True, use_container_width=True)

        with tab2:
            squadre_disponibili = sorted([s for s in df['Fantasquadra'].unique() if pd.notna(s)])
            scelta = st.selectbox("Scegli una Fantasquadra:", squadre_disponibili)
            
            rosa_squadra = df[df['Fantasquadra'] == scelta].copy()
            budget_team = budgets_fisso.get(scelta, 0)
            valore_team = rosa_squadra['Valore Rosa'].sum()
            
            # Visualizzazione delle metriche principali
            c1, c2, c3 = st.columns(3)
            c1.metric("Valore Rosa Attuale", f"{int(valore_team)}")
            c2.metric("Budget Febbraio", f"{int(budget_team)}")
            c3.metric("Potenziale d'acquisto", f"{int(valore_team + budget_team)}")

            # Ordine colonne: Ruolo per primo, poi Nome e Prezzo
            ordine_visualizzazione = ['Ruolo', 'Calciatore', 'Valore Rosa']
            
            # Ordinamento logico dei ruoli (Portieri -> Difensori -> Centrocampisti -> Attaccanti)
            ordine_ruoli = {'Portiere': 1, 'Difensore': 2, 'Centrocampista': 3, 'Attaccante': 4, 'Giovani': 5}
            rosa_squadra['sort_key'] = rosa_squadra['Ruolo'].map(ordine_ruoli).fillna(99)
            
            st.dataframe(
                rosa_squadra.sort_values(by='sort_key')[ordine_visualizzazione], 
                use_container_width=True, 
                hide_index=True
            )

    except Exception as e:
        st.error(f"Si è verificato un errore: {e}")
        st.info("Assicurati di aver caricato il file 'nuove rose muynov25.csv'")
else:
    st.info("👋 Benvenuto! Carica il file aggiornato delle rose per visualizzare la situazione della lega.")
