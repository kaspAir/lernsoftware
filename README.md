# Lernsoftware

Webbasierte Lernumgebung für Lernende an Hochschulen, Schulen und Organisationen: Üben und Wiederholen über Lektionen hinweg, formative Rückmeldung mit Quellen, Testprüfungen mit wählbarer Schwierigkeit (Ausbaustufe) und ein Lernbegleiter, der Antworten auf Basis der freigegebenen Unterlagen und des Lernprofils erklärt.

> **Arbeitsname «Lernsoftware»** (D-01, vorläufig). Der endgültige Name ist offen und lässt sich ohne Umbau ändern.

- Repository: https://github.com/kaspAir/lernsoftware
- Geplante Adresse: https://lernen.kaspair.ch/ (Zertifikat in Erstellung)
- Sprache: Deutsch, Schweizer Schreibweise

**Status:** Inkrement 1 (lokaler Lernablauf) umgesetzt und getestet — mit simuliertem Modell. Ein Lauf mit einem echten Modell und der Live-Test gegen den Vorschaltdienst sind offen. Was dokumentiert, implementiert, simuliert oder mit echtem Modell geprüft ist, steht in [07 · Umsetzung und Nachweise](docs/07_Umsetzung_und_Nachweise.md).

---

## Dokumente

| Nr. | Dokument | Inhalt |
|---|---|---|
| 01 | [Anforderungen](docs/01_Anforderungen.md) | Rollen, Prüfstatus, funktionale und nicht-funktionale Anforderungen, Änderungsprotokoll 0.1→0.2 |
| 02 | [Architektur](docs/02_Architektur.md) | Schichten, Kernobjekte, Abläufe, Modellzugang, Konformität zu RA-01…RA-13 |
| 03 | [Spezifikation](docs/03_Spezifikation.md) | Felder, Zustände, Rechte-Matrix, Bewertung, Lernprofil, Wiederholung, API |
| 04 | [Testkonzept](docs/04_Testkonzept.md) | Testpyramide, Testfälle, Rückverfolgbarkeit, Protokoll |
| 05 | [Andragogik und SVEB](docs/05_Andragogik_SVEB.md) | Geprüfte SVEB-Quellen (Tier 1), Leitlinien (Tier 2), Produktentscheidungen (Tier 3) |
| 06 | [Entscheidungen und offene Punkte](docs/06_Entscheidungen_und_offene_Punkte.md) | D-…, ADR-L-…, Befunde an die Normen (B-…) |
| 07 | [Umsetzung und Nachweise](docs/07_Umsetzung_und_Nachweise.md) | Inkremente, Anforderungsstatus, Abweichungen, Testergebnisse |

## Grundlagen

Quellen der Normen: `C:\Projekte\Skills\_docs\1_Architektur\Referenzarchitektur_v0.4.docx` und `C:\Projekte\Skills\_docs\5_Entwicklung\richtlinien\`. Der Vorschaltdienst für Modellaufrufe ist `C:\Projekte\Pseudonymisierung`. Abweichungen werden in 07 begründet, nicht stillschweigend übernommen.

## Lokal starten

Anleitung: [07 · Umsetzung und Nachweise](docs/07_Umsetzung_und_Nachweise.md), Abschnitt 5.

## Ordnerstruktur

```
Lernsoftware/
├── README.md
├── docs/            Anforderungen, Architektur, Spezifikation, Tests, Entscheidungen, Umsetzung
├── app/             Anwendung
├── tests/           Tests und synthetische Testdaten
├── config/          Basiswerte, Vokabular (YAML, versioniert)
├── run.py           Startpunkt
└── requirements.txt
```

## Verantwortung

Fachliche Verantwortung für Inhalte, Lernziele, Aufgaben und Bewertungsfragen liegt bei den Lehrpersonen der jeweiligen Lernorganisation. Das Werkzeug trifft keine Entscheidungen, die einem Menschen zustehen (NR-01).
