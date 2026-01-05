import streamlit as st
import pandas as pd

# Titolo e stile
st.set_page_config(page_title="Gestore Fantalega", layout="centered")
st.title("⚽ La mia Fantalega Manageriale")

# Sezione Caricamento
st.sidebar.header("Impostazioni")
file_caricato = st.sidebar.file_uploader("Carica il file rose.csv", type="csv")

if file_caricato is not None:
    # Leggiamo i dati del file
try:
    # Prova a leggere con il formato standard UTF-8
    df = pd.read_csv(file_caricato, encoding='utf-8')
except UnicodeDecodeError:
    # Se fallisce, prova con il formato tipico di Excel in Italia
    df = pd.read_csv(file_caricato, encoding='latin-1')

    # Creiamo le schede nell'app
    tab1, tab2 = st.tabs(["📊 Classifica Budget", "🏃 Visualizza Rose"])

    with tab1:
        st.header("Spese per Squadra")
        # Calcoliamo quanto ha speso ogni fantasquadra
        spese = df.groupby('Fantasquadra')['Prezzo'].sum().reset_index()
        st.bar_chart(data=spese, x='Fantasquadra', y='Prezzo')
        st.table(spese)

    with tab2:
        st.header("Dettaglio Giocatori")
        squadre = df['Fantasquadra'].unique()
        scelta = st.selectbox("Scegli una squadra da visualizzare:", squadre)
        
        # Filtriamo i dati
        rosa_filtrata = df[df['Fantasquadra'] == scelta]
        st.dataframe(rosa_filtrata, use_container_width=True)
        
        totale = rosa_filtrata['Prezzo'].sum()
        st.info(f"Questa squadra ha speso in totale: {totale} crediti.")
else:
    st.warning("👋 Benvenuto! Per iniziare, carica il file CSV delle rose nella barra laterale a sinistra.")


