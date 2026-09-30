import numpy as np
import pandas as pd
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import docx
import openpyxl
from PIL import Image, ExifTags
import pypdf

st.set_page_config(
    page_title="Bestanden Vergelijker", page_icon="📁", layout="wide"
)

st.title("📁 Bestanden Vergelijken op Laatste Bewerkingsdatum")
st.write(
    "Upload documenten (PDF, Word, Excel, Afbeeldingen) om de echte interne bewerkingsdatum te vergelijken."
)


def get_file_modification_date(uploaded_file):
    """Probeert de interne 'last modified' datum uit het bestand te lezen."""
    file_name = uploaded_file.name.lower()

    try:
        # 1. Voor PDF bestanden
        if file_name.endswith(".pdf"):
            reader = pypdf.PdfReader(uploaded_file)
            meta = reader.metadata
            if meta and meta.modification_date:
                return meta.modification_date.replace(tzinfo=None)

        # 2. Voor Word (.docx) bestanden
        elif file_name.endswith(".docx"):
            doc = docx.Document(uploaded_file)
            prop = doc.core_properties
            if prop.modified:
                return prop.modified

        # 3. Voor Excel (.xlsx) bestanden
        elif file_name.endswith(".xlsx"):
            wb = openpyxl.load_workbook(uploaded_file, read_only=True)
            if wb.properties and wb.properties.modified:
                return wb.properties.modified

        # 4. Voor Afbeeldingen (JPG/PNG - EXIF data)
        elif file_name.endswith((".jpg", ".jpeg", ".png")):
            img = Image.open(uploaded_file)
            exif = img._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    if tag in ["DateTimeOriginal", "DateTime"]:
                        return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")

    except Exception as e:
        pass

    # Fallback als er geen interne metadata gevonden kan worden
    return None


uploaded_files = st.file_uploader(
    "Kies of drop hier je bestanden", accept_multiple_files=True
)

if uploaded_files:
    file_data = []

    for uploaded_file in uploaded_files:
        file_size_kb = round(uploaded_file.size / 1024, 2)

        # Probeer interne datum op te halen
        mod_date = get_file_modification_date(uploaded_file)

        if mod_date:
            last_mod_str = mod_date.strftime("%Y-%m-%d %H:%M:%S")
            is_fallback = False
        else:
            mod_date = datetime.now()
            last_mod_str = "Geen metadata (Uploadtijd gebruikt)"
            is_fallback = True

        file_data.append(
            {
                "Bestandsnaam": uploaded_file.name,
                "Grootte (KB)": file_size_kb,
                "Laatst Gewijzigd": last_mod_str,
                "_datetime": mod_date,
                "_is_fallback": is_fallback,
            }
        )

    df = pd.DataFrame(file_data)
    df = df.sort_values(by="_datetime", ascending=False).reset_index(drop=True)

    # Toon meest recente bestand
    valid_dates = df[df["_is_fallback"] == False]
    if not valid_dates.empty:
        most_recent = valid_dates.iloc[0]
        st.success(
            f"🏆 **Meest recente bestand:** `{most_recent['Bestandsnaam']}` (Bewerkt op: {most_recent['Laatst Gewijzigd']})"
        )
    else:
        st.warning(
            "⚠️️ Kon in geen van de bestanden interne bewerkingsdatum-metadata vinden."
        )

    df_display = df.drop(columns=["_datetime", "_is_fallback"])
    st.subheader("Overzicht van alle bestanden")
    st.dataframe(df_display, use_container_width=True)
