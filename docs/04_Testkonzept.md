# 04 · Testkonzept

**Status:** Entwurf zur Prüfung · Stand: 2026-11-10
**Bezug:** Testkonzept Zielarchitektur V0.1 der Suite (Umgebungen, Testarten, Protokoll) · Modul `tests-und-nachweis` der Entwicklungsrichtlinien · [01 · Anforderungen](01_Anforderungen.md) · [03 · Spezifikation](03_Spezifikation.md)

Leitmotiv: Getestet wird nicht, um etwas ausprobiert zu haben, sondern um einen **nachvollziehbaren Nachweis** zu erzeugen. «Ist das getestet?» wird mit dem Protokoll beantwortet, nicht mit «ja».

---

## 1 · Grundsätze

1. **Pass/Fail entscheidet der Test-Runner**, nie ein Modell oder ein Mensch im Nachhinein (Testkonzept, Prinzip «Deterministische Ausführung»).
2. **Prüfer ≠ Erzeuger.** Die Testfälle werden aus der Spezifikation geschrieben, nicht aus dem Code abgeleitet. Wer den Code schreibt, nimmt ihn nicht allein ab.
3. **Keine Tests heisst nicht geprüft**, nicht «bestanden».
4. **Ein Regressionstest sagt, was er beweist.** Die erste Zeile jedes Testmoduls und jedes Testfalls ist `"""Beweist: …"""`. Ein Test ohne diesen Satz wird im Review zurückgegeben.
5. **Mandantentrennung wird ausdrücklich getestet**, nicht nur der erlaubte Fall (NR-04).
6. **Modellverhalten wird gegen einen Ground-Truth-Satz** geprüft, je Modell und Modellversion. Eine Freigabe gilt nur für die geprüfte Fassung (Architektur §2, letzter Abschnitt).
7. **Zahlen zählt der Code.** Auswertungen in Tests werden berechnet und mit Erwartungswerten verglichen, nicht aus Modellausgaben übernommen.

## 2 · Testpyramide im Projekt

| Testart (Suite) | Anwendung hier | Umgebung | Werkzeug |
|---|---|---|---|
| Unit / Komponente | Kernfunktionen: SM-2, Auswertung, Freigabezustände, Kontrastprüfung, Quellenprüfung | `develop`, `test`, `integration` | pytest |
| Kontrakttest (gegen Mock) | `ki_aufruf` gegen Mock-Adapter; Erklärungsschema; Extraktionsvertrag | `develop`, `test` | pytest + Schema-Prüfung |
| Mandanten- und Berechtigungstests | Struktur (RLS), Rollen, Zugriff über alle Endpunkte | `develop`, `test`, `integration` | pytest + Datenbank-Fixture mit zwei Mandanten |
| Fachliche Testfälle (End-to-End) | Upload → Freigabe → Prüfung → Auswertung; Lernen über Lektionen; Lernbegleiter | `develop`, `test` mit Mock; `integration` mit echtem Modell | Playwright (Browser) oder HTTP-Client |
| Modell-Ground-Truth | Fragenerzeugung, Erklärungen, Quellentreue | `integration` (echtes Modell über Vorschaltdienst) | eigenes Testset, siehe §6 |
| Sicherheit statisch | SAST, Abhängigkeits-Scan | `develop` (CI) | bandit, pip-audit |
| Sicherheit dynamisch | Eingabe- und Zugriffstests gegen laufende Instanz | `integration` | Phase 2 |
| Barrierefreiheit | Kontrast (automatisch), Tastatur, Screenreader-Stichproben | `test`, Stichprobe `integration` | axe-core, manuell |
| Abnahme | Andragogik-Prüfliste, fachliche Abnahme | `test` (Kunde), `integration` | manuell, dokumentiert |
| Smoke / Health | Erreichbarkeit, Login, Datenbankverbindung | `integration`, `main` | nicht destruktiv |

**Umgebungsregel:** Lasttests und dynamische Sicherheitstests laufen nur auf `integration` und nie während einer Abnahme. Im Produktivbetrieb (`main`) gibt es nur Smoke- und Health-Checks.

## 3 · Testfallkennungen

`TC-<Bereich>-<Nummer>` · Bereiche: `MAND` Mandant · `LOG` Login · `MOD` Module/Zuweisung · `UPL` Upload/Extraktion · `FRE` Freigabe · `LRN` Lernen/Repetition · `PRF` Prüfung · `BEG` Lernbegleiter · `ERS` Erscheinungsbild · `KI` Modellzugang · `NW` Nachweis · `AG` Andragogik · `A11Y` Barrierefreiheit · `NFT` nicht funktional · `SEC` Sicherheit.

Testfälle sind nie umzubenennen; zurückgezogene bleiben mit Vermerk stehen (wie bei den Kennungen der Norm).

## 4 · Testfälle (Auswahl, verbindlich)

### 4.1 Mandantentrennung (MAND) — NR-04, RA-08

| ID | Beweist | Prüfung | Anf. |
|---|---|---|---|
| TC-MAND-01 | Studierende von Organisation A kann keine Unterlage von B lesen, auch nicht über direkte ID-Eingabe. | Anfrage mit fremder UUID → 404 (nicht 403, um Existenz nicht zu verraten), keine Daten im Körper. | PL-05 |
| TC-MAND-02 | Eine Abfrage ohne Mandantenfilter liefert keine Zeilen fremder Mandanten. | Direkte SQL-Abfrage unter Rolle der Anwendung mit gesetztem Kontext A; erwartet nur A-Zeilen. | PL-05, NF-06 |
| TC-MAND-03 | Ein Mandanten-Erscheinungsbild-Delta ist für andere Mandanten nicht sichtbar, auch nicht als Vorlage. | Anfrage durch Admin B auf Delta von A → nichts. | PL-03, NR-04 |
| TC-MAND-04 | Der Super-Admin sieht Organisationsmetadaten, aber keine Inhalte. | Anfragen auf Lektionen, Antworten, Gespräche → verweigert. | PL-02 |
| TC-MAND-05 | Abschnitte für Erklärungen stammen nur aus der Lernorganisation der Sitzung. | Lernbegleiter-Aufruf mit fremder Abschnitts-ID → Ablehnung, Nachweis mit `NR-04`. | BS-02, NR-04 |
| TC-MAND-06 | Ein Konto mit Rollen in A und B sieht in einer Sitzung nur einen Mandanten. | Wechsel erfordert neue Sitzung. | BE-05 |

### 4.2 Login (LOG)

| ID | Beweist | Prüfung | Anf. |
|---|---|---|---|
| TC-LOG-01 | Passwörter werden nicht im Klartext gespeichert. | Datenbankeintrag enthält Argon2id/bcrypt-Präfix; Testpasswort nicht enthalten. | BE-02 |
| TC-LOG-02 | Nach fünf Fehlversuchen ist das Konto gesperrt. | Fünf falsche Eingaben, sechste mit richtigem Passwort → gesperrt; Ereignis im Nachweis. (Grenzwert D-14) | BE-03 |
| TC-LOG-03 | Keine Selbstregistrierung. | Keine Route zum Anlegen durch Unberechtigte. | BE-01 |
| TC-LOG-04 | Sitzungscookie ist HttpOnly, Secure, SameSite=Lax. | Antwortheader-Prüfung. | NF-01 |
| TC-LOG-05 | Schreibende Anfrage ohne CSRF-Token wird abgewiesen. | — | NF-01 |

### 4.3 Module und Zuweisungen (MOD)

| ID | Beweist | Prüfung | Anf. |
|---|---|---|---|
| TC-MOD-01 | Studierende sehen nur zugewiesene Module. | Liste und Detail. | MO-03 |
| TC-MOD-02 | Entfernte Zuweisung sperrt sofort den Zugriff. | Zuweisung löschen, dann Zugriff → verweigert. | MO-02 |
| TC-MOD-03 | Assistenz kann keine Freigabe erteilen. | Freigabe-Endpunkt mit Assistenz-Sitzung → 403. | IN-06, Matrix §2 |
| TC-MOD-04 | Lektionsstruktur entsteht nicht automatisch. | Hochladen einer Unterlage erzeugt keine Lektion. | MO-05, NR-01 |

### 4.4 Unterlagen und Freigabe (UPL, FRE)

| ID | Beweist | Prüfung | Anf. |
|---|---|---|---|
| TC-UPL-01 | Sammelupload ohne Lektionszuordnung und spätere Zuordnung funktionieren. | Ablauf. | IN-02, IN-03 |
| TC-UPL-02 | Unzulässiger Dateityp (per Inhalt) wird abgewiesen, auch mit anderer Endung. | Ausführbare Datei mit `.pdf`-Endung. | IN-01 |
| TC-UPL-03 | Fehlgeschlagene Extraktion ist sichtbar mit Grund. | Verschlüsseltes PDF. | IN-04 |
| TC-UPL-04 | Fremder Pfad im Dateinamen führt nicht zu Dateiablage ausserhalb des Werkverzeichnisses. | Dateiname `../../x`. | NF-01, Architektur §6 |
| TC-FRE-01 | Eine Inhaltsänderung setzt eine freigegebene Unterlage auf `in_pruefung` (NR-05). | Freigeben, Version ändern, Status prüfen; Zustand im selben Vorgang. | IN-07 |
| TC-FRE-02 | Bei `in_pruefung` werden Abschnitte nicht für neue Lernfragen verwendet. | Erzeugungsversuch → keine Verwendung. | IN-07 |
| TC-FRE-03 | Lernfragen mit Quelle in Prüfung sind für Studierende ausgeblendet, nicht gelöscht. | Sichtbarkeit und Bestand. | IN-07, LE-06 |
| TC-FRE-04 | Freigabe unter Auflage braucht Verantwortliche und Frist in der Zukunft. | Eingabe ohne Frist → abgewiesen. | IN-08 |
| TC-FRE-05 | Überfällige Auflage wird als überfällig markiert. | Zeitreise im Test. | RA-11 |
| TC-FRE-06 | Nicht freigebbar verlangt Begründung. | — | IN-08 |

### 4.5 Lernen und Repetition (LRN)

| ID | Beweist | Prüfung | Anf. |
|---|---|---|---|
| TC-LRN-01 | Der SM-2-Algorithmus ist deterministisch und entspricht den Referenzwerten. | Tabelle aus Spezifikation §6: Eingabe `q` und Startzustand → erwartetes Intervall und `ease`. | LE-03 |
| TC-LRN-02 | `q` < 3 setzt Wiederholungen zurück und Intervall auf 1 Tag. | — | LE-03 |
| TC-LRN-03 | `ease` fällt nie unter 1,3. | Wiederholte falsche Antworten. | LE-03 |
| TC-LRN-04 | Sicherheitsgrad und Datum werden zusammen angezeigt. | Oberflächen-Snapshot. | LE-04 |
| TC-LRN-05 | Lernen über mehrere Lektionen liefert nur freigegebene Fragen dieser Lektionen. | — | LE-02, LE-06 |
| TC-LRN-06 | Meldung einer Frage erzeugt Eintrag für Dozierende. | — | LE-08 |

### 4.6 Testprüfung (PRF)

| ID | Beweist | Prüfung | Anf. |
|---|---|---|---|
| TC-PRF-01 | Die Auswertung wird vom Code berechnet; Punkte und Quote stimmen mit Erwartung überein. | Festes Antwortset, erwartete Punkte. | PR-04 |
| TC-PRF-02 | Teilpunkte bei `multiple_choice` sind korrekt und nie negativ. | Grenzfälle. | PR-04 |
| TC-PRF-03 | Schwierigkeit «sehr schwer» liefert nur Fragen der Stufe 4; kein Auffüllen aus anderen Stufen. | Zu wenige Fragen → kleinere Prüfung mit Hinweis. | PR-02, PR-08 |
| TC-PRF-04 | Jede Antwort speichert Frage-Version und Prüfungs-Version. | Änderung an Frage nach Start verändert Auswertung nicht. | PR-05, RA-06 |
| TC-PRF-05 | Prüfung ist als formativ gekennzeichnet; keine Note. | Feld `formativ` = true, keine Notenausgabe. | PR-06, NR-01 |
| TC-PRF-06 | Keine Prüfung mit null freigegebenen Fragen; Hinweis statt Erzeugung. | — | PR-08 |
| TC-PRF-07 | Erzeugte Fragen werden vor Verwendung geprüft (Quellen, Lösung, Dubletten); verworfene werden gezählt. | Mock-Modell liefert fehlerhafte Fragen → verworfen. | LE-06, Architektur §5.2 |

### 4.7 Lernbegleiter (BEG)

| ID | Beweist | Prüfung | Anf. |
|---|---|---|---|
| TC-BEG-01 | Zitierte Quellen sind Teil der übergebenen Abschnitte; sonst wird die Antwort verworfen. | Mock-Modell zitiert fremde ID → Ablehnung, Nachweis `NR-02`. | BS-02, NR-02 |
| TC-BEG-02 | Schema-Verstoss führt zu Wiederholung mit fester Grenze, danach Fehlermeldung. | — | Spez. §10 |
| TC-BEG-03 | Bewertungssprache wird abgewiesen. | Mock liefert «Note 4». | BS-06, NR-01 |
| TC-BEG-04 | Der Lernstand wird nur pseudonymisiert übergeben. | Eingabe-Prüfung: keine Klarnamen, keine E-Mail-Adresse (Testdaten mit Markern). | NF-02, NF-07 |
| TC-BEG-05 | Frage ausserhalb der Unterlagen → Standardantwort und Weiterleitungsangebot. | — | BS-05 |
| TC-BEG-06 | Sicherheitsgrad ≠ «sicher» zeigt Annahmen. | — | RA-11, BS-04 |
| TC-BEG-07 | Modell nicht erreichbar → klare Meldung, keine stille Ersatzantwort. | Mock-Ausfall. | Spez. §12 |
| TC-BEG-08 | Gesprächsverlauf ist für Dozierende ohne Zustimmung nicht lesbar. | — | BS-07 |

### 4.8 Modellzugang (KI) — NR-03, RA-09

| ID | Beweist | Prüfung | Anf. |
|---|---|---|---|
| TC-KI-01 | Ohne Basis-URL des Vorschaltdienstes gibt es keinen Modellzugang. | Start ohne Konfiguration → kein Anbieterkontakt, Meldung im Start-Protokoll. | NF-07 |
| TC-KI-02 | Im Code existiert genau eine Stelle mit Anbieterkontakt. | Statische Suche nach Anbieter-SDK-Imports; Ergebnis genau eine Datei. | NF-07, RA-09 |
| TC-KI-03 | Jeder Modellaufruf erzeugt einen Aufrufnachweis mit Anbieter, Modell und Version. | — | NF-04 |
| TC-KI-04 | Direktschalter ist im Start-Protokoll als Warnung sichtbar. | — | Betrieb |
| TC-KI-05 | Einbettungen laufen ebenfalls über `ki_aufruf`. | — | Architektur §6 |

### 4.9 Erscheinungsbild (ERS)

| ID | Beweist | Prüfung | Anf. |
|---|---|---|---|
| TC-ERS-01 | Kontrastverstoss (Text/Hintergrund < 4,5 : 1) blockiert die Speicherung. | Testfarben-Paare. | PL-04 |
| TC-ERS-02 | Schaltflächenkontrast unter 3 : 1 blockiert die Speicherung. | — | PL-04 |
| TC-ERS-03 | Ungültiges Farbformat wird abgewiesen. | `#GGG` | PL-03 |
| TC-ERS-04 | Logo ohne Alternativtext wird abgewiesen. | — | PL-03, NF-03 |
| TC-ERS-05 | Erscheinungsbild wirkt auf alle Seiten der Lernorganisation und nur dort. | Mandantenübergreifend. | PL-03, TC-MAND-03 |

### 4.10 Nachweise (NW) — RA-13, NR-10

| ID | Beweist | Prüfung | Anf. |
|---|---|---|---|
| TC-NW-01 | Jede Freigabe erzeugt einen unveränderlichen Freigabenachweis. | Versuch, Nachweis zu ändern → abgewiesen. | AD-04, NF-04 |
| TC-NW-02 | Korrektur eines Nachweises erzeugt neue Fassung mit Verweis, nicht Änderung. | — | NR-10 |
| TC-NW-03 | Divergenzprotokoll enthält Differenz zwischen Entwurf und Endfassung. | — | RA-04 |
| TC-NW-04 | Provenienz einer Erklärung ist aus den Ausführungsdaten rekonstruierbar, ohne Modellabfrage. | — | RA-10, NR-07 |
| TC-NW-05 | Protokolle enthalten keine Passwörter, Sitzungs-IDs oder vollständige Antworttexte. | Suche nach Markern in Logs. | Betrieb |

### 4.11 Andragogik (AG)

Die Testfälle zur Andragogik stehen in [05 · Andragogik und SVEB](05_Andragogik_SVEB.md) (Prüfspalte). Sie sind Teil der Abnahme.

### 4.12 Barrierefreiheit (A11Y)

| ID | Beweist | Prüfung | Anf. |
|---|---|---|---|
| TC-A11Y-01 | Alle Seiten bestehen den automatischen Scan (axe-core) ohne schwerwiegende Verstösse. | Automatisch auf `test`. | NF-03 |
| TC-A11Y-02 | Alle Funktionen sind ohne Maus bedienbar. | Tastaturpfad-Test für Lernen, Prüfung, Lernbegleiter. | NF-03 |
| TC-A11Y-03 | Farbe ist nie das einzige Signal (Status, Sicherheitsgrad, Fehler). | Snapshot mit Textlabel. | NF-03 |
| TC-A11Y-04 | Schwierigkeitsslider ist per Tastatur und Screenreader bedienbar und bekannt beschriftet. | manuell + automatisch. | PR-02, NF-03 |

### 4.13 Nicht funktional und Sicherheit (NFT, SEC)

| ID | Beweist | Prüfung | Anf. |
|---|---|---|---|
| TC-NFT-01 | Seitenaufbau der Lernseiten < 1 s bei Referenzlast. | Messung auf `integration` (Zielwert D-12). | NF-10 |
| TC-NFT-02 | Upload-Extraktion blockiert die Oberfläche nicht. | Asynchron. | NF-10 |
| TC-NFT-03 | Konfigurationsänderung (Schwierigkeitsmix) ohne Codeänderung wirksam. | Konfigurationsdatei ändern, Ergebnis prüfen. | NF-09 |
| TC-SEC-01 | Statische Sicherheitsprüfung (bandit) ohne Befund hohen Schweregrads. | CI. | Betrieb |
| TC-SEC-02 | Abhängigkeiten ohne bekannte kritische Lücken (pip-audit). | CI. | Betrieb |
| TC-SEC-03 | Keine Schlüssel im Repository, auch nicht in der Historie. | Secret-Scan. | Betrieb |
| TC-SEC-04 | Datei-Upload-Grösse und Typ werden serverseitig geprüft. | — | IN-01 |

## 5 · Rückverfolgbarkeit: Muss-Anforderungen → Tests

| Anforderung | Testfälle |
|---|---|
| PL-01, PL-02 | TC-MAND-04 (+ Verwaltungstests Super-Admin) |
| PL-03, PL-04 | TC-ERS-01…05 |
| PL-05, NF-06 | TC-MAND-01, -02, -05 |
| BE-01…BE-03 | TC-LOG-02, -03 |
| BE-05 | TC-MAND-06 |
| MO-01…MO-05 | TC-MOD-01…04 |
| IN-01…IN-09 | TC-UPL-01…04, TC-FRE-01…06 |
| LE-01…LE-08 | TC-LRN-01…06, TC-PRF-07 |
| PR-01…PR-08 | TC-PRF-01…06 |
| BS-01…BS-07 | TC-BEG-01…08 |
| AD-01…AD-04 | TC-NW-01, TC-NW-03 (AD-02/03 Oberflächentests) |
| NF-01 | TC-LOG-04, -05, TC-SEC-01…04 |
| NF-02 | TC-BEG-04, TC-NW-05 (Datenschutz-Prüfliste offen, D-09) |
| NF-03 | TC-A11Y-01…04 |
| NF-04 | TC-KI-03, TC-NW-01, -02 |
| NF-07 | TC-KI-01, -02 |
| NF-09 | TC-NFT-03 |
| NF-10 | TC-NFT-01, -02 |
| Negativraum NR-01 … NR-10 | siehe §7 |

## 6 · Modell-Ground-Truth

Ein eigener Satz mit **fest definierten Erwartungen**, geschrieben vor der Modellauswahl und nicht aus Modellausgaben abgeleitet.

- Umfang Start: 40 Testfragen aus Musterunterlagen (sechs Lektionen), je mit erwarteter Lösung, erwarteter Quelle und Liste verbotener Aussagen.
- Prüfung: (a) Quellenkorrektheit durch Code, (b) Lösung durch Vergleich mit Erwartung, (c) Sprachprüfung durch Liste verbotener Muster; die inhaltliche Güte einer Erklärung wird **zusätzlich** von einer Lehrperson stichprobenartig bewertet (Prüfer ≠ Erzeuger).
- Abnahmeschwelle: (a) 100 % Quellentreue (Kern-Prüfung, Verstösse werden nie angezeigt); (b) mindestens Schwellenwert D-15 bei Lösungstreue; (c) keine verbotenen Muster in der Ausgabe.
- Protokoll je Lauf mit Modell, Version, Testset-Version, Ergebnis.
- Ein Modellwechsel verlangt einen neuen Lauf; die alte Freigabe gilt nicht mehr (ADR-L-005).

## 7 · Negativraum-Tests (NR-01 … NR-10)

| Kennung | Testfälle |
|---|---|
| NR-01 Entscheidung, die einem Menschen zusteht | TC-MOD-04, TC-BEG-03, TC-PRF-05 |
| NR-02 Fundstelle/Beleg ohne Quelle | TC-BEG-01, TC-PRF-07, TC-LRN-05 |
| NR-03 Modell direkt ansprechen | TC-KI-01, TC-KI-02 |
| NR-04 Mandantengrenze überschreiten | TC-MAND-01, -03, -05 |
| NR-05 freigegebener Zustand bei geändertem Inhalt | TC-FRE-01, -02, -03 |
| NR-06 Vokabular eigenmächtig erweitern | TC-NFT-03 erweitert um Vokabular-Abweisung (zu ergänzen: TC-VOK-01) |
| NR-07 Ergebnis ohne Herkunft | TC-NW-04 |
| NR-08 Zusicherung allein durch Anweisung an das Modell | TC-BEG-01, TC-BEG-03 (Kern-Prüfung statt Prompt) |
| NR-09 Bedeutung gespeicherter Werte ändern ohne Übergang | TC-PRF-04, TC-NW-02 |
| NR-10 ausgestellten Nachweis bearbeiten | TC-NW-01, TC-NW-02 |

**Lücke:** TC-VOK-01 (Vokabular-Abweisung) ist noch zu schreiben.

## 8 · Testprotokoll

Jeder Lauf erzeugt ein versioniertes Protokoll (YAML oder JSON), das **nicht überschrieben** wird.

```yaml
protokoll:
  id: "<uuid>"
  erzeugt_am: "2026-11-10T12:00:00Z"
  umgebung: develop            # develop | test | integration | main
  version_anwendung: "0.1.0"
  version_norm: "RA v0.3 · NR v0.3"
  version_testset: "TS-1"
  testarten:
    - art: unit
      ergebnis: bestanden        # bestanden | nicht_bestanden | nicht_geprueft
      anzahl: 212
      fehlgeschlagen: 0
    - art: kontrakt
      gegen: mock                # mock | real  (Pflicht, Scheinsicherheit vermeiden)
      ergebnis: bestanden
  modell:                        # nur wenn Modell beteiligt
    anbieter: "<über Adapter>"
    modell: "<Kennung>"
    version: "<Fassung>"
  faelle:
    - id: TC-MAND-01
      ergebnis: bestanden
  signatur: "<Hash über Inhalt>"
  herkunft: "Test-Runner"       # Mensch oder Modell darf nicht als Erzeuger eingetragen werden
```

- Ein Lauf ohne Protokoll hat nicht stattgefunden (RA-13).
- «Nicht geprüft» wird als solches ausgewiesen und zählt nicht als bestanden.
- Die Art **Kontrakt** und **Systemintegration** werden getrennt ausgewiesen.

## 9 · Ausführung und CI

- Lokal: `pytest` mit Markierungen `unit`, `mandant`, `kontrakt`, `e2e`, `modell`, `a11y`.
- CI (Jenkins, Docker): Lint → Unit → Kontrakt → Mandant → SAST/Abhängigkeiten → Protokoll. Ein roter Schritt stoppt die Pipeline.
- Auf `test`: Ende-zu-Ende und Barrierefreiheit. Auf `integration`: Modell-Ground-Truth, Lasttests, Smoke.
- Testdaten: nur synthetische Daten; keine echten Studierendendaten in Tests (NF-02).

## 10 · Abnahme

Die Abnahme ist erfüllt, wenn:

1. Alle Muss-Testfälle des Abschnitts 5 **bestanden** im Protokoll stehen.
2. Keine offenen Muss-Befunde aus dem Konformitätsnachweis bestehen.
3. TC-MAND-01…06 auf `integration` bestanden sind.
4. Die Modell-Ground-Truth für das eingesetzte Modell bestanden ist.
5. Die Andragogik-Prüfliste (05) gegengelesen ist.

Abnahme durch Auftraggeber erfolgt auf `test`; Freigabe zu `integration` und `main` ist eine bewusste, dokumentierte Handlung (Betriebsmodul).

## 11 · Offene Testpunkte

- TC-VOK-01 schreiben (Vokabular-Abweisung).
- Ground-Truth-Testset erstellen (40 Fragen) — Quelle: Musterunterlagen des Auftraggebers (D-16).
- Grenzwerte für Fehlversuche (D-14) und Ground-Truth-Schwelle (D-15) festlegen.
- Testdaten-Generator mit synthetischen Lernorganisationen und Konten.
