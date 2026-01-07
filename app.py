with t[3]: # TAB ROSE
    if f_rs is not None:
        sq_l = sorted(f_rs['Squadra_C'].unique())
        sq = st.selectbox("Seleziona Squadra:", sq_l, key="rose_view_final")
        
        # 1. Prendiamo i dati della squadra
        df_sq = f_rs[f_rs['Squadra_C'] == sq].copy()
        
        # 2. Funzione di stile corretta (cerca Ruolo_C, se non c'è usa Ruolo)
        def style_r_safe(row):
            # Cerchiamo il ruolo in Ruolo_C o in Ruolo
            r_val = row.get('Ruolo_C', row.get('Ruolo', ''))
            r = str(r_val).upper()
            
            bg = '#FFFFFF' # Default bianco
            if 'PORT' in r: bg = '#E3F2FD'
            elif 'DIF' in r: bg = '#E8F5E9'
            elif 'CEN' in r: bg = '#FFFDE7'
            elif 'ATT' in r: bg = '#FFEBEE'
            
            return [f'background-color: {bg}; color: black; font-weight: bold;'] * len(row)

        # 3. Definiamo le colonne da mostrare (Ruolo_C serve per lo stile, ma lo nascondiamo dopo)
        cols_to_show = ['Ruolo', 'Nome', 'Prezzo', 'Quotazione', 'Plusvalenza']
        
        # Filtriamo assicurandoci che le colonne esistano per non avere altri KeyError
        actual_cols = [c for c in cols_to_show if c in df_sq.columns]
        
        # Visualizzazione con stile applicato all'intero set di dati filtrato
        st.dataframe(
            df_sq[actual_cols].style.apply(style_r_safe, axis=1)
            .background_gradient(subset=['Plusvalenza'], cmap='RdYlGn')
            .format({"Prezzo":"{:g}","Quotazione":"{:g}","Plusvalenza":"{:+g}"}),
            hide_index=True, 
            use_container_width=True
        )
        
        if 'Plusvalenza' in df_sq.columns:
            st.metric("Plusvalenza Totale Rosa", f"{df_sq['Plusvalenza'].sum():+g}")
