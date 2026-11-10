# 07 · Umsetzung und Nachweise

**Stand:** 2026-11-10 · Wird bei jedem Inkrement fortgeschrieben.

Dieses Dokument trennt ausdrücklich vier Stufen des Nachweises:

| Stufe | Bedeutung |
|---|---|
| **dokumentiert** | in den Dokumenten 01–06 festgehalten |
| **implementiert** | im Code vorhanden |
| **simuliert** | im Ablauf mit dem Testadapter geprüft (Antworten sind als `SIMULIERT` gekennzeichnet) |
| **mit echtem Modell geprüft** | über den Vorschaltdienst gegen ein echtes Modell gelaufen (Protokoll mit Modellversion) |

---

## 1 · Inkrementplan

| Inkrement | Inhalt | Status |
|---|---|---|
| **1** | Lokaler durchgängiger Lernablauf: Lernorganisation, Anmeldung, Rollen, Modul, Zuweisungen, Lektion mit Lernzielen, Textunterlage mit Freigabe, Übung, Antwort mit Hilfen, formative Rückmeldung mit Quelle, Rückfrage, Speicherung des Versuchs und Lernprofils | in Umsetzung |
| 2 | Weitere Formate (PDF, DOCX, PPTX); Modellerzeugung von Ebene-B-Aufgaben über Adapter mit Kernprüfung; offene Antworten mit Bewertungsraster; Meldungsablauf mit Entscheid; Ebene-C-Prüfansicht; Divergenzprotokoll; Modell-Ground-Truth | geplant |
| 3 | Testprüfungen; Prüfungsrahmen (Struktur; Inhalt nach D-22); Regler; Modi Lernen und Simulation; Unterbrechung nach Rahmen | geplant, blockiert durch D-22 nur für Inhalte |
| 4 | Mehrere Lektionen gleichzeitig (Ausbau); Erscheinungsbild und Kontrast-Prüfung (PL-03, PL-04); CSV-Import (AD-01); Kontoverwaltung vollständig | geplant |
| 5 | PostgreSQL mit RLS als Standard (A-2); Betrieb, Konfiguration, Deployment (D-11) | geplant |
| Phase 2 | Zwei-Faktor, Selbstservice-Passwort, Modul-Feedback (AG-11), Spracheingabe über Vorschaltdienst | geplant |

**Reihenfolge-Begründung:** Inkrement 1 beweist den Ablauf und die Rechte. Es braucht kein Modell, kein Erscheinungsbild und keine Prüfungsvorlage. Damit ist der Ablauf vollständig prüfbar.

---

## 2 · Anforderungsstatus Inkrement 1

Legende: **impl.** implementiert · **sim.** im Ablauf mit Testadapter geprüft · **dok.** dokumentiert, nicht Inkrement 1 · **offen** blockiert.

| Kennung | Anforderung (Kurzform) | Stand Inkr. 1 | Testnachweis |
|---|---|---|---|
| PL-01 | Super-Admin legt Lernorganisation und Erstadministration an | — | — |
| PL-02 | Super-Admin ohne Inhaltszugriff | — | — |
| PL-05 | strukturelle Mandantentrennung | — | — |
| BE-01 | Anmeldung Benutzername/Passwort | — | — |
| BE-02 | Argon2id | — | — |
| BE-03 | Sperre nach Fehlversuchen | — | — |
| BE-05 | Rollen in mehreren Lernorganisationen | — | — |
| BE-07 | serverseitige Sitzungen | — | — |
| MO-01 bis MO-05 | Module, Zuweisungen, Lektionsstruktur | — | — |
| MO-07 | Lernziele mit Handlungsstufe | — | — |
| IN-01 | Upload Text und Markdown | — | — |
| IN-02, IN-03 | Zuordnung zu Lektion, nachträglich | — | — |
| IN-04, IN-10 | Abschnitte mit stabiler ID | — | — |
| IN-05 | Versionen | — | — |
| IN-06, IN-08 | fachliche Freigabe, Formen | — | — |
| IN-07 | Änderung setzt `in_pruefung` | — | — |
| LE-01 | Lektion wählen und üben | — | — |
| LE-02 | mehrere Lektionen wählen | — | — |
| LE-04 | Lernprofil je Lernziel | — | — |
| LE-05 | Quelle je Aufgabe und Rückmeldung | — | — |
| LE-06 | Aufgaben nur aus freigegebenen Abschnitten | — | — |
| LE-07 | Ebene B unmittelbar verfügbar | — | — |
| LE-08 | Meldung setzt Aufgabe aus | dok. (Meldung Inkr. 2) | — |
| LE-11 | Versuchstreue | — | — |
| LE-12 | Hilfekennzeichnung | — | — |
| PR-04 | Hilfen am Versuch vermerkt | — | — |
| PR-05 | Punkte begrenzt, Prozent konsistent | — | — |
| PR-06 | Versuch vollständig gespeichert | — | — |
| PR-07 | Übung mit Ebene-B-Aufgaben | — | — |
| BS-01 | Gespräch zum Ergebnis | — | — |
| BS-02 | Quellen-ID-Prüfung | — | — |
| BS-03 | Lernprofil in Erklärung | — | — |
| BS-04, BS-05 | Sicherheitsgrad, Lücke benennen | — | — |
| BS-06 | formativ, keine Note | — | — |
| BS-08 | Formen Hinweis, Rückfrage, Beispiel, Erklärung | — | — |
| BS-10 | Rückmeldung mit nächstem Schritt | — | — |
| AD-02 | Admin sieht Module und Konten | — | — |
| AD-04 | Änderungen protokolliert | — | — |
| NF-06 | Mandantentests | — | — |
| NF-07 | Modellzugang nur über Adapter | — | — |
| NF-12 | keine Zugangsdaten im Repository | — | — |

Ausstehend für Inkrement 1 nach Ergebnis: siehe Abschnitt 4.

---

## 3 · Abweichungen (Abweichungsregister)

| ID | Abweichung | Grund | Auswirkung | Behebung |
|---|---|---|---|---|
| **A-1** | Entwicklungsdatenbank SQLite statt PostgreSQL | Lokaler Start ohne Serverinstallation; PostgreSQL-Container ist vorgesehen | Keine RLS-Durchsetzung in Entwicklung; Mandantentrennung nur durch Code-Struktur und Tests | Tests laufen zusätzlich gegen PostgreSQL-Container in Inkr. 5 (A-2) |
| **A-2** | RLS noch nicht umgesetzt | Inkrement 1 fokussiert den Ablauf | Schutz hängt im Inkrement 1 von der Repository-Schicht ab | Inkr. 5 |
| **A-3** | Modellerzeugung von Aufgaben nicht im Inkrement 1 | Ablauf ohne Modell prüfbar; Aufgaben werden von Lehrpersonen vorbereitet | Keine automatische Aufgabenerzeugung im Inkr. 1 | Inkr. 2 |
| **A-4** | Erklärungen im Inkrement 1 deterministisch (aus Lösungsbegründung) | Verlässlich und ohne Modell prüfbar | Keine individuellen Formulierungen über Textbausteine hinaus; Individualisierung über Lernprofil-Auswahl | Modellvariante Inkr. 2 |
| **A-5** | Live-Anbindung an den Vorschaltdienst | Laufzeitstatus nicht bestätigt (D-05) | Modellpfad nur über Testadapter geprüft | Live-Test, wenn Dienst antwortet |
| **A-6** | Keine Textextraktion für PDF/DOCX/PPTX | Inkrement-Umfang | nur `.txt` und `.md` | Inkr. 2 |
| **A-7** | Lernziel-Evidenz ohne Ebene C | Ebene-C-Prüfung ist Inkr. 2 | Aufgaben sind Ebene B oder ungeprüft-Vorlagen der Lehrperson | Inkr. 2 |

Keine stille Abweichung: jede Abweichung steht hier und im Konformitätsnachweis (Dok. 02 §2).

---

## 4 · Testergebnisse Inkrement 1

*Wird nach der Ausführung eingetragen. Enthält: Anzahl, Ergebnis, Befehl, Datum, Umgebung, Modellherkunft.*

---

## 5 · Startanleitung

*Wird mit dem Code geliefert (siehe Abschnitt 6).*

---

## 6 · Fortschreibung

Jede Änderung an Anforderungen, Entscheidungen oder Abweichungen wird hier und im Änderungsprotokoll von Dok. 01 vermerkt. Ein Commit trägt die Kennungen, die er betrifft.
