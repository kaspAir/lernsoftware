# 07 · Umsetzung und Nachweise

**Stand:** 2026-11-10 · Inkrement 1.1 «verlässlicher Lernablauf» umgesetzt und getestet (lokal, mit Testadapter).

Vier Stufen des Nachweises werden nie vermischt:

| Stufe | Bedeutung in diesem Projekt |
|---|---|
| **dokumentiert** | in den Dokumenten 01–06 festgehalten |
| **implementiert** | im Code vorhanden |
| **simuliert** | im Ablauf mit dem Testadapter geprüft; jede Ausgabe trägt `herkunft: SIMULIERT` |
| **mit echtem Modell geprüft** | gegen den Vorschaltdienst und ein echtes Modell gelaufen — **bisher nicht erfolgt** |

---

## 1 · Inkrementplan

| Inkrement | Inhalt | Status |
|---|---|---|
| 1 | Lokaler Lernablauf (Grundfassung) | umgesetzt (Commit `b51f55d`) |
| **1.1** | **Verlässlicher Lernablauf:** einheitliches Antwortformat, wirksame Hilfen, idempotente Abgabe, gemeinsame Prüfungen, dauerhafte Versuchssicht, mehrere Rückfragen, strenge Modellvalidierung, Sitzungsregeln, reproduzierbarer Start, Testnachweise nach Art | **umgesetzt, getestet** (simuliert; kein echter Modelllauf) |
| 2 | Reales Kursmodul mit einfacher Dozentenoberfläche; echte Modellanbindung (nach D-05/D-07); automatische Fragenerzeugung mit Ebene B; PDF/DOCX/PPTX; Meldungsablauf; Ebene-C-Prüfansicht; Aufgabe bearbeiten mit Versionierung; Modell-Ground-Truth | geplant (Vorschlag in Abschnitt 8) |
| 3 | Testprüfungen; Prüfungsrahmen (Struktur steht, Inhalt fehlt: D-22); Regler; Modi Lernen und Simulation | geplant; Inhalte blockiert durch D-22 |
| 4 | Erscheinungsbild und Kontrast-Prüfung (PL-03, PL-04); CSV-Import (AD-01); Kontoverwaltung vollständig | geplant |
| 5 | PostgreSQL mit RLS als Standard (ADR-L-002/-006, A-2); Tests gegen PostgreSQL-Container; serverseitige Sitzungsliste (A-13); Betrieb und Deployment (D-11) | geplant |
| Phase 2 | Zwei-Faktor, Selbstservice-Passwort, Modul-Feedback (AG-11), Spracheingabe nur über Vorschaltdienst | geplant |

**Einheitliche Festlegung zu PostgreSQL/RLS:** Das Ziel ist PostgreSQL mit RLS (ADR-L-002, ADR-L-006). Umgesetzt wird es **in Inkrement 5**. Bis dahin gilt die Repository-Struktur mit Tests (A-1, A-2). Alle Dokumente verweisen auf diese Festlegung.

---

## 2 · Anforderungsstatus Inkrement 1 und 1.1

Legende: **umgesetzt** (Code und Test) · **teilweise** · **Inkr. N** (später geplant).

| Kennung | Anforderung (Kurzform) | Stand | Tests (Datei :: Funktion) |
|---|---|---|---|
| PL-01, PL-02 | Super-Admin legt Organisation an, sieht nur Registrierungsdaten | umgesetzt | test_mandant_und_rollen :: test_superadmin_sieht_nur_registrierungsdaten, :: test_superadmin_hat_keinen_zugriff_auf_inhalte; test_zugriff_sitzung_rollen :: test_deaktivierter_superadmin_verliert_zugang |
| PL-03, PL-04 | Erscheinungsbild, Kontrast | Inkr. 4 | — |
| PL-05, NF-06 | Mandantentrennung im Code | umgesetzt (A-1, A-2) | test_mandant_und_rollen :: test_mandantenlose_abfrage_wird_verweigert, :: test_mandant_abfrage_liefert_nur_eigene_zeilen, :: test_fremde_unterlage_ist_nicht_auffindbar, :: test_fremdes_modul_nicht_in_liste_und_nicht_lesbar |
| BE-01 | Anmeldung, keine Kontenerkennung | umgesetzt | test_anmeldung :: test_fehlermeldung_verraet_keine_kontenexistenz |
| BE-02 | Argon2id, kein Klartext | umgesetzt | test_anmeldung :: test_passwort_nur_als_argon2_hash |
| BE-03 | Sperre nach Fehlversuchen | umgesetzt | test_anmeldung :: test_fehlversuche_sperren_konto_auch_bei_richtigem_passwort |
| BE-05 | Konto in mehreren Organisationen | umgesetzt | test_anmeldung :: test_konto_in_zwei_organisationen_mit_getrennten_sitzungen |
| BE-07 | Sitzung, 120 Minuten ab Anmeldung | umgesetzt (A-13) | test_zugriff_sitzung_rollen :: test_sitzungsgrenze_ist_120_minuten_ab_anmeldung, :: test_sitzung_laeuft_nach_ablauf_im_api_ab, :: test_sitzung_im_browser_laeuft_ab |
| BE-04, BE-06 | Selbstservice-Passwort, Zwei-Faktor | Phase 2 | — |
| MO-01, MO-02 | Module anlegen, zuweisen | umgesetzt | test_mandant_und_rollen :: test_studierende_sieht_nur_zugewiesene_module |
| MO-02 (Regel) | Genau eine Modulrolle je Konto und Modul | umgesetzt (Festlegung 1.1, D-25) | test_zugriff_sitzung_rollen :: test_genau_eine_modulrolle_je_konto_und_modul, :: test_mehrfachrolle_verliert_keine_bisherigen_rechte |
| MO-03, MO-04 | nur zugewiesene Module | umgesetzt | test_mandant_und_rollen :: test_studierende_sieht_nur_zugewiesene_module |
| MO-05 | Lektionsstruktur durch Mensch | umgesetzt | Demo Schritt 6 |
| MO-06 | umsortieren, archivieren | teilweise (anlegen, Reihenfolge; Archivieren Inkr. 4) | — |
| MO-07 | Lernziele mit Handlungsstufe | umgesetzt | test_abnahme_ablauf (indirekt über Lernprofil) |
| IN-01 | Upload Text und Markdown | umgesetzt (A-6) | Demo Schritt 7 |
| IN-02, IN-03 | Zuordnung zu Lektion | teilweise (Zuordnung bei Upload; nachträglich Inkr. 4) | — |
| IN-04, IN-10 | Abschnitte mit stabiler ID und Position | umgesetzt | test_kern :: test_abschnitte_lueckenlos_und_begrenzt, :: test_markdown_ueberschrift_beginnt_neuen_abschnitt |
| IN-05 | Versionen | umgesetzt | test_freigabe_und_versuch :: test_aenderung_freigegebener_unterlage_setzt_status_zurueck; test_zugriff_sitzung_rollen :: test_historischer_versuch_bleibt_lesbar_mit_altem_stand |
| IN-06 | fachliche Freigabe vor Wirkung | umgesetzt | test_mandant_und_rollen :: test_admin_gibt_nicht_frei, :: test_assistenz_darf_nicht_freigeben_ohne_delegation |
| IN-07 | Änderung: `in_pruefung`, abhängige Aufgaben gesperrt | umgesetzt | test_freigabe_und_versuch :: test_aufgaben_in_pruefung_sind_ausgeblendet_und_nicht_bearbeitbar; test_zugriff_sitzung_rollen :: test_aenderung_wirkt_auf_bestehende_uebung_und_hilfe |
| IN-08 | Freigabeformen | umgesetzt | test_freigabe_und_versuch :: test_freigabe_unter_auflage_braucht_verantwortliche_und_zukunftsfrist, :: test_nicht_freigebbar_verlangt_begruendung, :: test_neue_fassung_nach_ablehnung_kehrt_in_den_entwurf |
| IN-09 | Herkunft je Unterlage | umgesetzt (Felder) | — |
| LE-01, LE-02 | Lektion(en) wählen, üben | umgesetzt | test_abnahme_ablauf :: test_abnahme_durchgaengiger_browserablauf |
| LE-03 | Wiederholungsplan, deterministisch | umgesetzt (Planung; Übersicht Inkr. 2, A-12) | test_kern :: test_sm2_referenzwerte, :: test_sm2_falsch_setzt_zurueck_und_ease_untergrenze, :: test_sm2_intervall_obergrenze |
| LE-04 | Lernprofil mit Evidenzlage und Datum | umgesetzt | test_kern :: test_hilfe_zaehlt_nicht_als_selbststaendig, :: test_mehrere_richtige_auf_dieselbe_aufgabe_zaehlen_einmal, :: test_ausreichend_erst_ab_schwelle_und_widerspruch |
| LE-05 | Quelle je Aufgabe und Rückmeldung | umgesetzt | test_abnahme_ablauf; test_web_oberflaeche :: test_rueckmeldung_zeigt_quelle_und_bleibt_zugaenglich |
| LE-06 | Aufgaben nur aus freigegebenen, aktuellen Abschnitten | umgesetzt | test_freigabe_und_versuch :: test_aufgaben_in_pruefung_sind_ausgeblendet_und_nicht_bearbeitbar |
| LE-07 | Ebene B ohne Vorabfreigabe | umgesetzt (Anlage); Modellerzeugung Inkr. 2 | test_mandant_und_rollen :: test_delegierte_assistenz_darf_freigeben |
| LE-08, LE-10 | Meldung, Entscheid | Inkr. 2 | — |
| LE-09 | Ebene-C-Prüfung | Dienst vorhanden (`aufgabe_fachlich_pruefen`), Ansicht Inkr. 2 | — |
| LE-11 | Versuche bleiben unverändert | umgesetzt (Kopie je Versuch) | test_antwort_hilfe_abgabe; test_freigabe_und_versuch :: test_versuch_bleibt_unveraendert_wenn_aufgabe_spaeter_geaendert_wird |
| LE-12 | Hilfe am Versuch erkennbar | umgesetzt | test_antwort_hilfe_abgabe :: test_hinweis_erscheint_im_browser_und_ist_als_hilfe_vermerkt |
| PR-01 bis PR-03, PR-09 bis PR-12 | Testprüfungen, Prüfungsrahmen, Regler, Modi | Inkr. 3 | — (D-22) |
| PR-04 | Hilfen vermerkt, Hinweis wirksam | umgesetzt (Punkt 2) | test_antwort_hilfe_abgabe :: test_hinweis_wird_angezeigt_und_bleibt_nach_neuladen, :: test_hinweis_erscheint_im_browser…, :: test_wiederholung_nach_hilfe_bleibt_nicht_selbststaendig, :: test_neue_bearbeitung_nach_frueherer_loesung_ist_nicht_selbststaendig |
| PR-05 | Punkte im Maximum, Prozent konsistent | umgesetzt | test_kern :: test_single_choice_voll_oder_null, :: test_multiple_choice_teilpunkte_nie_negativ_nie_ueber_maximum, :: test_prozent_konsistent_und_null_maximum; test_freigabe_und_versuch :: test_richtige_antwort_mit_punkten_im_maximum |
| PR-06 | Versuch vollständig gespeichert | umgesetzt | test_antwort_hilfe_abgabe :: test_gleicher_schluessel_erzeugt_keinen_zweiten_versuch |
| PR-07 | Übungen mit Ebene B | umgesetzt | test_ablauf_durchgaengig |
| PR-08 | nicht auffüllen, ehrlich melden | umgesetzt | test_freigabe_und_versuch :: test_aufgaben_in_pruefung_sind_ausgeblendet_und_nicht_bearbeitbar |
| PR-13 | formativ, keine Note | umgesetzt (keine Notenfunktion) | — |
| Antwortformat (Punkt 1) | Liste gültiger Option-IDs, Text bei Lücke, verständliche Fehler | umgesetzt | test_antwort_hilfe_abgabe :: test_einzelauswahl_mit_mehrstelliger_id_wird_richtig_bewertet, :: test_einzelauswahl_als_text_wird_abgewiesen, :: test_unbekannte_option_wird_mit_namen_gemeldet, :: test_einzelauswahl_mit_zwei_optionen_und_leere_auswahl_werden_abgewiesen, :: test_ungueltige_datentypen_werden_abgewiesen, :: test_luecke_nimmt_nur_text, :: test_web_einzelauswahl_mit_mehrstelliger_id |
| BS-01 | Gespräch zum Ergebnis | umgesetzt | test_gespraech_und_modellausgabe :: test_mehrere_rueckfragen_hintereinander_und_verlauf_bleibt; test_abnahme_ablauf |
| BS-02 | Quellen-ID-Prüfung im Kern | umgesetzt | test_gespraech_und_modellausgabe :: test_quellen_sind_durchgaengig_belegbar_und_nicht_erfunden; test_lernbegleiter_und_modell :: test_fremde_quelle_wird_abgelehnt |
| BS-03 | Lernprofil im Kontext | umgesetzt (Lernstand im Auftrag) | test_gespraech_und_modellausgabe :: test_modellkontext_ist_begrenzt_und_personenfrei |
| BS-04 | Sicherheitsgrad und Annahmen | umgesetzt | test_lernbegleiter_und_modell :: test_erfolgreiche_antwort_trägt_quelle_und_fachlich_ungeprueft |
| BS-05 | Lücke benennen | umgesetzt | test_lernbegleiter_und_modell :: test_antwort_ohne_quelle_wird_als_unbelegt_benannt |
| BS-06 | formativ, keine Bewertungssprache | umgesetzt | test_gespraech_und_modellausgabe :: test_ungueltige_modellausgaben_werden_abgelehnt (Fall «Note 4») |
| BS-07 | Gespräche nur für Berechtigte | umgesetzt für Lernende; Lehrsicht Inkr. 2 | test_freigabe_und_versuch :: test_fremder_versuch_ist_nicht_sichtbar |
| BS-08 | Formen Hinweis, Rückfrage, Beispiel, Erklärung | umgesetzt (Auswahl) | test_web_oberflaeche; Demo |
| BS-10 | nächster Schritt | umgesetzt | test_ablauf_durchgaengig |
| Versuchssicht dauerhaft (Punkt 5) | gespeicherter Stand nach Neuladen und Neuanmeldung | umgesetzt | test_gespraech_und_modellausgabe :: test_versuch_und_gespraech_nach_neuer_anmeldung_unveraendert; test_abnahme_ablauf :: test_abnahme_durchgaengiger_browserablauf |
| Quellenansicht (Punkt 5) | Zitierstand, aktueller Status, Verwendbarkeit | umgesetzt | test_zugriff_sitzung_rollen :: test_abschnitt_zeigt_historischen_stand_und_aktuellen_status |
| Modellvalidierung (Punkt 6) | Typen, Pflichtfelder, Werte, Quellen | umgesetzt | test_gespraech_und_modellausgabe :: test_ungueltige_modellausgaben_werden_abgelehnt (13 Fälle), :: test_annahmen_42_fuehrt_zu_wiederholung… |
| AD-02 | Admin sieht Module und Konten | teilweise (Übersicht Inkr. 4) | Demo |
| AD-03 | aggregierte Lernprofile | umgesetzt (Zählung) | Demo Schritt 18 |
| AD-04 | Änderungen protokolliert | umgesetzt (Zuweisung mit Vorwert) | test_zugriff_sitzung_rollen :: test_genau_eine_modulrolle… |
| NF-01 | HTTPS, Cookie, CSRF | teilweise (HTTPS im Betrieb offen) | test_mandant_und_rollen :: test_schreibende_anfrage_ohne_csrf…, :: test_sitzungscookie_ist_httponly |
| NF-02 | Datenschutz | teilweise (Pseudonym im Kontext; Löschkonzept D-09 offen) | test_gespraech_und_modellausgabe :: test_modellkontext_ist_begrenzt_und_personenfrei |
| NF-03 | Barrierefreiheit | teilweise (Beschriftungen, Sprache; kein Scan) | test_web_oberflaeche :: test_anmeldeseite_ist_erreichbar_und_beschriftet |
| NF-04 | Nachweise | umgesetzt | test_ablauf_durchgaengig (Nachweis-Arten) |
| NF-05 | Deutsch, Schweizer Schreibweise | umgesetzt in Texten | — |
| NF-07 | Modellzugang nur über Adapter | umgesetzt (Vertrag); Dienst läuft, Anwendung nicht registriert (D-05) | test_lernbegleiter_und_modell :: Vertragstests; test_live_vorschaltdienst (siehe 4) |
| Punkt 4 | Gemeinsame Prüfungen, deaktivierte Konten/Organisationen | umgesetzt | test_zugriff_sitzung_rollen :: test_deaktiviertes_konto…, :: test_deaktivierte_organisation…, :: test_entzogene_modulrolle…, :: test_neue_erklaerung_wird_bei_gesperrter_quelle_nicht_erzeugt |
| NF-12 | keine Zugangsdaten im Repository | umgesetzt | Prüfung durch Review; Testpasswörter nur in Testdatenbanken |

**Nicht abgedeckt:** Die fachliche Qualität von Aufgaben und Rückmeldungen an einem Referenzsatz durch eine Lehrperson. Der synthetische Referenzsatz (`tests/fachlich/`) prüft nur die Konsistenz der Lösungsschlüssel.

---

## 3 · Abweichungsregister

| ID | Abweichung | Grund | Auswirkung | Behebung |
|---|---|---|---|---|
| **A-1** | Entwicklungsdatenbank SQLite statt PostgreSQL | lokaler Start ohne Serverinstallation | keine RLS-Durchsetzung im Entwicklungsbetrieb | Inkr. 5 |
| **A-2** | RLS nicht umgesetzt | Umfang Inkrement 1/1.1 | Schutz hängt an der Repository-Schicht; Tests prüfen das | Inkr. 5 |
| **A-3** | Aufgabenerzeugung durch Modell nicht im Inkrement | Ablauf ohne Modell prüfbar | keine automatische Erzeugung | Inkr. 2 |
| **A-4** | Rückmeldung zu Aufgaben deterministisch (Lösung + Begründung) | verlässlich, ohne Modell prüfbar | keine individuelle Formulierung über den hinterlegten Text hinaus | Inkr. 2 |
| **A-5** | Keine Anwendungsanbindung an den Vorschaltdienst | Anwendung `lernsoftware` ist dort nicht registriert; kein Anbieterschlüssel | 409- und 503-Verhalten nur gegen Testdouble geprüft | Registrierung nach Freigabe, dann Live-Test der Fehlerfälle |
| **A-6** | Nur `.txt` und `.md` | Umfang | keine PDF/DOCX/PPTX-Unterlagen | Inkr. 2 |
| **A-7** | Ebene C nur über Anlage durch Lehrperson; keine Prüfansicht | Umfang | Prüfstatus-Anzeige vollständig erst mit Inkr. 2 | Inkr. 2 |
| **A-8** | Aufgaben können nicht bearbeitet werden (nur anlegen und fachlich prüfen) | Versionierung der Aufgaben folgt in Inkr. 2 | Änderung nur durch neue Aufgabe | Inkr. 2 |
| **A-9** | Lernbegleiter ohne echtes Modell: Testadapter (Wortüberschneidung, SIMULIERT) | keine echte Modellprüfung vorhanden | Qualität der Rückfragen ist **nicht** bewertet | echter Modelllauf + Ground-Truth (Inkr. 2) |
| **A-10** | Browser-Oberfläche nur für Lernende; Verwaltung über Schnittstelle und Demo | Bedienungsnorm fehlt (D-10) | Verwaltung nicht per Oberfläche | Inkr. 2 (Dozentenoberfläche) |
| **A-11** | Argon2-Parameter in Tests reduziert | Testlaufzeit | Produktwerte in `config/basis.yaml`, nicht in Tests geprüft | ein Test mit Produktwerten vor Abnahme |
| **A-12** | Wiederholung nur berechnet und in der Antwort angezeigt | Umfang | keine Übersicht fälliger Aufgaben | Inkr. 2 |
| **A-13** | Sitzung als signiertes Cookie, nicht serverseitig widerrufbar; Ablauf 120 Minuten ab Anmeldung | Umfang | Abmeldung und Ablauf wirken am Client; ein kopiertes Cookie bleibt bis Ablauf gültig. Deaktivierung von Konto und Organisation wirkt sofort (Kontext wird je Anfrage geladen) | serverseitige Sitzungsliste (Inkr. 5) |
| **A-14** | Frühere Versuche erhalten nach einer neuen Quellenfassung keine neue Erklärung | strenge Regel: Erklärungen nur mit aktuellen Quellen (Punkt 4) | Historie bleibt lesbar; für Fragen zu einer geänderten Quelle ist eine neue Bearbeitung der Aufgabe nötig, die erst mit Inkr. 2 (A-8) komfortabel ist | Inkr. 2 |

Keine stille Abweichung: jede Abweichung steht hier und im Konformitätsnachweis (Dokument 02 §2).

---

## 4 · Testergebnisse Inkrement 1.1

**Protokoll:** `docs/nachweise/testprotokoll-20261110T142413Z.json` (RA-13: nicht überschreiben; Erzeugung nur mit `LERNSOFTWARE_PROTOKOLL=1`).

| Art | bestanden | nicht bestanden | nicht geprüft |
|---|---|---|---|
| technisch (Unit, Kontrakt, Ablauf, Web, Sicherheit) | 131 | 0 | 0 |
| fachlich_synthetisch (Referenzsatz, keine Lehrpersonen-Abnahme) | 4 | 0 | 0 |
| live (Vorschaltdienst) | 0 | 0 | **1** (übersprungen, `VORSCHALT_LIVE` nicht gesetzt) |
| **Summe** | **135** | **0** | **1** |

**Modellherkunft der Läufe:** alle mit Testadapter (SIMULIERT). **Kein Lauf mit einem echten Modell.** Die Live-Prüfung des Vorschaltdienstes (Health) ist mit `VORSCHALT_LIVE=1` bestanden, siehe 5.

**Befehle:**

```powershell
# Alle Tests (ohne Live-Prüfung)
.venv\Scripts\python.exe -m pytest

# Mit Protokoll-Datei
$env:LERNSOFTWARE_PROTOKOLL = "1"; .venv\Scripts\python.exe -m pytest
```

Der GitHub-Actions-Workflow `.github/workflows/tests.yml` führt denselben Lauf ohne Zugangsdaten und ohne Modellanbieter aus. Ich habe den Workflow nicht auf GitHub ausgeführt; das ist ein Prüfschritt nach dem Push.

---

## 5 · Vorschaltdienst (Stand 2026-11-10)

- Der Dienst (`C:\Projekte\Pseudonymisierung`, Modus `develop`, `127.0.0.1:8040`) war gestartet. Health: `bereit`, Version 0.0.1, Wortliste geladen, Stufe C inaktiv. Der Live-Health-Test ist bestanden.
- Vertrag ohne Anbieteraufruf: fehlende Kopfzeilen und unbekannte Anwendung → 400 `kontext_fehlt`.
- **Offen:** Die Anwendung `lernsoftware` ist im Dienst nicht registriert (ANBINDUNG.md, Schritt 1). Darum sind 409 und 503 von hier aus nicht prüfbar. Kein Anbieterschlüssel ist hinterlegt.
- Der Dienst ist ein eigenes Projekt. Dieses Repository steuert ihn nicht; sein Start und Stopp liegt beim Betreiber des Hosts.

---

## 6 · Startanleitung (lokal, Windows PowerShell)

Voraussetzungen: Python 3.13, Projektordner `C:\Projekte\Lernsoftware`.

```powershell
cd C:\Projekte\Lernsoftware
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**1. Frische Demo-Datenbank anlegen** (eine neue Datei je Lauf; die Zugangsdaten stehen auf der Konsole):

```powershell
.venv\Scripts\python.exe -m app.demo
```

Der Lauf schreibt den Zeiger `instance\aktuelle-demo.txt`, den `run.py` ohne weitere Angabe verwendet.

**2. Server starten** (laufenden Server vorher mit `Strg+C` beenden):

```powershell
.venv\Scripts\python.exe run.py
```

**3. Im Browser** `http://127.0.0.1:5050/anmelden` öffnen:

| Feld | Wert |
|---|---|
| Lernorganisation | `beispiel-hs` |
| Benutzername | `student` |
| Passwort | aus der Konsolenausgabe von Schritt 1 (`student`) |

Ablauf: Modul «Statistik-Grundlagen (Testkurs)» → Lektion wählen → Übung erzeugen → Hinweis anzeigen → Antwort abgeben → Rückmeldung und Quelle lesen → Rückfragen stellen → neu anmelden. Die Oberfläche zeigt oben den Modellmodus (SIMULIERT).

**Modellmodus wählen:** Standard ist `testadapter` (config/basis.yaml). Mit `$env:LERNSOFTWARE_MODELL = "vorschaltdienst"` vor dem Start wird der Vorschaltdienst verwendet (erst nach Schritt A-5). Ungültige Werte brechen den Start ab. Der wirksame Modus steht im Start-Log und unter `http://127.0.0.1:5050/healthz`.

**Wichtig:** Eine Datenbank aus einer früheren Version ist nicht kompatibel (neue Spalten). Nach einem Update immer Schritt 1 ausführen.

**Tests:**

```powershell
.venv\Scripts\python.exe -m pytest
```

---

## 7 · Verbleibende Einschränkungen

1. Kein Lauf mit einem echten Modell; alle Antworten sind simuliert (A-9). Die Qualität der Rückfragen ist nicht bewertet.
2. Keine fachliche Abnahme durch eine Lehrperson. Die Referenzaufgaben sind synthetisch.
3. Kein RLS, keine serverseitige Sitzungsliste (A-1, A-2, A-13).
4. Verwaltung nur über Schnittstelle und Demo (A-10).
5. Keine Bearbeitung von Aufgaben (A-8) und daher keine komfortable Neuerstellung nach Quellenänderung (A-14).

---

## 8 · Vorschlag Inkrement 2: reales Kursmodul

Ziel: Ein echter Kurs mit einfacher Dozentenoberfläche, echter Modellanbindung und automatischer Fragenerzeugung, mit klaren Freigaben.

1. **Dozentenoberfläche:** Module, Lektionen, Lernziele, Unterlagen (Upload, Ersatz), Freigabe, Aufgaben anlegen und bearbeiten (A-8), Ebene-C-Prüfung, Meldungen (LE-08, LE-10).
2. **Modellanbindung:** Registrierung der Anwendung im Vorschaltdienst (nach Freigabe), Anbieterschlüssel durch Betrieb, Live-Test der 409- und 503-Fälle, Entscheid D-07 vor echten Lernenden.
3. **Automatische Fragenerzeugung:** Ebene-B-Aufgaben aus freigegebenen Abschnitten, mit Kernprüfung der Quellen und Schema-Validierung (Dokument 03 §5.1), Begrenzung je Lektion.
4. **Formate:** PDF und DOCX (pypdf, python-docx), mit den Stolpersteinen aus ADR-L-004.
5. **Ground-Truth:** Testset mit echten, nicht personenbezogenen Unterlagen (D-16); Schwelle D-15 vor Modellfreigabe.
6. **Nachweise:** Modellaufruf mit echter Herkunft in Testprotokoll und Versuch.

Entscheidungen vorab: D-07 (Verarbeitungsort), D-09 (Aufbewahrung), D-16 (echte Musterunterlagen), D-15 (Schwelle).

---

## 9 · Fortschreibung

Jede Änderung an Anforderungen, Entscheidungen oder Abweichungen wird hier und im Änderungsprotokoll von Dokument 01 vermerkt. Ein Commit nennt die Kennungen, die er betrifft.
