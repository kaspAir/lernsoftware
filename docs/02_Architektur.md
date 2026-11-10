# 02 · Architektur

**Version:** 0.2 (2026-11-10) · Vorgänger 0.1
**Abgeleitet aus:** Referenzarchitektur **v0.4** (`RA-01…RA-13`, `NR-01…NR-10`; RA-08 ist laut v0.4 ausstehend verankert) · Entwicklungsrichtlinien Basis und Module · Capability-Katalog v0.1 (`ki_aufruf`, Abschnitt 5.2)
**Bekannte Abweichungen und Befunde:** siehe [07 · Umsetzung und Nachweise](07_Umsetzung_und_Nachweise.md) (A-…) und [06 · Befunde](06_Entscheidungen_und_offene_Punkte.md) (B-…)

---

## 1 · Leitgedanke

Der deterministische Kern entscheidet, was gilt: Prüfstatus, Freigaben, Auswertung, Evidenzlage, Wiederholungstermine, Quellenprüfung, Mandantengrenzen. Das Sprachmodell formuliert, erklärt und schlägt vor. Es erzeugt keine Quellen, keine Zahlen und keine Freigaben. Menschen geben Unterlagen frei und prüfen Aufgaben (Ebene C).

## 2 · Konformität zu den Referenzprinzipien (Entwurf für den Nachweis)

Liste 1 des Konformitätsnachweises. Status: **umgesetzt** (im Code, mit Test), **entworfen** (Dokument, noch nicht im Code), **Abweichung** (siehe 07).

| Kennung | Prinzip | Umsetzung | Fundstelle | Status |
|---|---|---|---|---|
| RA-01 | Kern entscheidet, Modell schlägt vor, Mensch verantwortet | Freigaben sind Menschenhandlungen; Auswertung ist Code; Lernbegleiter ohne Notenfunktion | Spez. §2, §5.3, §7 | umgesetzt (Inkr. 1), Tests TC-FRE, TC-PRF |
| RA-02 | Keine autoritativen Fakten aus dem Modell | Quellen-IDs werden gegen übergebene Abschnitte geprüft; Aussagen tragen «fachlich ungeprüft», wenn nicht geprüft | Spez. §3.5, §10 | umgesetzt (Inkr. 1), TC-BEG |
| RA-03 | Governance-Mixin an jedem Kernobjekt | `created_at, updated_at, version, created_by, status, schema_version` | Spez. §3.1 | umgesetzt (Basisklasse) |
| RA-04 | Entwurf und Bestätigung getrennt | Aufgabe: `entwurf_*` und `fachlich_geprueft_*` | Spez. §3.3 | umgesetzt (Felder), Ebene-C-Prüfung Inkr. 2 |
| RA-05 | Freigabe ist Tor; Änderung macht sie ungültig | Unterlage `in_pruefung` bei Änderung im selben Vorgang | Spez. §4.2 | umgesetzt (Inkr. 1), TC-FRE-01 |
| RA-06 | Änderungen sind Übergänge | `schema_version`, Aufgabenversion, Versuchstreue | Spez. §8 | umgesetzt (Versuchskopie), TC-PRF-04 |
| RA-07 | Konfiguration vor Programmierung | Basiswerte, Vokabular, Prüfungsrahmen als YAML | Spez. §9 | teilweise (Basiswerte und Vokabular in Inkr. 1) |
| RA-08 | Mandantentrennung ist Struktur | `lernorganisation_id` auf jedem Objekt; Repository-Schicht bindet Mandant; RLS Inkr. 2 | ADR-L-006, Abweichung A-2 | Struktur im Code (Inkr. 1), Auslegung für Plattformregister (B-01) |
| RA-09 | Kein direkter Modellkontakt | einzige Adapterstelle; Vorschaltdienst als Basis-URL | §5.4, §6 | umgesetzt (Adapter + Testadapter), Live-Test abhängig von D-05 |
| RA-10 | Jedes Ergebnis trägt seine Herkunft | `herkunft` je Rückmeldung und Versuch | Spez. §3.4 | umgesetzt (Inkr. 1) |
| RA-11 | Unsicherheit ist ein Feld | `evidenzlage`, `sicherheitsgrad`, Datum der letzten Evidenz | Spez. §6.2, §6.4, §10 | umgesetzt (Inkr. 1) |
| RA-12 | Kontrolliertes Vokabular | geschlossene Listen, Ablehnung unbekannter Werte | Spez. §7.3 | umgesetzt (Inkr. 1) |
| RA-13 | Nachweise, nicht nur Ergebnisse | Nachweise: Provenienz, Freigabe, Aufruf, Divergenz, Testprotokoll | §7 | teilweise (Freigabe-, Aufruf-, Versuchsnachweis Inkr. 1) |

**Negativraum** `NR-01…NR-10`: Testfälle in Dok. 04 §7.

**Gleiche Norm, nicht gleiches Verhalten:** Eine Freigabe des Lernbegleiters gilt je Modellversion. Ein Modellwechsel verlangt einen Ground-Truth-Lauf.

## 3 · Schichten

```
┌──────────────────────────────────────────────────────────────┐
│ Oberfläche     Flask-Templates, kleines JS                    │  Bedienung, Hinweise zum Prüfstatus
├──────────────────────────────────────────────────────────────┤
│ Dienste        Anmeldung · Module · Lektionen · Unterlagen ·  │  Ablauf, keine Fachregeln
│                Übungen · Versuche · Lernbegleiter             │
├──────────────────────────────────────────────────────────────┤
│ Kern           Zustände · Freigaben · Prüfstatus · Auswertung │  deterministisch, getestet
│                Evidenz · Wiederholung · Quellenprüfung ·      │
│                Versuchstreue · Nachweise                      │
├──────────────────────────────────────────────────────────────┤
│ Capabilities   ki_aufruf (Adapter: Testadapter, Vorschaltd.)  │  WIE, nicht WAS gut ist
│                textextraktion (Text/Markdown)                 │
├──────────────────────────────────────────────────────────────┤
│ Persistenz     SQLAlchemy-Repositories mit Mandantenbindung   │  SQLite (Entwicklung, A-1)
│                PostgreSQL + RLS (Ziel, ADR-L-006)             │
└──────────────────────────────────────────────────────────────┘
```

**Regel:** Deterministisch prüfbare Kriterien liegen im Kern. Fachlich zu beurteilende Inhalte liegen in der Konfiguration oder Methode und werden durch Prüfung abgesichert, nicht durch Code erzwungen.

## 4 · Kernobjekte und Zustände

| Objekt | Führt | Art |
|---|---|---|
| `Lernorganisation` | Mandant (Registrierungsfelder) | Plattformregister (B-01) |
| `Konto` | Login, Rollen je Lernorganisation | Objekt |
| `Modul`, `Modulzuweisung` | Fach, Zuweisungen, Delegation | Objekt |
| `Lektion`, `Lernziel` | Struktur, Lernhandlungsstufe | Objekt (archivierbar) |
| `Unterlage` (+ Version) | Datei, Freigabe | Objekt mit Freigabezyklus |
| `Abschnitt` | zitierfähige Textstelle | Objekt mit stabiler ID |
| `Aufgabe` (+ Version) | Frage, Schlüssel/Raster, Quellen, Prüfstatus | Objekt mit Prüfzyklus |
| `Übung`, `Testprüfung` | eingefrorene Aufgabenliste | Objekt |
| `Versuch` | eine Bearbeitung mit Hilfen und Auswertung | Objekt, unveränderlich nach Abgabe |
| `Evidenz` (je Person und Lernziel) | Zählungen der Versuche | berechnet aus Versuchen (Kern) |
| `Wiederholungszustand` (je Person und Aufgabe) | SM-2-Zustand | berechnet (Kern) |
| `Meldung` | Studierendenmeldung zu einer Aufgabe | Objekt mit Entscheid |
| `Gespräch` / `Nachricht` | Lernbegleiter | Objekt |
| `Nachweis` | Protokolleintrag | Objekt, unveränderlich |

### 4.1 Zustände der Unterlage
Siehe Spez. §4. Kurz: `hochgeladen → extrahiert → entwurf → freigegeben | freigegeben_unter_auflage | nicht_freigebbar`; Änderung eines freigegebenen Inhalts → `in_pruefung`.

### 4.2 Prüfstatus der Aufgabe
Siehe Spez. §5.3: `technisch_geprueft` (Ebene B) → `fachlich_geprueft` (Ebene C); `gesperrt` (nach Meldung); `verworfen`.

## 5 · Wichtige Abläufe

### 5.1 Upload bis Freigabe (Inkr. 1)
1. Assistenz oder Dozierende lädt eine Textdatei hoch und ordnet sie einer Lektion zu (IN-02).
2. Abschnittsbildung (synchron).
3. Dozierende gibt die Unterlage fachlich frei (Ebene A, IN-06).
4. Ab da sind die Abschnitte Grundlage für Aufgaben und Rückmeldungen.

### 5.2 Übung erzeugen (Inkr. 1)
Die Erzeugung ist in Inkrement 1 **deterministisch**: Aus den freigegebenen Abschnitten werden Aufgaben aus **hinterlegten Aufgabenvorlagen der Lehrperson** erzeugt (Lernaufgabe mit Lösungsschlüssel, manuell vorbereitet, Assistenz oder Dozierende). Das Modell ist im Inkrement 1 **nicht** für Aufgabenerzeugung eingebunden. Die Erzeugung mit Modell (Ebene B) ist Inkrement 2 und läuft über den Adapter mit Kernprüfung (Spez. §5.1).

Begründung: Der Ablauf «Lektion wählen → Übung → Antwort → Rückmeldung → Rückfrage» ist so vollständig prüfbar, ohne dass ein Modell verfügbar sein muss. Die Lehrperson liefert die Aufgaben; das Produkt liefert den Ablauf.

### 5.3 Auswertung und Lernprofil
- Auswertung: reiner Code gegen Lösungsschlüssel (Spez. §7.1).
- Versuch wird mit Aufgabenkopie, Hilfen, Selbsteinschätzung und Auswertung gespeichert (Spez. §8).
- Evidenz je Lernziel: Zählung verschiedener selbstständig richtiger Aufgaben (Spez. §6.1–6.2).
- Wiederholungsplanung: SM-2 (Spez. §6.3), getrennt.

### 5.4 Lernbegleiter (Inkr. 1)
1. Kern sammelt: Versuch (mit Aufgabenversion), Lösung, Abschnitte mit IDs, Lernprofil **pseudonymisiert**, gewählte Form (Hinweis, Rückfrage, Beispiel, Erklärung).
2. Die Erklärung entsteht über `ki_aufruf` **oder** — im Inkrement 1 als Standard — aus einem **deterministischen Textbaustein** mit Verweis auf den Abschnitt der Aufgabe (Erklärung aus Lösungsbegründung). Die Modellvariante ist hinter dem Adapter aktivierbar.
3. Kern prüft Schema, Quellen-IDs, verbotene Muster (Spez. §10). Verstoss → Standardtext (BS-05).
4. Anzeige: Text, Quelle, «fachlich ungeprüft», Sicherheitsgrad.

### 5.5 Mandantenkontext
Jede Anfrage trägt eine Sitzung mit genau einer Lernorganisation (BE-05). Die Repository-Schicht verlangt den Mandanten für jede Abfrage (ADR-L-006). Im Ziel-Zustand setzt PostgreSQL RLS den Kontext je Verbindung.

## 6 · Modellzugang und Vorschaltdienst

| Element | Stand (Prüfung 2026-11-10) |
|---|---|
| Capability `ki_aufruf` | Vertrag v0.1 im Katalog (Abschnitt 5.2): Eingabe `auftrag, modellklasse, mandant`; Ausgabe `antwort, aufrufnachweis`; Invariante: jeder Aufruf durch die Pseudonymisierung. |
| Vorschaltdienst `Pseudonymisierung` | Projekt `C:\Projekte\Pseudonymisierung`. README: «Dienst gebaut und getestet, Erstinstallation auf dem Host läuft». API-Referenz geprüft (`docs/API.md`, Stand 2026-07-21). Ports 8040 (develop) … 8043. Kopfzeilen `X-Pseudo-Anwendung`, `X-Pseudo-Mandant`, `X-Pseudo-Projekt`. Fehler 409 (Entscheidung nötig), 502 (Rückersetzung unvollständig), 503 (kein Schlüssel). |
| **Laufzeitstatus** | **nicht bestätigt.** `GET http://127.0.0.1:8040/pseudo/v1/health` lieferte beim Prüfen keine Antwort. Der Dienst ist im Projekt als verfügbar **nicht** geführt, bis der Health-Check antwortet. |
| Adapter im Projekt | `app/modell/adapter.py`: spricht `/anthropic/v1/messages` bzw. den Pfad der gewählten Klasse über die Basis-URL. Das Verhalten bei 409 und 502 folgt der Vorgabe in `ANBINDUNG.md` §6.2 (Ausnahmeklasse, kein generisches Schlucken). |
| Testadapter | `app/modell/testadapter.py`: deterministisch, `herkunft: SIMULIERT`. |

## 7 · Nachweise (RA-13)

| Nachweis | Inhalt | Erzeuger | Inkr. |
|---|---|---|---|
| Freigabenachweis | Wer, wann, welche Form, welche Version | Kern | 1 |
| Versuchsnachweis | Aufgabenkopie, Hilfen, Antwort, Auswertung, Version | Kern | 1 |
| Meldungsnachweis | Meldung, Entscheid, Begründung | Kern | 2 |
| Aufrufnachweis | Anbieter, Modell, Version, Klasse, Zeitpunkt, `herkunft` (echt/SIMULIERT) | Adapter | 1 (Testadapter), 2 (echt) |
| Divergenznachweis | Entwurf vs. Endfassung | Kern | 2 |
| Testprotokoll | siehe Dok. 04 §8 | Test-Runner | 1 |
| Konformitätsnachweis | Liste 1–3 | Projekt | fortlaufend |

Ein ausgestellter Nachweis ist unveränderlich (NR-10).

## 8 · Betrieb und Umgebungen

| Umgebung | Auslegung |
|---|---|
| `develop` | lokal; SQLite oder PostgreSQL-Container; Testadapter oder Vorschaltdienst; synthetische Daten |
| `test` | Kundenumgebung; nur auf ausdrückliche Anweisung |
| `integration` | Abbild der Produktion; echter Vorschaltdienst |
| `main` | Produktivbetrieb; erst nach D-07 und D-09 |

Portblock: offen (D-11). Schlüssel nur in `.env`, nie im Repository. Start-Warnungen: fehlender Vorschaltdienst, Testadapter aktiv, fehlende Konfiguration.

## 9 · Capability-Katalog

| Capability | Stand | Anmerkung |
|---|---|---|
| `ki_aufruf` | Vertrag v0.1 vorhanden | Umsetzung über Vorschaltdienst; Laufzeit offen (D-05) |
| `textextraktion` | Katalogantrag offen | Inkr. 1: nur Text; PDF/DOCX/PPTX Inkr. 2 |
| `lernfortschritt` | **Katalogantrag** (B-04) | deterministische Funktion aus Evidenz und SM-2, konfigurierbar |
| `pruefungsrahmen` | **Katalogantrag** (Inkr. 3) | Rahmen mit Regeln; Inhalt liegt beim Auftraggeber (D-22) |

## 10 · Schnittstellen

- Web-Oberfläche (serverseitig) für alle Rollen.
- JSON-API unter `/api/v1/` (Spez. §13). Die Beschreibung wird aus dem Code erzeugt; keine zwei handgepflegten Fassungen.
- Keine Schnittstelle zu Lernmanagementsystemen in Phase 1.

## 11 · Offene Architekturpunkte

- RLS-Umsetzung und Tests gegen PostgreSQL (A-2 in 07).
- Befund B-01 (Plattformregister und RA-08) zur Klärung an die Architektur.
- Vorschaltdienst-Laufzeit (D-05).
- Bedienungsnorm (D-10).
