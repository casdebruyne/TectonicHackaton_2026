import base64
import io
import json
import sqlite3
from datetime import datetime

import docx
import openpyxl
import pandas as pd
import pypdf
import streamlit as st
from PIL import ExifTags, Image

st.set_page_config(page_title="Kennis Betrouwbaarheid", page_icon="🛡️", layout="wide")

DB = "kennis.db"
DREMPEL = 75  # vanaf deze score telt een document als "betrouwbaar"

# Maximale punten per factor (samen 100)
GEWICHTEN = {
    "Actualiteit": 10,
    "Auteur": 30,
    "AI-percentage": 30,
    "Metadata aanwezig": 15,
    "Bestandstype": 15,
}
TYPE_SCORE = {"pdf": 1.0, "docx": 0.9, "xlsx": 0.8, "jpg": 0.4, "jpeg": 0.4, "png": 0.4}
MIME = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
}
TALEN = ["Nederlands", "Frans", "Engels", "Duits", "Andere"]
LANDEN = ["België", "Nederland", "Frankrijk", "Duitsland", "Verenigd Koninkrijk", "Andere"]


# ---------------------------------------------------------------
# Stijl
# ---------------------------------------------------------------
st.markdown(
    """
<style>
section[data-testid="stSidebar"] { border-right: 1px solid rgba(128,128,128,.2); }
section[data-testid="stSidebar"] .stButton > button {
    justify-content: flex-start; text-align: left; border-radius: 12px;
    padding: .65rem 1rem; font-weight: 600; margin-bottom: .15rem;
}
.brand { font-size: 1.5rem; font-weight: 800; line-height: 1.1;
    background: linear-gradient(90deg,#FF4B4B,#FF8C42); -webkit-background-clip: text;
    -webkit-text-fill-color: transparent; }
.brand-sub { opacity: .6; font-size: .85rem; margin-bottom: .8rem; }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------
# Database
# ---------------------------------------------------------------
def get_con():
    con = sqlite3.connect(DB)
    con.execute(
        """CREATE TABLE IF NOT EXISTS documenten (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bestandsnaam TEXT, onderwerp TEXT, taal TEXT, auteur TEXT, land TEXT,
            ai_percentage INTEGER, bestandsdatum TEXT, toegevoegd_op TEXT,
            score INTEGER, uitleg TEXT, inhoud BLOB)"""
    )
    kolommen = [r[1] for r in con.execute("PRAGMA table_info(documenten)")]
    if "inhoud" not in kolommen:  # oude database bijwerken
        con.execute("ALTER TABLE documenten ADD COLUMN inhoud BLOB")
    return con


def lees_database():
    con = get_con()
    df = pd.read_sql(
        """SELECT id, bestandsnaam, onderwerp, taal, auteur, land, ai_percentage,
                  bestandsdatum, toegevoegd_op, score, uitleg
           FROM documenten ORDER BY score DESC""",
        con,
    )
    con.close()
    return df


def lees_inhoud(doc_id):
    con = get_con()
    rij = con.execute("SELECT inhoud FROM documenten WHERE id=?", (int(doc_id),)).fetchone()
    con.close()
    return rij[0] if rij else None


def aantal_betrouwbaar(auteur):
    """Aantal documenten van deze auteur in de database met score >= DREMPEL."""
    if not auteur.strip():
        return 0
    con = get_con()
    n = con.execute(
        "SELECT COUNT(*) FROM documenten WHERE lower(trim(auteur)) = ? AND score >= ?",
        (auteur.strip().lower(), DREMPEL),
    ).fetchone()[0]
    con.close()
    return n


# ---------------------------------------------------------------
# Metadata uit het bestand zelf
# ---------------------------------------------------------------
def lees_metadata(naam, data):
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
            p = openpyxl.load_workbook(io.BytesIO(data), read_only=True).properties
            return p.modified, (p.lastModifiedBy or p.creator)
        elif naam.endswith((".jpg", ".jpeg", ".png")):
            exif = Image.open(io.BytesIO(data))._getexif()
            if exif:
                for tag_id, waarde in exif.items():
                    if ExifTags.TAGS.get(tag_id) in ("DateTimeOriginal", "DateTime"):
                        return datetime.strptime(waarde, "%Y:%m:%d %H:%M:%S"), None
    except Exception:
        pass
    return None, None


# ---------------------------------------------------------------
# Score (1-100)
# ---------------------------------------------------------------
def bereken_score(d):
    f = {}

    # Actualiteit: daalt traag (halveert per 5 jaar) en zakt nooit onder 40%
    if d["datum"]:
        jaren = (datetime.now() - d["datum"]).days / 365
        f["Actualiteit"] = max(0.4, 0.5 ** (jaren / 5))
    else:
        f["Actualiteit"] = 0.3

    # Auteur: gebaseerd op aantal betrouwbare documenten van deze auteur in de database
    if not d["auteur"].strip():
        f["Auteur"] = 0.0
    else:
        n = aantal_betrouwbaar(d["auteur"])
        f["Auteur"] = 0.2 + 0.8 * min(1, n / 5)  # nieuwe auteur 20%, vanaf 5 betrouwbare docs 100%

    f["AI-percentage"] = 1 - d["ai"] / 100
    f["Metadata aanwezig"] = 1.0 if d["datum"] else 0.0
    f["Bestandstype"] = TYPE_SCORE.get(d["bestandsnaam"].rsplit(".", 1)[-1].lower(), 0.3)

    punten = {k: round(f[k] * GEWICHTEN[k], 1) for k in f}
    score = max(1, min(100, round(sum(punten.values()))))
    return score, punten


def rating(score):
    if score >= DREMPEL:
        return "🟢 Betrouwbaar"
    if score >= 50:
        return "🟠 Let op"
    return "🔴 Niet vertrouwen"


# ---------------------------------------------------------------
# Document openen (voorbeeld + download)
# ---------------------------------------------------------------
def toon_document(naam, data):
    ext = naam.rsplit(".", 1)[-1].lower()
    st.download_button(
        f"⬇️ Open / download {naam}", data, file_name=naam,
        mime=MIME.get(ext, "application/octet-stream"), type="primary",
    )
    if ext == "pdf":
        b64 = base64.b64encode(data).decode()
        st.markdown(
            f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="700"></iframe>',
            unsafe_allow_html=True,
        )
    elif ext in ("jpg", "jpeg", "png"):
        st.image(data, use_container_width=True)
    elif ext == "docx":
        tekst = "\n\n".join(p.text for p in docx.Document(io.BytesIO(data)).paragraphs if p.text.strip())
        st.text_area("Inhoud", tekst or "(geen tekst gevonden)", height=400)
    elif ext == "xlsx":
        for blad, tabel in pd.read_excel(io.BytesIO(data), sheet_name=None).items():
            st.caption(f"Blad: {blad}")
            st.dataframe(tabel, use_container_width=True)


# ---------------------------------------------------------------
# Sidebar / navigatie
# ---------------------------------------------------------------
st.session_state.setdefault("pagina", "upload")
st.session_state.setdefault("wachtrij", [])
st.session_state.setdefault("up_nr", 0)

df_all = lees_database()
n_wacht = len(st.session_state.wachtrij)

with st.sidebar:
    st.markdown('<div class="brand">🛡️ Kennis<br>Betrouwbaarheid</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">Vind it. Begrijp it. Vertrouw it.</div>', unsafe_allow_html=True)

    menu = [
        ("upload", "📤", "1 · Uploaden"),
        ("beoordeel", "🧮", f"2 · Beoordelen" + (f"  ({n_wacht})" if n_wacht else "")),
        ("zoek", "🔎", "3 · Zoeken"),
    ]
    for sleutel, icoon, label in menu:
        actief = st.session_state.pagina == sleutel
        if st.button(f"{icoon}  {label}", key=f"nav_{sleutel}", use_container_width=True,
                     type="primary" if actief else "secondary"):
            st.session_state.pagina = sleutel
            st.rerun()

    st.divider()
    s1, s2 = st.columns(2)
    s1.metric("In database", len(df_all))
    s2.metric("Gem. score", f"{df_all['score'].mean():.0f}" if len(df_all) else "–")
    st.caption(f"⏳ {n_wacht} document(en) in wachtrij")
    st.caption(f"🟢 Betrouwbaar = score ≥ {DREMPEL}")

pagina = st.session_state.pagina


def ga_naar(p):
    st.session_state.pagina = p


# ===============================================================
# PAGINA 1: Uploaden
# ===============================================================
if pagina == "upload":
    st.title("📤 Documenten uploaden")
    st.write("Upload documenten en vul per document de gegevens in.")

    if st.session_state.get("flash"):
        st.success(st.session_state.pop("flash"))

    bestanden = st.file_uploader(
        "Kies of drop hier je bestanden (PDF, Word, Excel, afbeeldingen)",
        accept_multiple_files=True,
        key=f"up_{st.session_state.up_nr}",
    )

    invoer = []
    for i, f in enumerate(bestanden or []):
        with st.expander(f"📄 {f.name}", expanded=True):
            c1, c2 = st.columns(2)
            onderwerp = c1.text_input("Onderwerp", key=f"onderwerp_{i}_{f.name}")
            auteur = c2.text_input("Naam auteur", key=f"auteur_{i}_{f.name}")
            c3, c4 = st.columns(2)
            taal = c3.selectbox("Taal", TALEN, key=f"taal_{i}_{f.name}")
            land = c4.selectbox("Land", LANDEN, key=f"land_{i}_{f.name}")
            ai = st.slider("Percentage AI-gegenereerd", 0, 100, 0, key=f"ai_{i}_{f.name}")
            invoer.append((f, onderwerp, auteur, taal, land, ai))

    if invoer:
        if st.button("➡️ Doorsturen naar beoordeling", type="primary"):
            ontbreekt = [f.name for f, o, *_ in invoer if not o.strip()]
            if ontbreekt:
                st.error("Vul het onderwerp in voor: " + ", ".join(ontbreekt))
            else:
                for f, onderwerp, auteur, taal, land, ai in invoer:
                    data = f.getvalue()
                    datum, meta_auteur = lees_metadata(f.name, data)
                    st.session_state.wachtrij.append({
                        "bestandsnaam": f.name, "onderwerp": onderwerp.strip(), "auteur": auteur,
                        "taal": taal, "land": land, "ai": ai, "datum": datum,
                        "meta_auteur": meta_auteur, "inhoud": data,
                    })
                st.session_state.up_nr += 1  # uploader leegmaken
                st.session_state.pagina = "beoordeel"
                st.rerun()
    else:
        st.info("Upload minstens één bestand om te starten.")


# ===============================================================
# PAGINA 2: Beoordelen & opslaan
# ===============================================================
elif pagina == "beoordeel":
    st.title("🧮 Beoordelen & opslaan")
    wachtrij = st.session_state.wachtrij

    if not wachtrij:
        st.info("Er staan geen documenten klaar. Upload eerst documenten op pagina 1.")
        st.button("📤 Naar uploaden", on_click=ga_naar, args=("upload",))
    else:
        resultaten = [(d, *bereken_score(d)) for d in wachtrij]

        overzicht = pd.DataFrame([
            {
                "Document": d["bestandsnaam"],
                "Onderwerp": d["onderwerp"],
                "Auteur": d["auteur"] or "⚠️ onbekend",
                "Betrouwbare docs auteur": aantal_betrouwbaar(d["auteur"]),
                "Bestandsdatum": d["datum"].strftime("%Y-%m-%d") if d["datum"] else "Onbekend",
                "AI %": d["ai"],
                "Score": score,
                "Rating": rating(score),
            }
            for d, score, _ in resultaten
        ])
        st.dataframe(
            overzicht, hide_index=True, use_container_width=True,
            column_config={"Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d")},
        )

        st.subheader("🔍 Waarom deze score?")
        keuze = st.selectbox("Kies een document", [d["bestandsnaam"] for d, _, _ in resultaten])
        d, score, punten = next(r for r in resultaten if r[0]["bestandsnaam"] == keuze)
        c1, c2 = st.columns([1, 2])
        c1.metric("Betrouwbaarheid", f"{score} / 100")
        c1.write(rating(score))
        c2.bar_chart(pd.Series(punten, name="Punten"))

        b1, b2 = st.columns(2)
        if b1.button("💾 Opslaan in database", type="primary", use_container_width=True):
            con = get_con()
            for d, score, punten in resultaten:
                con.execute(
                    """INSERT INTO documenten
                    (bestandsnaam, onderwerp, taal, auteur, land, ai_percentage,
                     bestandsdatum, toegevoegd_op, score, uitleg, inhoud)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        d["bestandsnaam"], d["onderwerp"], d["taal"], d["auteur"], d["land"], d["ai"],
                        d["datum"].strftime("%Y-%m-%d") if d["datum"] else None,
                        datetime.now().strftime("%Y-%m-%d %H:%M"),
                        score, json.dumps(punten), d["inhoud"],
                    ),
                )
            con.commit()
            con.close()
            st.session_state.wachtrij = []
            st.session_state.pagina = "zoek"
            st.balloons()
            st.rerun()
        if b2.button("🗑️ Wachtrij leegmaken", use_container_width=True):
            st.session_state.wachtrij = []
            st.rerun()


# ===============================================================
# PAGINA 3: Zoeken + document openen
# ===============================================================
else:
    st.title("🔎 Zoeken in de kennisbank")
    df = df_all

    if df.empty:
        st.info("De database is nog leeg. Voeg eerst documenten toe via pagina 1 en 2.")
    else:
        zoek = st.text_input("Zoek op onderwerp, bestandsnaam of auteur")
        c1, c2, c3 = st.columns(3)
        talen = c1.multiselect("Taal", sorted(df["taal"].unique()))
        landen = c2.multiselect("Land", sorted(df["land"].unique()))
        min_score = c3.slider("Minimale score", 1, 100, 1)

        res = df.copy()
        if zoek:
            z = zoek.lower()
            res = res[
                res["onderwerp"].str.lower().str.contains(z, na=False)
                | res["bestandsnaam"].str.lower().str.contains(z, na=False)
                | res["auteur"].str.lower().str.contains(z, na=False)
            ]
        if talen:
            res = res[res["taal"].isin(talen)]
        if landen:
            res = res[res["land"].isin(landen)]
        res = res[res["score"] >= min_score].sort_values("score", ascending=False).reset_index(drop=True)
        res["Rating"] = res["score"].apply(rating)

        st.write(f"**{len(res)}** resultaat/resultaten  ·  👆 klik op een rij om het document te openen")
        event = st.dataframe(
            res[["bestandsnaam", "onderwerp", "auteur", "taal", "land", "ai_percentage", "score", "Rating"]],
            hide_index=True, use_container_width=True,
            on_select="rerun", selection_mode="single-row", key="zoektabel",
            column_config={
                "score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
                "ai_percentage": "AI %",
            },
        )

        geselecteerd = event.selection.rows
        if geselecteerd:
            r = res.iloc[geselecteerd[0]]
            st.divider()
            st.subheader(f"📄 {r['bestandsnaam']}")
            k1, k2 = st.columns([1, 2])
            k1.metric("Betrouwbaarheid", f"{r['score']} / 100")
            k1.write(r["Rating"])
            k1.write(f"**Onderwerp:** {r['onderwerp']}")
            k1.write(f"**Auteur:** {r['auteur'] or '⚠️ onbekend'}")
            k1.write(f"**Bestandsdatum:** {r['bestandsdatum'] or 'onbekend'}")
            k2.caption("Zo is de score opgebouwd")
            k2.bar_chart(pd.Series(json.loads(r["uitleg"]), name="Punten"))

            inhoud = lees_inhoud(r["id"])
            if inhoud:
                toon_document(r["bestandsnaam"], inhoud)
            else:
                st.warning("Dit document is opgeslagen vóór de update en heeft geen bestand in de database.")
        else:
            st.info("Selecteer een rij om de score-uitleg te zien en het document te openen.")

        st.download_button(
            "⬇️ Download database als CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name="kennisbank.csv", mime="text/csv",
        )
