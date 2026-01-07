# ... (Codice precedente invariato fino a Tab Classifiche) ...

with t[0]: # CLASSIFICHE + GRAFICI ZOOMATI
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔥 Scontri")
        if f_sc is not None:
            cols_sc = f_sc.select_dtypes(include=['number']).columns
            st.dataframe(f_sc.style.background_gradient(subset=cols_sc, cmap='Blues').set_properties(**{'font-weight': 'bold'}), hide_index=True, use_container_width=True)
    with c2:
        st.subheader("🎯 Punti")
        if f_pt is not None:
            f_pt['Punti Totali'] = f_pt['Punti Totali'].apply(cv)
            f_pt['Media'] = f_pt['Media'].apply(cv)
            st.dataframe(f_pt[['Posizione','Giocatore','Punti Totali','Media']].sort_values('Posizione').style.background_gradient(subset=['Punti Totali'], cmap='Greens').background_gradient(subset=['Media'], cmap='YlGn').format({"Punti Totali": "{:g}", "Media": "{:.2f}"}).set_properties(**{'font-weight': 'bold'}), hide_index=True, use_container_width=True)
    
    if f_pt is not None:
        st.write("---")
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("📊 Gap Punti Totali (Zoom)")
            # Calcoliamo un minimo dinamico per esaltare il distacco
            min_punti = f_pt['Punti Totali'].min() * 0.95 
            st.bar_chart(f_pt.set_index('Giocatore')['Punti Totali'], y_label="Punti", color="#2e7d32")
            st.caption("Nota: La scala è ottimizzata per evidenziare il distacco tra le squadre.")

        with col_g2:
            st.subheader("📈 Differenza Media Voto")
            st.line_chart(f_pt.set_index('Giocatore')['Media'], y_label="Media", color="#ff9800")

# ... (Resto del codice invariato) ...
