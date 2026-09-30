# SD WORX APPLICATION

**Weet wat je kunt vertrouwen, voordat je het gebruikt.**
Een Streamlit-app die documenten beoordeelt op betrouwbaarheid, met een transparante score van 1 tot 100, en ze opslaat in een doorzoekbare kennisbank.

## Launch the app here!

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://tectonichackaton2026-wtiard6rvzwqny5qdv29qj.streamlit.app/)

## ✨ Waarom deze app?

Organisaties verzamelen kennis in PDF's, Word-bestanden, spreadsheets en afbeeldingen, maar niemand weet hoe betrouwbaar die bronnen zijn. Is het document nog actueel? Wie schreef het? Is het door AI gegenereerd?

Deze app beantwoordt die vragen in drie stappen en geeft elk document een **uitlegbare score**: je ziet precies waarom een document 82 of 34 punten krijgt.

## 🚀 Functies

| Pagina | Wat kan je doen? |
|---|---|
| **1️⃣ Uploaden** | Meerdere bestanden tegelijk uploaden (PDF, Word, Excel, afbeeldingen) en per document onderwerp, auteur, taal, land en AI-percentage invullen |
| **2️⃣ Beoordelen & opslaan** | Automatisch een score berekenen, per factor bekijken waarom, en alles opslaan in de database |
| **3️⃣ Zoeken** | Zoeken op onderwerp, bestandsnaam of auteur, filteren op taal, land en minimale score, en exporteren naar CSV |

## 🧮 Hoe werkt de score?

De score bestaat uit vijf factoren met vaste gewichten (samen 100 punten). Zo blijft elke score volledig uitlegbaar.

| Factor | Max. punten | Logica |
|---|---:|---|
| **Actualiteit** | 30 | Op basis van de wijzigingsdatum uit de metadata. Loopt lineair af naar 0 na 3 jaar. Onbekende datum = lage score |
| **Auteur** | 20 | Volledig punt als de ingevulde naam overeenkomt met de metadata van het bestand, gedeeltelijk als de naam niet te controleren is, niets als de auteur ontbreekt |
| **AI-percentage** | 25 | Hoe meer AI-gegenereerd, hoe lager de score |
| **Metadata aanwezig** | 15 | Bestand bevat leesbare metadata (datum) |
| **Bestandstype** | 10 | PDF > Word > Excel > afbeeldingen |

**Rating**

- 🟢 **Betrouwbaar**: score ≥ 75
- 🟠 **Let op**: score 50 tot 74
- 🔴 **Niet vertrouwen**: score < 50


## 🧱 Tech stack

- [Streamlit](https://streamlit.io/): interface
- [pandas](https://pandas.pydata.org/): dataverwerking
- [SQLite](https://www.sqlite.org/): opslag
- pypdf, python-docx, openpyxl, Pillow: metadata uitlezen

## ⚠️ Beperkingen

- Het **AI-percentage** wordt momenteel handmatig ingevuld; er is nog geen automatische AI-detectie.
- **Metadata kan aangepast of vervalst zijn**. De score is een onderbouwde indicatie, geen garantie.
- De **gewichten** zijn een bewuste keuze en kunnen worden bijgesteld in de `GEWICHTEN`-dictionary.

## 🗺️ Mogelijke uitbreidingen

- Automatische AI-detectie in plaats van een handmatige slider
- Inhoudelijke analyse van de tekst (bronvermelding, consistentie)
- Gebruikersaccounts en een gedeelde database
- Aanpasbare gewichten via de interface

## 👥 Team

Mauro Collier
William Hovine
Gill Derous
Cas De Bruyne
