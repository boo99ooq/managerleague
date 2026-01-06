import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fantalega Manageriale", layout="wide")
st.title("⚽ La mia Fantalega")

st.sidebar.header("Caricamento Dati")
file_caricato = st.sidebar.file_uploader("Carica il file rose muynov25.csv", type="csv")

if file_caricato is not None:
    try:
        # 1. Lettura super-flessibile per Tab, virgole e punti e virgola
        file_caricato.seek(0)
        df = pd.read_csv(file_caricato, sep=None, engine='python', encoding='latin-1', skip_blank_lines=True)
        
        # 2. Pulizia: rimuoviamo righe e colonne completamente vuote
        df = df.dropna(how='all').reset_index(drop=True)
        df.columns = df.columns.str.strip() # Toglie spazi dai nomi delle colonne

        # 3. Uniformiamo i nomi delle colonne
        # Se nel file hai 'Prezzo', lo trasformiamo in 'Costo' per il calcolo
        if 'Prezzo' in df.columns:
            df = df.rename(columns={'Prezzo': 'Costo'})
        
        # 4. Controllo colonne fondamentali
        if 'Fantasquadra' in df.columns and 'Costo' in df.columns:
            # Trasformiamo il Costo in numero (gestendo eventuali errori)
            df['Costo'] = pd.to_numeric(df['Costo'], errors='coerce').fillna(0)

            tab1, tab2 = st.tabs(["📊 Analisi Lega", "🏃 Rose Complete"])

            with tab1:
                st.subheader("Riepilogo Spese e Budget")
                budget_totale = 500
                riepilogo = df.groupby('Fantasquadra')['Costo'].sum().reset_index()
                riepilogo['Crediti Residui'] = budget_totale - riepilogo['Costo']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(riepilogo, use_container_width=True)
                with col2:
                    st.bar_chart(data=riepilogo, x='Fantasquadra', y='Costo')

            with tab2:
                squadre = [s for s in df['Fantasquadra'].unique() if pd.notna(s)]
                scelta = st.selectbox("Seleziona Squadra:", squadre)
                rosa = df[df['Fantasquadra'] == scelta]
                st.write(f"**Giocatori in rosa:** {len(rosa)}")
                st.table(rosa)
        else:
            st.error(f"Colonne non trovate! Il file ha queste colonne: {list(df.columns)}")
            st.info("Assicurati che la prima riga del file contenga: Fantasquadra, Calciatore, Prezzo, Ruolo")

    except Exception as e:
        st.error(f"Errore tecnico: {e}")
else:
    st.info("👋 Carica il file 'rose muynov25.csv' per visualizzare la tua lega!")
