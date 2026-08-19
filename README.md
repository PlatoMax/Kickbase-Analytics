Hier ist die sauber formatierte und korrigierte Copy-Paste-Version für deine `README.md`. Die zerschossenen Formatierungen (Listen, Code-Blöcke, Überschriften) wurden repariert, sodass sie auf GitHub oder in deinem Editor optimal gerendert wird:


# Kickbase-Analytics

Kickbase-Analytics unterstützt datenbasierte Kauf- und Verkaufsentscheidungen im Kickbase-Management.  
Das Projekt kombiniert Bundesliga-Daten, Feature Engineering und ML-Prognosen (XGBoost), um erwartete Spielerpunkte vorherzusagen und daraus konkrete Handlungsempfehlungen abzuleiten.

---

## Funktionen
- Vorhersage erwarteter Punkte für Spieler
- Optimierung des Kaders (Buy / Sell / Hold)
- Transfermarkt-Ansicht mit Bid-Unterstützung
- Dashboard mit:
  - KPI-Übersicht (Spieltag, Deadline, Budget, Expected Points)
  - Leaderboard
  - Matchups

---

## Projektstruktur (relevant)
- api/main.py → FastAPI-Backend (API-Endpunkte)
- dashboard/Overview.py → Streamlit-Startseite
- dashboard/pages/2_team.py → Seite „My Team“
- dashboard/pages/3_market.py → Seite „Transfer Market“
- update_database.py → Skript zum Aktualisieren der Datenbank

---

## Voraussetzungen
- Python 3.10+ (empfohlen)
- pip

**Abhängigkeiten installieren:**

pip install -r requirements.txt


---

## Einrichtung

1. **Umgebungsvariablen:** `.env` anlegen (z. B. aus `.env.example`) und Zugangsdaten setzen:

```env
EMAIL=deine_email_hier
PASSWORD=dein_passwort_hier

```

2. **Liga-Konfiguration:** In `scrape/config.py` den Liga-Namen auf deine Kickbase-Liga setzen:

```python
LEAGUE_NAME = "Dein Liga-Name"

```

---

## Starten (vom Projekt-Root)

**1) Backend starten (FastAPI/Uvicorn)**

```bash
uvicorn api.main:app --reload

```

*Das Backend läuft anschließend unter:* `http://127.0.0.1:8000`

**2) Frontend starten (Streamlit)**

In einem zweiten Terminal ausführen:

```bash
streamlit run dashboard/Overview.py

```

---

## Dashboard-Seiten

### Overview (`dashboard/Overview.py`)

* Matchday/Deadline
* Budget
* Expected Points
* Leaderboard
* Nächste Matchups

<img width="1920" height="989" alt="Bildschirmfoto 2026-08-19 um 17 06 04" src="https://github.com/user-attachments/assets/43f950b5-1acc-4983-8186-2c7fe8bee67b" />


### My Team (`dashboard/pages/2_team.py`)

* Aktueller Kader vs. optimierter Kader
* Erwartete Punkte vorher/nachher
* Verkauf von Spielern per Button

<img width="1920" height="987" alt="Bildschirmfoto 2026-08-19 um 17 34 28" src="https://github.com/user-attachments/assets/390cdc59-10b5-4df8-a664-96d96229da2b" />


### Transfer Market (`dashboard/pages/3_market.py`)

* Transfermarkt mit Prognosewerten
* Auto-Bid per Overpay-Slider
* Manuelle Gebote

<img width="1920" height="983" alt="Bildschirmfoto 2026-08-19 um 18 51 31" src="https://github.com/user-attachments/assets/2d671c71-678f-4e5f-af1f-8e251a94e0e2" />

---

## Hinweis zum Projektstatus

Das Projekt ist funktional aber enthält bereits markierte Erweiterungs-/TODO-Ideen (z. B. bessere Fehlerbehandlung, Statistik-Erweiterungen, UX-Verbesserungen, API-Optimierung).
