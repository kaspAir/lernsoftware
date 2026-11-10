# 06 · Entscheidungen, Annahmen und offene Punkte

**Version:** 0.2 (2026-11-10)

Jede Zeile trägt eine Kennung. Kennungen werden nie umgewidmet. Der Status ist eine von:
- **festgelegt** (Arbeitsregel für die Umsetzung, durch den Auftraggeber bestätigt oder ausdrücklich vorläufig);
- **vorläufig** (Arbeitsannahme, im Inkrement umgesetzt, aber vom Auftraggeber noch zu bestätigen);
- **offen** (Auftraggeber muss liefern oder entscheiden; betroffener Teil blockiert nur sich selbst).

---

## 1 · Projektentscheide

| ID | Thema | Status | Festlegung / Empfehlung | Auswirkung |
|---|---|---|---|---|
| D-01 | **Produktname** | vorläufig | Arbeitsname «Lernsoftware». Umbenennung ohne fachlichen oder technischen Umbau: Anzeigename aus Konfiguration (`basis.yaml: produkt.name`), Paketname und Datenbankname sind davon getrennt und tragen keinen Anzeigenamen. Die endgültige Namenswahl blockiert nichts. | Oberfläche liest Name aus Konfiguration |
| D-02 | **Super-Admin und Mandantentrennung** | vorläufig | Arbeitsregel gemäss Auftrag: Super-Admin legt Lernorganisationen an und richtet die Erstadministration ein; er sieht Registrierungsdaten (Name, Kurzname, Status, Erstelldatum). **Kein** Leserecht auf Unterlagen, Aufgaben, Versuche, Gespräche, Lernprofile. Konflikt mit RA-08: siehe B-01. | Plattformregister ist eigene Tabelle ohne Verknüpfung auf Inhalte |
| D-03 | **Assistenz** | vorläufig | Assistenz darf hochladen, Lektionen pflegen und Lernaufgaben vorbereiten (Modul). Fachliche Freigabe und Ebene-C-Prüfung sind **eigene Berechtigung** `freigabe`; Standard bei Dozierenden; Delegation an Assistenz durch Admin per Zuweisung `freigabe_delegiert` (Nachweis). | Rollenmodell, Spez. §2 |
| D-04 | **Freigabe von Übungsaufgaben** | vorläufig (Auftrag) | Unmittelbare Erzeugung von Übungsaufgaben ist Produktziel. Drei Ebenen: A Unterlage fachlich freigegeben; B Aufgabe technisch geprüft (automatisch); C Aufgabe fachlich geprüft (Lehrperson). Ebene B darf nie als C erscheinen. Prüfungsrahmen kann «nur C» verlangen. Meldungen setzen sofort aus; Entscheid durch Dozierende mit Nachweis. Konflikt mit Suite-Norm: keiner gefunden (RA-05 gilt für Unterlagen und Freigaben; die Ebene B ist keine Freigabe, sondern ein Prüfstatus). Begründung und Prüfung in Dok. 01 §4 und Spez. §5.3. | Prüfstatus, Sichtbarkeit |
| D-05 | **Vorschaltdienst (Pseudonymisierung)** | festgelegt; Dienst läuft (develop, 2026-11-10), Anwendung `lernsoftware` noch **nicht registriert** (siehe 07 §4) | Der Dienst `C:\Projekte\Pseudonymisierung` existiert, ist laut seinem README «gebaut und getestet, Erstinstallation auf dem Host läuft». Schnittstelle geprüft gegen `docs/API.md` und `docs/ANBINDUNG.md`. Prüfstand 2026-11-10: `GET http://127.0.0.1:8040/pseudo/v1/health` liefert Verbindungsabbruch (curl Exit 7); der Live-Test ist im Protokoll als **nicht bestanden** ausgewiesen (`docs/nachweise/`). Der Dienst wurde nicht gestartet, weil er einen Tresor-Schlüssel braucht und in sein eigenes Datenverzeichnis schreibt. Umsetzung: Adapter nach API.md; Tests gegen Testadapter; ein Live-Test wird nur ausgeführt, wenn der Dienst erreichbar ist, und als solcher im Protokoll ausgewiesen. | Modellzugang nur über Adapter; Live-Status im Testprotokoll |
| D-06 | **Änderung freigegebener Unterlage** | festgelegt | Unterlage → `in_pruefung`; abhängige Aufgaben für Studierende ausgeblendet, nicht gelöscht; Versuche bleiben erhalten (LE-11). Die Alternative «Aufgabe bleibt sichtbar» scheidet aus, weil RA-05/NR-05 den freigegebenen Zustand bei geändertem Inhalt verbieten. | Spez. §4.2, §5.3 |
| D-07 | **Modellanbieter und Verarbeitungsort** | offen | Der Vorschaltdienst spricht Anthropic und Voyage; das Dokument des Dienstes nennt «LLM- und Embedding-Dienste im Ausland». Für Lernende mit personenbezogenen Gesprächen ist der Verarbeitungsort rechtlich relevant (revDSG). **Empfehlung:** Vor produktiver Nutzung Auftragsbearbeitung und Verarbeitungsort klären. **Auswirkung:** Blockiert nur den Produktivbetrieb mit echten Lernenden, nicht die Entwicklung mit synthetischen Daten. | Produktivbetrieb |
| D-08 | **Barrierefreiheit** | vorläufig | WCAG 2.2 AA als Arbeitsziel. Rechtliche Vorgabe der Organisation offen. | Prüfaufwand |
| D-09 | **Datenschutz und Aufbewahrung** | offen | Vorschlag: Gespräche 12 Monate; Löschkonzept; Nachweise mit Personenbezug über Pseudonym; Rechtsgrundlage je Lernorganisation. **Rechtliche Prüfung nötig.** Blockiert Produktivbetrieb. | Spez. §14 |
| D-10 | **Bedienungsnorm und Styleguide** | offen | Die Oberflächennorm der Suite liegt nicht in der Ablage (Referenzarchitektur v0.4 verweist auf sie). Im Projekt `kennora` liegt ein Styleguide-PDF (`kennora_Styleguide.pdf`). Bis zur Bestätigung: neutrale, zugängliche Oberfläche ohne Markenübernahme. | Oberflächenentwurf vorläufig |
| D-11 | **Hosting, Portblock, Deployment** | offen | Ports der Suite: 8040–8043 sind für den Vorschaltdienst belegt. Für dieses Projekt ist kein Portblock festgelegt. Die Suite-Betriebsregel verlangt einen eigenen Block je Produkt. Deployment: Der Kaspair-Auftritt wird per FTP ausgeliefert; eine dynamische Anwendung braucht einen Laufzeitort (Container oder Dienst) hinter Reverse-Proxy. **Empfehlung:** Portblock 8050–8053 vorschlagen, Bestätigung ausstehend. | Kein Deployment |
| D-12 | **Leistungs- und Verfügbarkeitsziele** | offen | Vorschlag: Seitenaufbau < 1 s, Verfügbarkeit 99 % werktags. | Tests TC-NFT nicht bewertbar |
| D-13 | **Evidenzschwelle «ausreichend belegt»** | vorläufig | 3 verschiedene Aufgaben mit selbstständig richtiger Antwort (`evidenz.schwelle_aufgaben`). Wiederholungsplanung getrennt. | Spez. §6.2 |
| D-14 | **Fehlversuchsgrenze Anmeldung** | vorläufig | 5 Fehlversuche, 15 Minuten Sperre. | TC-LOG-02 |
| D-15 | **Schwelle Modell-Ground-Truth** | offen | Vorschlag: ≥ 90 % Lösungstreue vor Freigabe eines Modells. Festlegung vor der Modellauswahl. | Modellfreigabe [Inkr. 2] |
| D-16 | **Musterunterlagen** | offen | Für Ground-Truth und Demonstrationen werden echte, nicht personenbezogene Unterlagen benötigt. Im Inkrement 1 werden **synthetische Testunterlagen** verwendet (gekennzeichnet). | Realitätsnähe der Aussagen |
| D-17 | **SVEB-Quellen** | teilweise geschlossen | Fünf Modulbeschreibungen (ZA-DL, ZA-BE, FA-AMD, FA-VNM, FA-VM-OL) sind geprüft (Dok. 05 §1). **Lücken offen:** Wegleitung und Qualifikationsprofil; weitere Modulbeschreibungen (u. a. FA-AMB, FA-TVM, FA-VM); Kursunterlagen; Berufsbild und Qualitätsstandards; AKV. Auswirkung: Aussagen zu Begleitung in Gruppen und Transversalkompetenzen nicht belegt. | Dok. 05 |
| D-18 | **Einstiegs-Selbsteinschätzung** | vorläufig | Optional je Lernziel, zählt nicht als Evidenz (AG-02, Spez. §6.1). | — |
| D-19 | **Erste Lernorganisation** | offen | Pilotorganisation und Name der ersten Administration. Im Inkrement 1 werden fiktive Organisationen verwendet. | Pilot |
| D-20 | **Sprache** | festgelegt | Deutsch, Schweizer Schreibweise. | — |
| D-21 | **Formativ / summativ** | vorläufig (Auftrag) | Phase 1: formative Rückmeldungen, Übungspunkte, begründete Lernstandshinweise sind Teil des Produkts. Verbindliche Noten und formale Leistungsentscheide sind nicht im Umfang. Für geschlossene Aufgaben wertet der Code gegen einen hinterlegten Lösungsschlüssel; die fachliche Qualität des Schlüssels ist durch Ebene C zu prüfen. | Abgrenzung Produkt |
| D-22 | **Prüfungsrahmen und Schwierigkeitsregler: fehlende Vorlage** | offen | **Nicht vorhanden in den Projektunterlagen:** (a) der «bereits bereitgestellte Prüfungsrahmen» des Auftraggebers; (b) die «Idee zum Schwierigkeitsregler» mit Stufenbeschreibungen. Vorhanden und genutzt: nur die Stufenbezeichnungen einfach · mittel · schwer · sehr schwer. **Fehlende Angaben:** Themengewichtung, Aufgabenformen und Anteile, Punkteverteilung und Maximum, Zeitlimit, Hilfsmittel, Anzahl, Zuordnung Stufe → Dimensionen. Die Struktur ist definiert (Spez. §5.4, §9.2); die Inhalte bleiben leer. **Auswirkung:** blockiert nur Inkrement 3 (Prüfungssimulation), nicht Inkrement 1–2. | Inkr. 3 |
| D-23 | **Eigene Testunterlagen** | vorläufig | Synthetische Unterlage «Grundlagen Wahrscheinlichkeit (Testkurs)» im Repository unter `tests/daten/`, eindeutig als synthetisch gekennzeichnet. Keine Aussage über Eignung für reale Kurse möglich. | Tests |

## 2 · Architekturentscheide (ADR-L)

Jeder Entscheid nennt Kontext, Entscheidung und Folgen. Ein ersetzter Entscheid bleibt mit Verweis stehen.

### ADR-L-001 · Anwendungsstack
- **Entscheidung:** Python 3.13 (lokal verfügbar), Flask 3.x, SQLAlchemy 2.x, Jinja2-Templates, Gunicorn im Betrieb. Verwendet dieselbe Familie wie `kennora` und der Vorschaltdienst.
- **Status:** festgelegt (bestätigt durch die Prüfung der vorhandenen Projekte am 2026-11-10: Flask-basierte Produkte und Vorschaltdienst laufen in der Suite).

### ADR-L-002 · Datenbank
- **Entscheidung:** PostgreSQL 16 mit RLS ist Zielsystem (ADR-L-006). Lokale Entwicklung über Docker-Container. Für den Schnelleinstieg ohne Docker ist SQLite als Entwicklungsdatenbank vorgesehen; **Abweichung A-1** (siehe 07): ohne RLS, Mandantentrennung dort nur durch Code-Struktur und Tests.
- **Status:** festgelegt mit Abweichung A-1.

### ADR-L-003 · Oberfläche
- **Entscheidung:** Serverseitig gerenderte Seiten, minimales JavaScript.
- **Status:** festgelegt.

### ADR-L-004 · Textextraktion
- **Entscheidung:** Inkrement 1: nur `.txt` und `.md`. Inkrement 2: `pypdf`, `python-docx`, `python-pptx`. Keine Cloud-Extraktion. OCR nicht im Umfang.
- **Status:** festgelegt.

### ADR-L-005 · Modellzugang
- **Entscheidung:** Alle Modellaufrufe laufen über die Capability `ki_aufruf` (Katalog v0.1, Abschnitt 5.2) mit Adapter. Im Projekt gibt es genau eine Stelle mit Anbieterkontakt (`app/modell/adapter.py`); der Adapter spricht nur den Vorschaltdienst über seine Basis-URL an. **Kein** Browser-Spracherkennungsdienst (Ton an Browserhersteller, verboten nach NR-03).
- **Testadapter:** `app/modell/testadapter.py` liefert deterministische Antworten. Jede Antwort trägt `herkunft: "SIMULIERT"`. Testprotokolle weisen dies aus.
- **Status:** festgelegt; Live-Anbindung abhängig von D-05.

### ADR-L-006 · Mandantentrennung
- **Entscheidung:** Jedes mandantenbezogene Objekt trägt `lernorganisation_id`. Zielsystem: PostgreSQL Row-Level-Security mit Mandantenkontext je Verbindung. Im Inkrement 1: Zugriffe laufen über eine Repository-Schicht, die jede Abfrage an einen Mandantenkontext bindet (Code-Struktur); **kein** Abfrage-Helfer ohne Mandant. Tests prüfen das (Testkonzept §4.1).
- **Status:** festgelegt; RLS-Umsetzung ist Inkrement 2 (Abweichung A-2 in 07).

### ADR-L-007 · Wiederholungsplanung
- **Entscheidung:** SM-2-Variante (Spez. §6.3), austauschbar. Kompetenzeinschätzung ist davon getrennt (Spez. §6.1–6.2).
- **Status:** vorläufig (T3-Entscheidung, nicht SVEB-Pflicht).

### ADR-L-008 · Anmeldung
- **Entscheidung:** Benutzername und Passwort. Argon2id (Bibliothek `argon2-cffi`). Serverseitige Sitzungen. CSRF-Schutz. Sperre nach Fehlversuchen. Zwei-Faktor: Phase 2.
- **Status:** festgelegt.

## 3 · Befunde an die Normen

Befunde werden zurückgemeldet; die Normen werden nicht stillschweigend geändert (Entwicklungsrichtlinien §1).

| Nr. | Befund | Norm-Fundstelle | Konflikt / Lücke | Vorschlag | Status |
|---|---|---|---|---|---|
| **B-01** | **Super-Admin und RA-08** | RA v0.4 §3.8: «Prüfbar: Ein Zugriff ohne Mandantenbezug liefert ausschliesslich geteilte Bestände. Es gibt keine Abfrage, die zwei Mandanten zugleich sieht.» Und: «ein Zugriff quer über Mandantengrenzen existiert nicht als Weg, nicht als Berechtigung.» | Die Liste aller Lernorganisationen ist eine Abfrage, die mehrere Mandanten zugleich zeigt. Der Super-Admin braucht sie für die Verwaltung (PL-01). Der Wortlaut lässt keine Ausnahme zu. Verschärfend: Die Verankerung von RA-08 ist laut v0.4 §2.2 und §13 **ausstehend** (Manifestsatz zurückgestellt, bis Zustimmung und Widerruf geregelt sind). | **Auslegung im Projekt:** Die Mandanten-Registrierung ist selbst das Basisobjekt (Ebene «geteilte Basis» der RA-08-Drei-Ebenen). Die Abfrage liest nur Registrierungsfelder und keine mandantenbezogenen Tabellen; keine Auswertung verknüpft Inhalte. **Vorschlag an die Norm:** RA-08 um eine Ausnahme für Plattformregister ergänzen, die nur Registrierungsfelder umfasst; dazu den zurückgestellten Manifestsatz klären. Bis dahin ist RA-08 für Inhalte streng, für das Register als Auslegung markiert. | offen (Rückmeldung an Architektur) |
| B-02 | Berechtigungen innerhalb eines Mandanten sind in der Referenzarchitektur nicht geregelt (v0.4 §12). | RA v0.4 §12 | Lücke | Rollenmodell aus Dok. 01 §3 und Spez. §2 als Ergänzung für die Architektur vorschlagen. | offen |
| B-03 | Die Bedienungsnorm fehlt in der Ablage. | RA v0.4 §6, Richtlinien `module/oberflaeche.md` | Lücke | D-10 | offen |
| B-04 | Die Lernfunktion (Wiederholungsplanung, Evidenz) ist im Capability-Katalog nicht geführt. Die Ausführungsschicht ist in der Referenzarchitektur noch nicht gebaut (RA v0.4 §12). | Katalog v0.1 §6; RA v0.4 §12 | Lücke | Katalogantrag `lernfortschritt` als deterministische Funktion mit Konfiguration. | offen |
| B-05 | Das Testkonzept kennt keine Modell-Ground-Truth als eigene Testart mit Abnahmeschwelle, obwohl das Entwicklungsmodul `tests-und-nachweis` sie fordert. | Testkonzept V0.1 §2; Richtlinien `module/tests-und-nachweis.md` | Lücke | Ergänzung im Testkonzept; Umsetzung in Dok. 04 §6 vorläufig. | offen |
| B-06 | **Simulierte Modellantworten** sind im Testkonzept nicht als eigene Kategorie geführt. Die Trennung «Kontrakt gegen Mock» existiert, aber nicht «Demonstration mit simuliertem Modell». | Testkonzept V0.1 §4 (Kontrakttest) | Lücke | Im Protokoll Feld `modell.herkunft` mit `SIMULIERT` oder `echt`; Dok. 04 §8. | vorläufig umgesetzt |
| B-07 | Die Ebene «Ausgangsunterlage freigegeben» ist RA-05 zuzuordnen; die Ebene «Aufgabe technisch geprüft» ist keine Freigabe. Die Norm kennt nur eine Freigabeform mit drei Ausprägungen. | RA v0.4 §3.5 | Unklarheit, ob ein Prüfstatus unterhalb der Freigabe ein Freigabeobjekt ist. | Vorschlag: Prüfstatus als eigene Stufe ohne Freigabewirkung, Tor bleibt bei der Lehrperson. | offen |

## 4 · Nicht-Ziele (Phase 1)

- Notenverwaltung, verbindliche Leistungsnachweise;
- Anbindung an Lernmanagementsysteme oder Hochschulverwaltung;
- Selbstregistrierung, Single-Sign-On;
- native Mobile-Apps (Oberfläche responsiv);
- Mehrsprachigkeit;
- OCR;
- Sprachein- und -ausgabe (ADR-L-005);
- Offline-Betrieb;
- Video- und Audioinhalte.

## 5 · Nächste Schritte

1. Auftraggeber bestätigt D-01 bis D-04 (oder korrigiert).
2. Klärung D-05 (Vorschaltdienst läuft auf dem Host?), D-07 (Verarbeitungsort), D-11 (Portblock).
3. Lieferung D-16 (echte Musterunterlagen), D-17 (weitere SVEB-Dokumente), D-22 (Prüfungsrahmen und Regler-Idee).
4. Befund B-01 an die Architektur zur Klärung geben.
