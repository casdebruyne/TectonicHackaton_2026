import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Betrouwbaarheid", page_icon="🛡️", layout="wide")
st.title("🛡️ Betrouwbaarheidsscore van kennis")
st.caption("Elke score is uitlegbaar: je ziet per document waarom het dit cijfer krijgt.")

# ---------- Voorbeelddata ----------
docs = pd.DataFrame([
    ["Verlofbeleid 2026",      "Verlofdagen", "25 dagen", "Beleid",     "Goedgekeurd", "HR Team",  date(2026, 1, 10)],
    ["HR Handleiding",         "Verlofdagen", "25 dagen", "Handleiding","Goedgekeurd", "An Peeters", date(2025, 6, 2)],
    ["Oude intranetpagina",    "Verlofdagen", "20 dagen", "Handleiding","Onbekend",    None,        date(2022, 3, 15)],
    ["Teams-gesprek Marc",     "Verlofdagen", "24 dagen", "Teams-chat", "Onbekend",    "Marc D.",   date(2026, 8, 20)],
    ["Payroll procedure",      "Loonbrief",   "Vóór de 25e", "Beleid",  "Goedgekeurd", "Payroll",   date(2026, 3, 1)],
    ["E-mail klant",           "Loonbrief",   "Vóór de 28e", "E-mail",  "Concept",     "Sara V.",   date(2025, 11, 5)],
], columns=["Document", "Onderwerp", "Antwoord", "Brontype", "Status", "Eigenaar", "Datum"])

# ---------- Gewichten (aanpasbaar = transparant) ----------
with st.sidebar:
    st.header("⚖️ Gewichten")
    w = {
        "Actualiteit": st.slider("Actualiteit", 0, 10, 3),
        "Eigenaar":    st.slider("Eigenaar bekend", 0, 10, 2),
        "Status":      st.slider("Goedkeuring", 0, 10, 3),
        "Brontype":    st.slider("Brontype", 0, 10, 2),
        "Consensus":   st.slider("Consensus met andere bronnen", 0, 10, 4),
    }
    totaal = sum(w.values()) or 1

STATUS = {"Goedgekeurd": 1.0, "Concept": 0.4, "Onbekend": 0.0}
BRON = {"Beleid": 1.0, "Handleiding": 0.8, "E-mail": 0.4, "Teams-chat": 0.3}

# ---------- Score berekenen ----------
def factoren(rij):
    leeftijd = (date.today() - rij["Datum"]).days
    anderen = docs[(docs["Onderwerp"] == rij["Onderwerp"]) & (docs["Document"] != rij["Document"])]
    consensus = (anderen["Antwoord"] == rij["Antwoord"]).mean() if len(anderen) else 0.5
    return {
        "Actualiteit": max(0, 1 - leeftijd / 730),
        "Eigenaar": 1.0 if rij["Eigenaar"] else 0.0,
        "Status": STATUS[rij["Status"]],
        "Brontype": BRON[rij["Brontype"]],
        "Consensus": consensus,
    }

def bereken(rij):
    f = factoren(rij)
    bijdrage = {k: f[k] * w[k] / totaal * 100 for k in f}
    return sum(bijdrage.values()), bijdrage

docs["Score"] = docs.apply(lambda r: round(bereken(r)[0]), axis=1)
docs["Rating"] = docs["Score"].apply(
    lambda s: "🟢 Betrouwbaar" if s >= 75 else ("🟠 Let op" if s >= 50 else "🔴 Niet vertrouwen")
)

# ---------- Overzicht ----------
st.subheader("📋 Overzicht")
st.dataframe(
    docs.sort_values("Score", ascending=False)[["Document", "Onderwerp", "Antwoord", "Score", "Rating"]],
    use_container_width=True, hide_index=True,
    column_config={"Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d")},
)

# ---------- Detail ----------
st.subheader("🔍 Waarom deze score?")
keuze = st.selectbox("Kies een document", docs["Document"])
rij = docs[docs["Document"] == keuze].iloc[0]
score, bijdrage = bereken(rij)

c1, c2 = st.columns([1, 2])
with c1:
    st.metric("Betrouwbaarheid", f"{round(score)} / 100")
    st.write(rij["Rating"])
    st.write(f"**Eigenaar:** {rij['Eigenaar'] or '⚠️ onbekend'}")
    st.write(f"**Datum:** {rij['Datum']}")
    st.write(f"**Status:** {rij['Status']}")
with c2:
    st.bar_chart(pd.Series(bijdrage, name="Punten"))

# ---------- Conflictdetectie ----------
zelfde = docs[docs["Onderwerp"] == rij["Onderwerp"]]
if zelfde["Antwoord"].nunique() > 1:
    st.warning(f"⚠️ Bronnen spreken elkaar tegen over **{rij['Onderwerp']}**:")
    st.dataframe(zelfde[["Document", "Antwoord", "Datum", "Score"]].sort_values("Score", ascending=False),
                 hide_index=True, use_container_width=True)
    beste = zelfde.sort_values("Score", ascending=False).iloc[0]
    st.success(f"✅ Aanbevolen bron: **{beste['Document']}** ({beste['Antwoord']}, score {beste['Score']})")
else:
    st.success("Alle bronnen zijn het eens over dit onderwerp.")

if score < 50:
    st.error(f"Lage betrouwbaarheid. Vraag het aan: **{rij['Eigenaar'] or 'de afdeling HR'}**")
