# 07 · Umsetzung und Nachweise

**Stand:** 2026-11-10 · Inkrement 1 umgesetzt und getestet (lokal). Wird bei jedem Inkrement fortgeschrieben.

Vier Stufen des Nachweises werden nie vermischt:

| Stufe | Bedeutung in diesem Projekt |
|---|---|
| **dokumentiert** | in den Dokumenten 01–06 festgehalten |
| **implementiert** | im Code vorhanden |
| **simuliert** | im Ablauf mit dem Testadapter geprüft; jede Modellausgabe trägt `herkunft: SIMULIERT` |
| **mit echtem Modell geprüft** | gegen den Vorschaltdienst und ein echtes Modell gelaufen — **bisher nicht erfolgt** |

---

## 1 · Inkrementplan

| Inkrement | Inhalt | Status |
|---|---|---|
| **1** | Lokaler durchgängiger Lernablauf: Lernorganisation, Anmeldung, Rollen, Modul, Zuweisungen, Lektion mit Lernzielen, Textunterlage mit Freigabe, Übung, Hilfen, Antwort, formative Rückmeldung mit Quelle, Rückfrage, Versuch und Lernprofil | **umgesetzt, getestet** (simuliert; kein echter Modelllauf) |
| 2 | PDF, DOCX, PPTX; Aufgabenerzeugung (Ebene B) über den Adapter mit Kernprüfung; offene Antworten mit Bewertungsraster; Meldungsablauf (LE-08, LE-10); Ebene-C-Prüfansicht; Divergenzprotokoll; Modell-Ground-Truth; Aufgabe bearbeiten mit Versionierung | geplant |
| 3 | Testprüfungen; Prüfungsrahmen (Struktur steht, Inhalt fehlt: D-22); Regler; Modi Lernen und Simulation | geplant; Inhalte blockiert durch D-22 |
| 4 | Erscheinungsbild und Kontrast-Prüfung (PL-03, PL-04); CSV-Import (AD-01); Kontoverwaltung vollständig; Ausbau mehrerer Lektionen in einer Übung | geplant |
| 5 | PostgreSQL mit RLS als Standard (A-2), Tests gegen PostgreSQL-Container; Betrieb und Deployment (D-11) | geplant |
| Phase 2 | Zwei-Faktor, Selbstservice-Passwort, Modul-Feedback (AG-11), Spracheingabe nur über Vorschaltdienst | geplant |

---

## 2 · Anforderungsstatus Inkrement 1

Legende: **umgesetzt** (Code + Test) · **teilweise** · **Inkr. N** (später geplant).

| Kennung | Anforderung (Kurzform) | Stand | Tests (Datei :: Funktion) |
|---|---|---|---|
| PL-01 | Super-Admin legt Organisation und Erstadministration an | umgesetzt | test_mandant_und_rollen :: test_superadmin_sieht_nur_registrierungsdaten (indirekt); Demo Schritt 2 |
| PL-02 | Super-Admin ohne Inhaltszugriff | umgesetzt | test_mandant_und_rollen :: test_superadmin_hat_keinen_zugriff_auf_inhalte, :: test_superadmin_sieht_nur_registrierungsdaten |
| PL-03, PL-04 | Erscheinungsbild, Kontrast | Inkr. 4 | — |
| PL-05 | Mandantentrennung im Code | umgesetzt (Abweichung A-2) | test_mandant_und_rollen :: test_mandantenlose_abfrage_wird_verweigert, :: test_mandant_abfrage_liefert_nur_eigene_zeilen, :: test_fremde_unterlage_ist_nicht_auffindbar, :: test_fremdes_modul_nicht_in_liste_und_nicht_lesbar |
| BE-01 | Anmeldung Benutzername/Passwort, keine Kontenerkennung | umgesetzt | test_anmeldung :: test_fehlermeldung_verraet_keine_kontenexistenz |
| BE-02 | Argon2id, kein Klartext | umgesetzt | test_anmeldung :: test_passwort_nur_als_argon2_hash, :: test_zu_kurzes_passwort_wird_abgelehnt |
| BE-03 | Sperre nach Fehlversuchen | umgesetzt | test_anmeldung :: test_fehlversuche_sperren_konto_auch_bei_richtigem_passwort |
| BE-05 | Konto in mehreren Organisationen, getrennte Sitzung | umgesetzt | test_anmeldung :: test_konto_in_zwei_organisationen_mit_getrennten_sitzungen |
| BE-04, BE-06 | Selbstservice-Passwort, Zwei-Faktor | Phase 2 | — |
| BE-07 | serverseitige Sitzung, Abmelden | umgesetzt (signiertes Cookie; serverseitige Sitzungsverwaltung offen, A-13) | test_mandant_und_rollen :: test_sitzungscookie_ist_httponly |
| MO-01, MO-02 | Module anlegen, zuweisen | umgesetzt | test_mandant_und_rollen :: test_studierende_sieht_nur_zugewiesene_module; Demo Schritte 4–5 |
| MO-03, MO-04 | nur zugewiesene Module | umgesetzt | test_mandant_und_rollen :: test_studierende_sieht_nur_zugewiesene_module |
| MO-05 | Lektionsstruktur durch Mensch | umgesetzt (kein Automatismus) | Demo Schritt 6 |
| MO-06 | umsortieren, archivieren | teilweise (anlegen, Reihenfolge; Archivieren Inkr. 4) | — |
| MO-07 | Lernziele mit Handlungsstufe | umgesetzt | test_ablauf_durchgaengig :: test_durchgaengiger_lernablauf (indirekt) |
| IN-01 | Upload Text und Markdown, Typprüfung | umgesetzt (nur .txt/.md; Abweichung A-6) | Demo Schritt 7 |
| IN-02, IN-03 | Zuordnung zu Lektion, nachträglich | teilweise (Zuordnung bei Upload; Nachträgliche Änderung Inkr. 4) | — |
| IN-04 | Abschnittsbildung, Fehler sichtbar | umgesetzt (Fehler: Textprüfung) | test_kern :: test_abschnitte_lueckenlos_und_begrenzt, :: test_markdown_ueberschrift_beginnt_neuen_abschnitt |
| IN-05 | Versionen | umgesetzt | test_freigabe_und_versuch :: test_aenderung_freigegebener_unterlage_setzt_status_zurueck |
| IN-06 | fachliche Freigabe vor Wirkung | umgesetzt | test_mandant_und_rollen :: test_admin_gibt_nicht_frei, :: test_assistenz_darf_nicht_freigeben_ohne_delegation |
| IN-07 | Änderung setzt `in_pruefung`, Aufgaben ausgeblendet | umgesetzt | test_freigabe_und_versuch :: test_aenderung_freigegebener_unterlage_setzt_status_zurueck, :: test_aufgaben_in_pruefung_sind_ausgeblendet_und_nicht_bearbeitbar |
| IN-08 | Freigabeformen mit Auflage und nicht freigebbar | umgesetzt | test_freigabe_und_versuch :: test_freigabe_unter_auflage_braucht_verantwortliche_und_zukunftsfrist, :: test_nicht_freigebbar_verlangt_begruendung, :: test_neue_fassung_nach_ablehnung_kehrt_in_den_entwurf |
| IN-09 | Herkunft je Unterlage | umgesetzt (hochgeladen_von, Version) | — (Feld vorhanden) |
| IN-10 | stabile Abschnitt-IDs und Position | umgesetzt | test_ablauf_durchgaengig :: test_durchgaengiger_lernablauf |
| LE-01, LE-02 | Lektion(en) wählen, üben | umgesetzt | test_ablauf_durchgaengig; Demo Schritt 12 |
| LE-03 | Wiederholungsplan, deterministisch | umgesetzt (Planung; Anzeige in Inkr. 2) | test_kern :: test_sm2_referenzwerte, :: test_sm2_falsch_setzt_zurueck_und_ease_untergrenze, :: test_sm2_intervall_obergrenze |
| LE-04 | Lernprofil mit Evidenzlage und Datum | umgesetzt | test_kern :: test_hilfe_zaehlt_nicht_als_selbststaendig, :: test_mehrere_richtige_auf_dieselbe_aufgabe_zaehlen_einmal, :: test_ausreichend_erst_ab_schwelle_und_widerspruch |
| LE-05 | Quelle je Aufgabe und Rückmeldung | umgesetzt | test_ablauf_durchgaengig :: test_durchgaengiger_lernablauf |
| LE-06 | Aufgaben nur aus freigegebenen Abschnitten | umgesetzt | test_freigabe_und_versuch :: test_aufgaben_in_pruefung_sind_ausgeblendet_und_nicht_bearbeitbar |
| LE-07 | Ebene B ohne Vorabfreigabe | umgesetzt (Assistenz-Anlage ergibt Ebene B; Modellerzeugung Inkr. 2) | test_mandant_und_rollen :: test_delegierte_assistenz_darf_freigeben (Anlage) |
| LE-08, LE-10 | Meldung, Entscheid | Inkr. 2 | — |
| LE-09 | Ebene-C-Prüfung | Dienst vorhanden (`aufgabe_fachlich_pruefen`), Ansicht Inkr. 2 | — |
| LE-11 | Versuche bleiben unverändert | umgesetzt (Kopie je Versuch) | test_freigabe_und_versuch :: test_versuch_bleibt_unveraendert_wenn_aufgabe_spaeter_geaendert_wird |
| LE-12 | Hilfe erkennbar am Versuch | umgesetzt | test_freigabe_und_versuch :: test_hilfe_vor_antwort_wird_vermerkt_und_zaehlt_nicht_selbststaendig |
| PR-01 bis PR-03, PR-09 bis PR-12 | Testprüfungen, Prüfungsrahmen, Regler, Modi | Inkr. 3 | — (D-22) |
| PR-04 | Hilfen vermerkt | umgesetzt | test_freigabe_und_versuch :: test_hilfe_vor_antwort_wird_vermerkt_und_zaehlt_nicht_selbststaendig |
| PR-05 | Punkte im Maximum, Prozent konsistent | umgesetzt | test_kern :: test_single_choice_voll_oder_null, :: test_multiple_choice_teilpunkte_nie_negativ_nie_ueber_maximum, :: test_prozent_konsistent_und_null_maximum; test_freigabe_und_versuch :: test_richtige_antwort_mit_punkten_im_maximum |
| PR-06 | Versuch vollständig gespeichert | umgesetzt | test_freigabe_und_versuch :: test_versuch_bleibt_unveraendert… |
| PR-07 | Übungen mit Ebene B | umgesetzt | test_ablauf_durchgaengig |
| PR-08 | nicht auffüllen, ehrlich melden | umgesetzt | test_freigabe_und_versuch :: test_aufgaben_in_pruefung_sind_ausgeblendet_und_nicht_bearbeitbar |
| PR-13 | formativ, keine Note | umgesetzt (keine Notenfunktion) | Prüfung durch Fehlen einer Notenausgabe |
| BS-01 | Gespräch zum Ergebnis | umgesetzt | test_ablauf_durchgaengig; test_web_oberflaeche; Demo Schritt 16 |
| BS-02 | Quellen-ID-Prüfung im Kern | umgesetzt | test_lernbegleiter_und_modell :: test_fremde_quelle_wird_abgelehnt |
| BS-03 | Lernprofil in Erklärung | teilweise (Aufruf enthält Lernziele; Lernprofil-Auswahl Inkr. 2) | test_lernbegleiter_und_modell (Auftragsaufbau) |
| BS-04 | Sicherheitsgrad und Annahmen | umgesetzt | test_lernbegleiter_und_modell :: test_erfolgreiche_antwort_trägt_quelle_und_fachlich_ungeprueft |
| BS-05 | Lücke benennen | umgesetzt | test_lernbegleiter_und_modell :: test_antwort_ohne_quelle_wird_als_unbelegt_benannt, :: test_simulation_ohne_ueberschneidung_meldet_luecke |
| BS-06 | formativ, keine Bewertungssprache | umgesetzt | test_lernbegleiter_und_modell :: test_bewertungssprache_wird_abgelehnt |
| BS-07 | Gespräche nur für Berechtigte | teilweise (Versuch nur eigener Konto; Lehrsicht fehlt) | test_freigabe_und_versuch :: test_fremder_versuch_ist_nicht_sichtbar |
| BS-08 | Formen Hinweis, Rückfrage, Beispiel, Erklärung | umgesetzt (Auswahl), Qualität ungeprüft | Demo Schritt 16 |
| BS-09 | offene Antworten mit Raster | Inkr. 2 | — |
| BS-10 | nächster Schritt | umgesetzt | test_ablauf_durchgaengig (naechster_schritt in Antwort) |
| AD-01 | CSV-Import | Inkr. 4 | — |
| AD-02 | Admin sieht Module und Konten | teilweise (Module, Konten-Anlage; Übersicht Inkr. 4) | Demo Schritt 3–5 |
| AD-03 | aggregierte Lernprofile | umgesetzt (Zählung) | test_… (Demo Schritt 18: Studierende 403) |
| AD-04 | Änderungen protokolliert | umgesetzt (Nachweis je Verwaltungsschritt) | Nachweis-Art `zuweisung`, `freigabe`, `konto_angelegt` |
| NF-01 | HTTPS, Cookie-Schutz, CSRF | teilweise (Cookie- und CSRF-Prüfung; HTTPS im Betrieb offen) | test_mandant_und_rollen :: test_schreibende_anfrage_ohne_csrf_wird_abgewiesen, :: test_sitzungscookie_ist_httponly |
| NF-02 | Datenschutz | teilweise (Pseudonym im Modellaufruf; Löschkonzept D-09 offen) | test_lernbegleiter_und_modell :: test_konstante_kopfzeilen_nicht_aus_eingabe |
| NF-03 | Barrierefreiheit | teilweise (Beschriftungen, Sprachangabe; kein automatischer Scan) | — (Inkr. 2) |
| NF-04 | Nachweise | umgesetzt (Versuch, Freigabe, Aufruf, Anmeldung, Sperre) | test_ablauf_durchgaengig :: Nachweis-Arten |
| NF-05 | Deutsch, Schweizer Schreibweise | umgesetzt in Texten | — |
| NF-06 | Mandantentests | umgesetzt | test_mandant_und_rollen (siehe PL-05) |
| NF-07 | Modellzugang nur über Adapter | umgesetzt (Vertrag); Dienst läuft, Anwendung noch nicht registriert (D-05) | test_lernbegleiter_und_modell :: test_vertrag_setzt_drei_pflichtkopfzeilen, :: test_409_…, :: test_502_…, :: test_503_…; test_live_vorschaltdienst |
| NF-12 | keine Zugangsdaten im Repository | umgesetzt (Demo-Passwörter zufällig, nur Konsole; Testpasswörter nur in Testdatenbank) | Prüfung durch Review |

**Nicht getestet im Inkrement 1:** Die fachliche Qualität von Aufgaben und Rückmeldungen an einem Referenzsatz (Abnahmekriterium der Anforderung 7). Der Referenzsatz besteht aus zwei synthetischen Aufgaben; eine fachliche Bewertung durch eine Lehrperson steht aus.

---

## 3 · Abweichungsregister

| ID | Abweichung | Grund | Auswirkung | Behebung |
|---|---|---|---|---|
| **A-1** | Entwicklungsdatenbank SQLite statt PostgreSQL | lokaler Start ohne Serverinstallation | keine RLS-Durchsetzung im Entwicklungsbetrieb; Mandantentrennung nur durch Repository-Struktur und Tests | Inkr. 5 (PostgreSQL-Container) |
| **A-2** | RLS nicht umgesetzt | Inkrement 1 fokussiert den Ablauf | Schutz hängt von der Repository-Schicht ab; Tests prüfen das | Inkr. 5 |
| **A-3** | Aufgabenerzeugung durch Modell nicht im Inkrement 1 | Ablauf ohne Modell prüfbar; Aufgaben werden von Lehrpersonen oder Assistenz angelegt | keine automatische Erzeugung | Inkr. 2 |
| **A-4** | Rückmeldung zu Aufgaben deterministisch (Lösungsbegründung) | verlässlich, ohne Modell prüfbar | keine individuellen Formulierungen über den hinterlegten Text hinaus | Inkr. 2 |
| **A-5** | Keine Anwendungsanbindung an den Vorschaltdienst | Anwendung `lernsoftware` nicht registriert; kein Anbieterschlüssel | 409- und 503-Verhalten nur gegen Testdouble geprüft | Registrierung nach Freigabe, dann Live-Test der Fehlerfälle |
| **A-6** | Nur `.txt` und `.md` | Inkrement-Umfang | keine PDF/DOCX/PPTX-Unterlagen | Inkr. 2 |
| **A-7** | Ebene C (fachlich geprüft) nur über Anlage durch Lehrperson; keine Prüfansicht | Inkr. 2 | Prüfstatus-Anzeige vollständig erst mit Inkr. 2 | Inkr. 2 |
| **A-8** | Aufgaben können nicht bearbeitet werden (nur anlegen und fachlich prüfen) | Inkr. 2 mit Versionierung | Änderung einer Aufgabe nur über neue Aufgabe | Inkr. 2 |
| **A-9** | Lernbegleiter-Erklärung ohne Modell: Standardtext; mit Testadapter: einfache Wortüberschneidung (SIMULIERT) | keine echte Modellprüfung vorhanden | Qualität der Rückfrage ist **nicht** bewertet | echter Modelllauf + Ground-Truth (Inkr. 2) |
| **A-10** | Browser-Oberfläche minimal; Verwaltung über Schnittstelle und Demo | Bedienungsnorm fehlt (D-10) | Verwaltung nicht per Oberfläche | Inkr. 4 bzw. nach D-10 |
| **A-11** | Argon2-Parameter in Tests reduziert | Testlaufzeit | Produktwerte stehen in `config/basis.yaml` und werden in den Tests nicht geprüft | ein Test mit Produktwerten vor Abnahme |
| **A-12** | Wiederholung nur berechnet und in der Antwort angezeigt, keine Übersicht | Inkr. 2 | Fälligkeit ist nicht als Liste sichtbar | Inkr. 2 |
| **A-13** | Sitzung als signiertes Cookie (Flask), nicht serverseitig widerrufbar | Inkrement-Umfang | Abmeldung wirkt auf dem Client; ein gestohlenes Cookie bleibt bis zum Ablauf gültig | Serverseitige Sitzungsliste vor Betrieb (Inkr. 5) |

Keine stille Abweichung: jede Abweichung steht hier und im Konformitätsnachweis (Dokument 02 §2).

---

## 4 · Testergebnisse Inkrement 1

**Protokoll:** `docs/nachweise/testprotokoll-20261110T121013Z.json` (RA-13, nicht überschreiben; Erzeugung nur mit `LERNSOFTWARE_PROTOKOLL=1`).

| Ergebnis | Anzahl |
|---|---|
| bestanden | 64 |
| **nicht bestanden** | **1** (`test_live_vorschaltdienst.py::test_vorschaltdienst_gesundheit_erreichbar`: Dienst nicht erreichbar) |
| nicht geprüft (übersprungen) | 0 |

**Modellherkunft der Testläufe:** alle Läufe mit Testadapter (SIMULIERT). **Kein Testlauf mit einem echten Modell.**

**Befehl:**

```bash
LERNSOFTWARE_PROTOKOLL=1 VORSCHALT_LIVE=1 python -m pytest
```

Ohne `VORSCHALT_LIVE=1` wird der Live-Test als *nicht geprüft* protokolliert, nicht als bestanden.

**Prüfung des Vorschaltdienstes (2026-11-10, nach Start auf Anweisung):**

- Der Dienst wurde im Modus `develop` auf `127.0.0.1:8040` gestartet (Schlüssel nur als Prozess-Umgebungsvariable, nicht gespeichert).
- Health-Endpunkt: `status: bereit`, Version 0.0.1, Wortliste geladen, Stufe C inaktiv. **Live-Test bestanden.**
- Vertrag ohne Anbieteraufruf: Fehlende Kopfzeilen → 400 `kontext_fehlt`. Unbekannte Anwendung → 400 `kontext_fehlt`.
- **Offen:** Die Anwendung `lernsoftware` ist im Dienst **nicht registriert** (ANBINDUNG.md, Schritt 1). Dadurch sind die Antworten 409 (Entscheidung nötig) und 503 (kein Anbieterschlüssel) von hier aus noch nicht prüfbar. Die Registrierung ist eine Änderung an den Daten des Pseudonymisierungsdienstes und braucht eine Freigabe. **Kein Anbieterschlüssel wurde hinterlegt**; deshalb ist kein Aufruf an einen Anbieter möglich.

**Demonstration:** `python -m app.demo` läuft ohne Fehler durch. Die Ausgabe zeigt je Schritt den HTTP-Status; die Abweisungen (Assistenz ohne Freigabe: 403; Studierende ohne Lehrsicht: 403; fremde Organisation: 404) sind darin sichtbar.

---

## 5 · Startanleitung (lokal)

Voraussetzungen: Python 3.13 (Windows), Projektordner `C:\Projekte\Lernsoftware`.

```bash
cd C:\Projekte\Lernsoftware
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Demonstrationsablauf (legt eine frische Entwicklungsdatenbank unter `instance/demo.sqlite3` an):

```bash
.venv\Scripts\python.exe -m app.demo
```

Server im Browser (Studierendenansicht, nur lokal erreichbar): Zuerst die Demo-Datenbank wählen, dann starten.

```bash
export DATABASE_URL="sqlite:///instance/demo.sqlite3"
.venv/Scripts/python.exe run.py
```

Dann `http://127.0.0.1:5050/anmelden` öffnen. Organisation `beispiel-hs`, Benutzer `student`; das Passwort gibt `python -m app.demo` auf der Konsole aus (zufällig, nicht gespeichert). Die Oberfläche zeigt Studierenden Module, Übungen, Hilfen, Rückmeldungen und Rückfragen. Verwaltung läuft über `/api/v1/…` (Spezifikation §13).

Tests:

```bash
.venv\Scripts\python.exe -m pytest
```

Ein Zugang mit einem echten Vorschaltdienst ist nur mit `MODELL_MODUS=vorschaltdienst` und laufendem Dienst vorgesehen (noch nicht geprüft, A-5).

---

## 6 · Fortschreibung

Jede Änderung an Anforderungen, Entscheidungen oder Abweichungen wird hier und im Änderungsprotokoll von Dokument 01 vermerkt. Ein Commit nennt die Kennungen, die er betrifft.
