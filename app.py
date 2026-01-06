import streamlit as st
import pandas as pd

# 1. Configurazione della pagina
st.set_page_config(page_title="Fantalega Manageriale", layout="wide")
st.title("⚽ La mia Fantalega")

# 2. Caricamento file nella barra laterale
st.sidebar.header("Impostazioni")
file_caricato = st.sidebar.file_uploader("Carica il file delle rose", type="csv")

if file_caricato is not None:
    try:
        # Lettura del file (gestisce Tab, Virgole o Punti e Virgola automaticamente)
        file_caricato.seek(0)
        df = pd.read_csv(file_caricato, sep=None, engine='python', encoding='latin-1')
        
        # PULIZIA DATI
        # Rimuoviamo righe e colonne completamente vuote
        df = df.dropna(how='all').reset_index(drop=True)
        # Togliamo spazi bianchi dai nomi delle colonne e dai dati
        df.columns = df.columns.str.strip()
        
        # Trasformiamo i nomi delle colonne per renderli più belli nell'app
        # Mappiamo i tuoi nomi (minuscoli) a quelli che vogliamo mostrare (Maiuscoli)
        mappa_colonne = {
            'ruolo': 'Ruolo',
            'Calciatore': 'Calciatore',
            'prezzo': 'Prezzo',
            'Fantasquadra': 'Fantasquadra'
        }
        df = df.rename(columns=mappa_colonne)

        # Convertiamo il Prezzo in numero per poter fare i calcoli
        if 'Prezzo' in df.columns:
            df['Prezzo'] = pd.to_numeric(df['Prezzo'], errors='coerce').fillna(0)

        # Creazione delle Tab
        tab1, tab2 = st.tabs(["📊 Classifica e Budget", "🏃 Dettaglio Rose"])

        with tab1:
            st.subheader("Situazione Economica della Lega")
            budget_iniziale = 500 # Puoi modificare questo valore
            
            # Calcolo spese per squadra
            classifica = df.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
            classifica['Residuo'] = budget_iniziale - classifica['Prezzo']
            
            # Grafico e Tabella
            col_graf, col_tab = st.columns([2, 1])
            with col_graf:
                st.bar_chart(data=classifica, x='Fantasquadra', y='Prezzo')
            with col_tab:
                st.dataframe(classifica.sort_values(by='Residuo', ascending=False), hide_index=True)

        with tab2:
            squadre_disponibili = [s for s in df['Fantasquadra'].unique() if pd.notna(s)]
            scelta = st.selectbox("Scegli una Fantasquadra:", squadre_disponibili)
            
            # Filtriamo la rosa della squadra scelta
            rosa_squadra = df[df['Fantasquadra'] == scelta]
            
            # ORDINE COLONNE: Spostiamo il Ruolo per primo come hai chiesto
            ordine_visualizzazione = ['Ruolo', 'Calciatore', 'Prezzo']
            
            # Mostriamo il numero di giocatori per ruolo
            st.write(f"**Totale giocatori:** {len(rosa_squadra.dropna(subset=['Calciatore']))}")
            
            # Visualizzazione tabella pulita
            st.dataframe(
                rosa_squadra[ordine_visualizzazione].sort_values(by='Ruolo'), 
                use_container_width=True, 
                hide_index=True
            )

    except Exception as e:
        st.error(f"Si è verificato un errore durante la lettura: {e}")
else:
    st.info("👋 Benvenuto! Carica il file 'rose muynov25.csv' per iniziare la gestione.")
