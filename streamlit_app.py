import streamlit as st
import pandas as pd
import numpy as np

# Configurazione pagina
st.set_page_config(page_title="Report Incentivi FV", layout="wide")

def load_irraggiamento():
    # Caricamento file irraggiamento.csv (separatore ;)
    df = pd.read_csv('irraggiamento.csv', sep=';', encoding='latin-1', skiprows=2)
    df.columns = ['Prov', 'Comune', 'Irraggiamento']
    # Pulizia dati: rimuove righe vuote e converte i valori numerici (virgola -> punto)
    df = df.dropna(subset=['Comune', 'Irraggiamento'])
    df['Irraggiamento'] = df['Irraggiamento'].astype(str).str.replace(',', '.').astype(float)
    return df

def get_color(loss_pct):
    if loss_pct < 5:
        return 'background-color: green; color: white'
    elif 5 <= loss_pct < 10:
        return 'background-color: yellow; color: black'
    elif 10 <= loss_pct < 15:
        return 'background-color: orange; color: black'
    elif 15 <= loss_pct < 20:
        return 'background-color: red; color: white'
    elif 20 <= loss_pct < 25:
        return 'background-color: purple; color: white'
    else:
        return 'background-color: black; color: white'

# --- UI SIDEBAR ---
st.sidebar.header("Parametri")
df_irr = load_irraggiamento()
comune_scelto = st.sidebar.selectbox("Seleziona Comune", options=sorted(df_irr['Comune'].unique()))

# Ottieni valore irraggiamento per il comune selezionato
val_irr_annuo = df_irr[df_irr['Comune'] == comune_scelto]['Irraggiamento'].values[0]
st.sidebar.metric("Irraggiamento Annuo (kWh/kWp)", f"{val_irr_annuo:.2f}")

# --- CARICAMENTO FILE ---
uploaded_file = st.file_uploader("Carica il file dei pagamenti (CSV o Excel)", type=['csv', 'xlsx', 'xls'])

if uploaded_file is not None:
    try:
        # Lettura file in base all'estensione
        if uploaded_file.name.endswith('.csv'):
            df_prod = pd.read_csv(uploaded_file)
        else:
            df_prod = pd.read_excel(uploaded_file)
        
        # Pulizia colonne produzione
        # Si assume la presenza di 'ANNO RIFERIMENTO', 'ENERGIA', 'POTENZA IMPIANTO'
        potenza_impianto = df_prod['POTENZA IMPIANTO'].iloc[0]
        
        # Calcolo produzione totale per anno
        report = df_prod.groupby('ANNO RIFERIMENTO')['ENERGIA'].sum().reset_index()
        report.columns = ['Anno', 'Energia Prodotta (kWh)']
        
        # Calcolo Target e %
        target_teorico = val_irr_annuo * potenza_impianto
        report['Target Atteso (kWh)'] = target_teorico
        report['Produzione %'] = (report['Energia Prodotta (kWh)'] / target_teorico) * 100
        report['Perdita %'] = 100 - report['Produzione %']
        
        # Applicazione colori
        def style_rows(row):
            color_style = get_color(row['Perdita %'])
            return [color_style] * len(row)

        st.subheader(f"Analisi Produzione Impianto ({potenza_impianto} kWp) - Comune: {comune_scelto}")
        
        # Visualizzazione tabella formattata
        styled_df = report.style.apply(style_rows, axis=1).format({
            'Energia Prodotta (kWh)': '{:.2f}',
            'Target Atteso (kWh)': '{:.2f}',
            'Produzione %': '{:.2f}%',
            'Perdita %': '{:.2f}%'
        })
        
        st.dataframe(styled_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Errore nella lettura del file: {e}")
else:
    st.info("In attesa del caricamento del file di produzione...")
