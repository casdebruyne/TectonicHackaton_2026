import numpy as np
import pandas as pd
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(
    page_title="Bestanden Vergelijker", page_icon="📁", layout="wide"
)

st.title("📁 Bestanden Vergelijken op Laatste Bewerkingsdatum")
st.write(
    "Sleep hier meerdere bestanden naartoe om te zien welke het recentst is bewerkt."
)

# File uploader widget (meerdere bestanden toegestaan)
uploaded_files = st.file_uploader(
    "Kies of drop hier je bestanden", accept_multiple_files=True
)

if uploaded_files:
    file_data = []

    for uploaded_file in uploaded_files:
        # Haal bestandsgrootte op
        file_size_kb = round(uploaded_file.size / 1024, 2)

        # Probeer de 'last modified' datum uit de browser te halen
        # Indien niet beschikbaar, gebruiken we de huidige tijd als ontvangsttijd
        if (
            hasattr(uploaded_file, "last_modified")
            and uploaded_file.last_modified
        ):
            # Timestamp in ms omzetten naar datetime
            last_mod_dt = datetime.fromtimestamp(
                uploaded_file.last_modified / 1000
            )
            last_mod_str = last_mod_dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_mod_dt = datetime.now()
            last_mod_str = "Onbekend (Uploadtijd gebruikt)"

        file_data.append(
            {
                "Bestandsnaam": uploaded_file.name,
                "Grootte (KB)": file_size_kb,
                "Laatst Gewijzigd": last_mod_str,
                "_datetime": last_mod_dt,  # Hulpkolom voor sorteren
            }
        )

    # Zet gegevens om naar een Pandas DataFrame en sorteer op meest recent
    df = pd.DataFrame(file_data)
    df = df.sort_values(by="_datetime", ascending=False).reset_index(drop=True)

    # Toon het meest recente bestand in een highlighted box
    most_recent = df.iloc[0]
    st.success(
        f"🏆 **Meest recente bestand:** `{most_recent['Bestandsnaam']}` (Bewerkt op: {most_recent['Laatst Gewijzigd']})"
    )

    # Verwijder de interne sorteerkolom voor de weergave
    df_display = df.drop(columns=["_datetime"])

    # Toon de resultaten in een nette tabel
    st.subheader("Overzicht van alle bestanden")
    st.dataframe(df_display, use_container_width=True)

else:
    st.info("Upload minimaal één of meerdere bestanden om de vergelijking te starten.")
