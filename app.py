from datetime import datetime
import io
import json
import sqlite3

import docx
import openpyxl
import pandas as pd
import pypdf
import streamlit as st
from PIL import ExifTags, Image

# ---------------------------------------------------------------
# Configuratie & Constanten
# ---------------------------------------------------------------
st.set_page_config(
    page_title="Kennis Betrouwbaarheid", page_icon="🛡️", layout="wide"
)

DB = "kennis.db"

GEWICHTEN = {
    "Actualiteit": 30,
    "Auteur": 20,
    "AI-percentage": 25,
    "Metadata aanwezig": 15,
    "Bestandstype": 10,
}

TYPE_SCORE = {
    "pdf": 1.0,
    "docx": 0.9,
    "xlsx": 0.8,
    "jpg": 0.4,
    "jpeg": 0.4,
    "png": 0.4,
}

TALEN = ["Nederlands", "Frans", "Engels", "Duits", "Andere"]
LANDEN = [
    "België",
    "Nederland",
    "Frankrijk",
    "Duitsland",
    "Verenigd Koninkrijk",
    "Andere",
]


# ---------------------------------------------------------------
# Database Functies
# ---------------------------------------------------------------
def get_con():
    con = sqlite3.connect(DB)
    con.execute(
        """CREATE TABLE IF NOT EXISTS documenten (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bestandsnaam TEXT, onderwerp TEXT, taal TEXT, auteur TEXT, land TEXT,
            ai_percentage INTEGER, bestandsdatum TEXT, toegevoegd_op TEXT,
            score INTEGER, uitleg TEXT)"""
    )
    return con


def lees_database():
    con = get_con()
    df = pd.read_sql("SELECT * FROM documenten ORDER BY score DESC", con)
    con.close()
    return df


# ---------------------------------------------------------------
# Hulpfuncties: Metadata & Tekst & AI Detectie
# ---------------------------------------------------------------
def lees_metadata(naam, data):
    """Geeft (datum, auteur) uit het bestand zelf, of (None, None)."""
    naam = naam.lower()
    try:
        if naam.endswith(".pdf"):
            m = pypdf.PdfReader(io.BytesIO(data)).metadata
            if m:
                d = m.modification_date
                return (d.replace(tzinfo=None) if d else None), m.author
        elif naam.endswith(".docx"):
            p = docx.Document(io.BytesIO(data)).core_properties
            return p.modified, (p.last_modified_by or p.author)
        elif naam.endswith(".xlsx"):
            p = openpyxl.load_workbook(
                io.BytesIO(data), read_only=True
            ).properties
            return p.modified, (p.lastModifiedBy or p.creator)
        elif naam.endswith((".jpg", ".jpeg", ".png")):
            exif = Image.open(io.BytesIO(data))._getexif()
            if exif:
                for tag_id, waarde in exif.items():
                    if ExifTags.TAGS.get(tag_id) in (
                        "DateTimeOriginal",
                        "DateTime",
                    ):
                        return (
                            datetime.strptime(waarde, "%Y:%m:%d %H:%M:%S"),
                            None,
                        )
    except Exception:
        pass
    return None, None


def haal_tekst_uit_bestand(naam, data):
    """Haalt de leesbare tekst uit PDF, DOCX of TXT bestanden."""
    naam = naam.lower()
    tekst = ""
    try:
        if naam.endswith(".pdf"):
            reader = pypdf.PdfReader(io.BytesIO(data))
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    tekst += t + "\n"
        elif naam.endswith(".docx"):
            doc = docx.Document(io.BytesIO(data))
            tekst = "\n".join([p.text for p in doc.paragraphs])
        elif naam.endswith(".txt"):
            tekst = data.decode("utf-8", errors="ignore")
    except Exception:
        pass
    return tekst.strip()


def detecteer_ai_percentage(tekst):
    """Analyseert tekststructuur om een automatische schatting van AI-content te maken."""
    if not tekst or len(tekst) < 30:
        return 0  # Te weinig tekst aanwezig om betrouwbaar te scannen

    woorden = tekst.split()
    zinnen = [z for z in tekst.split(".") if z.strip()]

    if not zinnen:
        return 0

    gemiddelde_zinslengte = len(woorden) / len(zinnen)

    # Signaalwoorden die frequent in AI-gegenereerde teksten voorkomen
    ai_signaalwoorden = [
        "conclusie",
        "daarnaast",
        "bovendien",
        "belangrijkste",
        "optimaliseren",
        "samenvattend",
        "essentieel",
        "sleutelrol",
        "inleiding",
        "kortom",
        "tot slot",
    ]

    matches = sum(
        1 for w in woorden if w.lower().strip(",.") in ai_signaalwoorden
    )

    # Bepaal een geschat AI-percentage op basis van woordgebruik en zinsbouw
    score = (matches / len(woorden)) * 500 + (
        15 if 14 <= gemiddelde_zinslengte <= 24 else 0
    )
    return min(100, max(0, int(score)))


# ---------------------------------------------------------------
# Score Berekening (1-100)
# ---------------------------------------------------------------
def bereken_score(d):
    f = {}
    if d["datum"]:
        leeftijd = (datetime.now() - d["datum"]).days
        f["Actualiteit"] = max(0, 1 - leeftijd / 1095)  # na 3 jaar = 0
    else:
        f["Actualiteit"] = 0.2  # onbekend = laag

    if not d["auteur"].strip():
        f["Auteur"] = 0.0
    elif (
        d["meta_auteur"]
        and d["meta_auteur"].strip().lower() == d["auteur"].strip().lower()
    ):
        f["Auteur"] = 1.0  # naam komt overeen met het bestand zelf
    else:
        f["Auteur"] = 0.6  # ingevuld maar niet te controleren

    f["AI-percentage"] = 1 - d["ai"] / 100
    f["Metadata aanwezig"] = 1.0 if d["datum"] else 0.0
    f["Bestandstype"] = TYPE_SCORE.get(
        d["bestandsnaam"].rsplit(".", 1)[-1].lower(), 0.3
    )

    punten = {k: round(f[k] * GEWICHTEN[k], 1) for k in f}
    score = max(1, min(100, round(sum(punten.values()))))
    return score, punten


def rating(score):
    if score >= 75:
        return "🟢 Betrouwbaar"
    if score >= 50:
        return "🟠 Let op"
    return "🔴 Niet vertrouwen"


# ---------------------------------------------------------------
# Navigatie & Session State
# ---------------------------------------------------------------
st.sidebar.title("🛡️ Kennis Betrouwbaarheid")
pagina = st.sidebar.radio(
    "Pagina",
    ["1️⃣ Uploaden", "2️⃣ Beoordelen & opslaan", "3️⃣ Zoeken"],
    key="pagina",
)

if "wachtrij" not in st.session_state:
    st.session_state.wachtrij = []


# ===============================================================
# PAGINA 1: Uploaden + Gegevens invullen (Automatische AI Detectie)
# ===============================================================
if pagina.startswith("1"):
    st.title("📤 Documenten uploaden")
    st.write("Upload documenten en vul per document de gegevens in.")

    bestanden = st.file_uploader(
        "Kies of drop hier je bestanden (PDF, Word, Excel, afbeeldingen)",
        accept_multiple_files=True,
    )

    invoer = []
    for i, f in enumerate(bestanden or []):
        with st.expander(f"📄 {f.name}", expanded=True):
            c1, c2 = st.columns(2)
            onderwerp = c1.text_input(
                "Onderwerp", key=f"onderwerp_{i}_{f.name}"
            )
            auteur = c2.text_input("Naam auteur", key=f"auteur_{i}_{f.name}")
            c3, c4 = st.columns(2)
            taal = c3.selectbox("Taal", TALEN, key=f"taal_{i}_{f.name}")
            land = c4.selectbox("Land", LANDEN, key=f"land_{i}_{f.name}")

            invoer.append((f, onderwerp, auteur, taal, land))

    if invoer:
        if st.button("➡️ Doorsturen naar beoordeling", type="primary"):
            ontbreekt = [f.name for f, o, *_ in invoer if not o.strip()]
            if ontbreekt:
                st.error("Vul het onderwerp in voor: " + ", ".join(ontbreekt))
            else:
                with st.spinner(
                    "🔍 Bestanden analyseren & AI-percentage berekenen..."
                ):
                    for f, onderwerp, auteur, taal, land in invoer:
                        bytes_data = f.getvalue()

                        # 1. Lees metadata uit het bestand (datum & auteur)
                        datum, meta_auteur = lees_metadata(f.name, bytes_data)

                        # 2. Haal tekst op & bereken automatisch AI %
                        tekst = haal_tekst_uit_bestand(f.name, bytes_data)
                        ai_percentage = detecteer_ai_percentage(tekst)

                        st.session_state.wachtrij.append(
                            {
                                "bestandsnaam": f.name,
                                "onderwerp": onderwerp.strip(),
                                "auteur": auteur,
                                "taal": taal,
                                "land": land,
                                "ai": ai_percentage,  # Automatisch berekend!
                                "datum": datum,
                                "meta_auteur": meta_auteur,
                            }
                        )
                st.success(
                    f"{len(invoer)} document(en) geanalyseerd en klaargezet. Ga naar **2️⃣ Beoordelen & opslaan** in de sidebar."
                )
    else:
        st.info("Upload minstens één bestand om te starten.")


# ===============================================================
# PAGINA 2: Score berekenen en opslaan in database
# ===============================================================
elif pagina.startswith("2"):
    st.title("🧮 Beoordelen & opslaan")
    wachtrij = st.session_state.wachtrij

    if not wachtrij:
        st.info(
            "Er staan geen documenten klaar. Upload eerst documenten op pagina 1."
        )
    else:
        resultaten = []
        for d in wachtrij:
            score, punten = bereken_score(d)
            resultaten.append((d, score, punten))

        overzicht = pd.DataFrame(
            [
                {
                    "Document": d["bestandsnaam"],
                    "Onderwerp": d["onderwerp"],
                    "Auteur": d["auteur"] or "⚠️ onbekend",
                    "Bestandsdatum": (
                        d["datum"].strftime("%Y-%m-%d")
                        if d["datum"]
                        else "Onbekend"
                    ),
                    "AI %": d["ai"],
                    "Score": score,
                    "Rating": rating(score),
                }
                for d, score, _ in resultaten
            ]
        )
        st.dataframe(
            overzicht,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Score", min_value=0, max_value=100, format="%d"
                )
            },
        )

        st.subheader("🔍 Waarom deze score?")
        keuze = st.selectbox(
            "Kies een document", [d["bestandsnaam"] for d, _, _ in resultaten]
        )
        d, score, punten = next(
            r for r in resultaten if r[0]["bestandsnaam"] == keuze
        )
        c1, c2 = st.columns([1, 2])
        c1.metric("Betrouwbaarheid", f"{score} / 100")
        c1.write(rating(score))
        c2.bar_chart(pd.Series(punten, name="Punten"))

        b1, b2 = st.columns(2)
        if b1.button("💾 Opslaan in database", type="primary"):
            con = get_con()
            for d, score, punten in resultaten:
                con.execute(
                    """INSERT INTO documenten
                    (bestandsnaam, onderwerp, taal, auteur, land, ai_percentage,
                     bestandsdatum, toegevoegd_op, score, uitleg)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (
                        d["bestandsnaam"],
                        d["onderwerp"],
                        d["taal"],
                        d["auteur"],
                        d["land"],
                        d["ai"],
                        (
                            d["datum"].strftime("%Y-%m-%d")
                            if d["datum"]
                            else None
                        ),
                        datetime.now().strftime("%Y-%m-%d %H:%M"),
                        score,
                        json.dumps(punten),
                    ),
                )
            con.commit()
            con.close()
            st.session_state.wachtrij = []
            st.success("Opgeslagen! Zoek ze terug op pagina 3.")
            st.balloons()
        if b2.button("🗑️ Wachtrij leegmaken"):
            st.session_state.wachtrij = []
            st.rerun()


# ===============================================================
# PAGINA 3: Zoeken & Filteren
# ===============================================================
else:
    st.title("🔎 Zoeken in de kennisbank")
    df = lees_database()

    if df.empty:
        st.info(
            "De database is nog leeg. Voeg eerst documenten toe via pagina 1 en 2."
        )
    else:
        zoek = st.text_input("Zoek op onderwerp, bestandsnaam of auteur")
        c1, c2, c3 = st.columns(3)
        talen = c1.multiselect("Taal", sorted(df["taal"].unique()))
        landen = c2.multiselect("Land", sorted(df["land"].unique()))
        min_score = c3.slider("Minimale score", 1, 100, 1)

        res = df.copy()
        if zoek:
            z = zoek.lower()
            mask = (
                res["onderwerp"].str.lower().str.contains(z, na=False)
                | res["bestandsnaam"].str.lower().str.contains(z, na=False)
                | res["auteur"].str.lower().str.contains(z, na=False)
            )
            res = res[mask]
        if talen:
            res = res[res["taal"].isin(talen)]
        if landen:
            res = res[res["land"].isin(landen)]
        res = res[res["score"] >= min_score].sort_values(
            "score", ascending=False
        )
        res["Rating"] = res["score"].apply(rating)

        st.write(f"**{len(res)}** resultaat/resultaten")
        st.dataframe(
            res[[
                "bestandsnaam",
                "onderwerp",
                "auteur",
                "taal",
                "land",
                "ai_percentage",
                "score",
                "Rating",
            ]],
            hide_index=True,
            use_container_width=True,
            column_config={
                "score": st.column_config.ProgressColumn(
                    "Score", min_value=0, max_value=100, format="%d"
                ),
                "ai_percentage": "AI %",
            },
        )

        if not res.empty:
            st.subheader("🔍 Waarom deze score?")
            opties = {
                f"{r.bestandsnaam} ({r.onderwerp})": r for r in res.itertuples()
            }
            r = opties[st.selectbox("Kies een document", list(opties))]
            k1, k2 = st.columns([1, 2])
            k1.metric("Betrouwbaarheid", f"{r.score} / 100")
            k1.write(rating(r.score))
            k1.write(f"**Auteur:** {r.auteur or '⚠️ onbekend'}")
            k1.write(f"**Bestandsdatum:** {r.bestandsdatum or 'onbekend'}")
            k2.bar_chart(pd.Series(json.loads(r.uitleg), name="Punten"))

        st.download_button(
            "⬇️ Download database als CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="kennisbank.csv",
            mime="text/csv",
        )
