# 01 · Anforderungen

**Projekt:** Lernsoftware (Arbeitsname, Festlegung D-01, siehe [06](06_Entscheidungen_und_offene_Punkte.md))
**Version:** 0.2 (bereinigt am 2026-11-10) · Vorgänger: 0.1
**Geltung:** dieses Repository · Normen: Referenzarchitektur v0.4 (`RA-…`, `NR-…`), Entwicklungsrichtlinien Basis, Testkonzept Zielarchitektur V0.1
**Status der Festlegungen:** Alle mit «vorläufig» markierten Aussagen sind Arbeitsregeln bis zur Bestätigung durch den Auftraggeber; sie sind so gebaut, dass sie ohne fachlichen Umbau änderbar sind.

---

## 1 · Zweck und Abgrenzung

Eine webbasierte Lernumgebung, in der Studierende die Unterlagen eines Moduls über Lektionen hinweg **lernen, repetieren und üben** können, Übungsaufgaben und (ab Inkrement 3) Testprüfungen mit wählbarer Schwierigkeit erhalten und ihre Antworten mit einem **quellenbezogenen Lernbegleiter** besprechen. Dozierende und zugewiesene Assistenz strukturieren die Unterlagen nach Lektionen und definieren Lernziele. Mehrere **Lernorganisationen** nutzen dieselbe Plattform mit strikt getrennten Daten.

**Das Werkzeug unterstützt:**
- Lernen und Üben mit formativer Rückmeldung (Übungspunkte, Hinweise, begründete Lernstandshinweise);
- Erklären, Begründen, Anwenden und Reflektieren anhand freigegebener Unterlagen;
- Wiederholung von Lerninhalten nach einem Wiederholungsplan;
- Testprüfungen als **Übungs- oder Prüfungssimulation** nach einem hinterlegten Prüfungsrahmen.

**Das Werkzeug tut nicht (Phase 1):**
- keine verbindlichen Noten und keine formalen Leistungsentscheide (Abschnitt 4, Festlegung «Formativ/Summativ»);
- keinen Ersatz für Lehrpersonen: Inhalte, Lernziele, Freigaben von Unterlagen und die Bewertung verbindlicher Leistungen bleiben bei Menschen (NR-01);
- keine Aussagen als gesicherter Kursinhalt, die nicht aus freigegebenen Unterlagen belegbar sind (NR-02).

## 2 · Begriffe

| Begriff | Bedeutung |
|---|---|
| **Lernorganisation** | Mandant (z. B. Hochschule, Schule, Firma). Strikt getrennt von allen anderen. |
| **Modul / Fach** | Lerneinheit innerhalb einer Lernorganisation mit Lektionen und Zuweisungen. |
| **Lektion** | Vom Dozierenden definierte Untergliederung eines Moduls mit Titel, Reihenfolge und Lernzielen. |
| **Lernziel** | Beschreibung einer nachweisbaren Fähigkeit. Hat eine Lernhandlungsstufe (Wiedergeben, Anwenden, Analysieren, Beurteilen/Transfer). |
| **Unterlage** | Hochgeladene Datei einer Lektion (Umfang Inkrement 1: Text und Markdown). |
| **Abschnitt** | Aus einer Unterlage gebildete, zitierfähige Textstelle mit Position. |
| **Aufgabe** | Eine einzelne Übungsfrage mit Lösungsschlüssel oder Bewertungsraster, Lernzielbezug und Quellen. |
| **Übung** | Zusammenstellung von Aufgaben aus gewählten Lektionen, im Lernmodus. |
| **Testprüfung** | Zusammenstellung von Aufgaben nach einem Prüfungsrahmen (Themengewichtung, Aufgabenformen, Punkte, Zeit, Hilfsmittel). |
| **Versuch** | Eine Bearbeitung einer Aufgabe durch eine Person, unveränderlich nach Abgabe. |
| **Hilfe** | Hinweis, Lösungsansatz oder Erklärung, die vor oder nach einer Antwort angezeigt wurde. Wird am Versuch vermerkt. |
| **Lernprofil** | Pro Person und Lernziel: Selbsteinschätzung, selbstständige Leistung, Leistung mit Hilfen, Evidenzlage (Abschnitt 6). |
| **Prüfstatus** | Zustand einer Aufgabe bezüglich Erzeugung und Prüfung (Abschnitt 4, D-04). |
| **Lernbegleiter** | Dialogfunktion zur Besprechung eines Versuchs mit Quellen und Lernprofil. |

## 3 · Rollen und Berechtigungen

| Rolle | Kurzbeschreibung |
|---|---|
| **Super-Admin** | Plattformbetrieb. Legt Lernorganisationen an und richtet deren erste Administration ein. Sieht Organisations- und Verwaltungsmetadaten, keine Inhalte (D-02). |
| **Administration** (je Lernorganisation) | Legt Module an, verwaltet Konten, weist Personen Modulen zu, pflegt Erscheinungsbild. |
| **Dozierende** | Gliedert Module in Lektionen, lädt Unterlagen hoch, gibt Unterlagen fachlich frei, prüft Aufgaben fachlich, sieht aggregierte Lernprofile und Meldungen des Moduls. |
| **Assistenz** | Lädt Unterlagen hoch, pflegt Lektionen und bereitet Lernaufgaben vor (D-03). Fachliche Freigabe nur bei ausdrücklicher Delegation (Berechtigung `freigabe_delegiert`). |
| **Studierende** | Lernt, übt, erstellt Testprüfungen im eigenen Modul, bespricht Versuche mit dem Lernbegleiter. |

**Berechtigungsregeln (vorläufig, D-03):**
- Alle Berechtigungen gelten **innerhalb einer Lernorganisation** und, für modulbezogene Rollen, **innerhalb eines zugewiesenen Moduls** (MO-03, MO-04).
- Die fachliche Freigabe ist eine **eigene Berechtigung** (`freigabe`). Standardmässig trägt sie die Rolle Dozierende. Die Administration kann sie einer zugewiesenen Assistenz ausdrücklich delegieren; die Delegation ist im Nachweis sichtbar.
- Die Rechte werden serverseitig an jedem Endpunkt geprüft (siehe Spezifikation §2).

## 4 · Prüfstatus, Freigaben und Formativität (D-04, vorläufig)

Drei Ebenen dürfen nie verwechselt werden. Jede Ausgabe zeigt die Ebene, auf der sie steht.

| Ebene | Bedeutung | Wer setzt sie | Kennzeichnung für Nutzende |
|---|---|---|---|
| **A · Ausgangsunterlage fachlich freigegeben** | Eine Unterlage ist von einer Lehrperson zur Verwendung freigegeben (IN-06, IN-08). | Dozierende (oder delegiert) | «Freigegebene Unterlage» |
| **B · Übungsaufgabe technisch geprüft** | Eine automatisch erzeugte Aufgabe hat die technische Prüfung bestanden (Quelle existiert und ist freigegeben, Lösungsschlüssel konsistent, Format, keine Dublette). | Kern (automatisch) | «KI-erzeugt, technisch geprüft. Nicht von einer Lehrperson geprüft.» |
| **C · Aufgabe fachlich geprüft** | Eine Lehrperson hat die Aufgabe und ihren Lösungsschlüssel ausdrücklich geprüft. | Dozierende (oder delegiert) | «Von Lehrperson geprüft (Name, Datum)» |

**Regeln:**
- Eine Ebene-B-Aufgabe darf **nie** als Ebene C erscheinen, auch nicht sprachlich vergleichbar.
- Übungen (Lernmodus) dürfen Ebene-B-Aufgaben unmittelbar verwenden (PR-07). Das ist das Produktziel «individuelle, sofortige Übung».
- **Testprüfungen mit Prüfungsrahmen** können festlegen, dass ausschliesslich Ebene-C-Aufgaben verwendet werden dürfen (PR-09). Ist zu wenig Ebene C vorhanden, wird das angezeigt, nicht aufgefüllt (PR-08).
- **Meldungen** (LE-08) setzen eine Aufgabe sofort aus der Auswahl (Zustand `gesperrt`, bis Dozierende entschieden haben). Die Entscheidung ist im Nachweis festgehalten (LE-10).
- **Formativ/Summativ:** Alles in Phase 1 ist formativ. Verbindliche Noten und formale Leistungsentscheide sind nicht im Umfang (Festlegung D-21, vorläufig).

## 5 · Funktionale Anforderungen

Kennungen werden nie umgewidmet. Zurückgezogene Anforderungen bleiben mit Vermerk stehen. Neue Anforderungen sind angehängt.
Der Status je Anforderung wird in [07 · Umsetzungsstand](07_Umsetzungsstand.md) geführt.

### 5.1 Plattform und Mandanten (PL)

| ID | Anforderung | Prio |
|---|---|---|
| PL-01 | Der Super-Admin erfasst, ändert und deaktiviert Lernorganisationen und richtet je Organisation eine erste Administration ein. | Muss |
| PL-02 | Der Super-Admin hat **keinen** Lesezugriff auf Unterlagen, Aufgaben, Versuche, Gespräche oder Lernprofile einer Lernorganisation. Er sieht nur Registrierungsdaten (Name, Kurzname, Status, Erstelldatum). Keine Auswertung, die Inhalte mehrerer Organisationen verknüpft (D-02, Befund B-01). | Muss |
| PL-03 | Jede Lernorganisation hat ein eigenes Erscheinungsbild (Farben, Logo), von ihrer Administration gepflegt. | Muss |
| PL-04 | Das Erscheinungsbild wird auf Kontrast (WCAG 2.2 AA, NF-03) maschinell geprüft; ein Verstoss blockiert die Speicherung. | Muss |
| PL-05 | Mandantentrennung ist strukturell: Jedes mandantenbezogene Objekt trägt seine Lernorganisation; jeder Datenzugriff verlangt einen Mandantenkontext (RA-08). | Muss |
| PL-06 | Für das Inkrement 1 wird das Erscheinungsbild **nicht** umgesetzt (Standardansicht); PL-03/PL-04 bleiben Muss für Inkrement 4. | Inkr. 4 |

### 5.2 Konten und Anmeldung (BE)

| ID | Anforderung | Prio |
|---|---|---|
| BE-01 | Anmeldung mit Benutzername und Passwort. Keine Selbstregistrierung; Konten legt die Administration an. | Muss |
| BE-02 | Passwörter werden mit Argon2id gehasht; Klartext wird nie gespeichert oder protokolliert. | Muss |
| BE-03 | Nach 5 Fehlversuchen wird das Konto 15 Minuten gesperrt; Sperre und Entsperrung sind protokolliert (Grenzwerte D-14). | Muss |
| BE-04 | Passwort-Zurücksetzung durch die Administration. Selbstservice ist Phase 2. | Muss / Phase 2 |
| BE-05 | Eine Person kann Rollen in mehreren Lernorganisationen haben; eine Sitzung gehört genau zu einer Lernorganisation. | Muss |
| BE-06 | Zwei-Faktor-Authentisierung: Phase 2. | Phase 2 |
| BE-07 | Serverseitige Sitzungen; Abmelden invalidiert die Sitzung. | Muss |

### 5.3 Module, Lektionen, Zuweisungen (MO)

| ID | Anforderung | Prio |
|---|---|---|
| MO-01 | Die Administration legt Module an (Bezeichnung, Beschreibung, Zeitraum). | Muss |
| MO-02 | Die Administration weist einem Modul Dozierende, Assistenz und Studierende zu; Zuweisungen können entfernt werden. Die Delegation der Freigabe ist Teil der Zuweisung (D-03). | Muss |
| MO-03 | Studierende sehen nur Module, denen sie zugewiesen sind. | Muss |
| MO-04 | Dozierende und Assistenz sehen nur Module, denen sie zugewiesen sind. | Muss |
| MO-05 | Die Lektionsstruktur (Titel, Reihenfolge, Lernziele) wird von Dozierenden oder Assistenz definiert, nicht vom System erzeugt. Das System darf eine Struktur nur vorschlagen, die ein Mensch übernimmt (NR-01). | Muss |
| MO-06 | Lektionen können umsortiert, umbenannt und archiviert werden; archivierte Lektionen bleiben für bestehende Versuche und Lernprofile erhalten. | Muss |
| MO-07 | Lernziele sind einer Lektion zugeordnet und tragen eine Lernhandlungsstufe. | Muss |

### 5.4 Unterlagen (IN)

| ID | Anforderung | Prio |
|---|---|---|
| IN-01 | Upload von Unterlagen. **Inkrement 1: Text (`.txt`) und Markdown (`.md`).** Weitere Formate (PDF, DOCX, PPTX) sind Inkrement 2. Maximale Grösse über Konfiguration. | Muss |
| IN-02 | Unterlagen können einer Lektion zugeordnet werden oder als Sammelupload ohne Lektion hochgeladen und später zugeordnet werden. | Muss |
| IN-03 | Zuordnungen sind nachträglich änderbar. | Muss |
| IN-04 | Nach dem Upload werden Abschnitte gebildet (Absatzgrenzen). Fehlschläge sind sichtbar mit Grund. | Muss |
| IN-05 | Jede Unterlage hat eine Version. Ein Ersatz erzeugt eine neue Version; alte Versionen bleiben nachvollziehbar. | Muss |
| IN-06 | Eine Unterlage wird für Studierende erst wirksam, wenn eine Lehrperson sie fachlich freigegeben hat (Ebene A, RA-05). | Muss |
| IN-07 | Ändert sich der Inhalt einer freigegebenen Unterlage, wird die Freigabe automatisch zurückgesetzt (NR-05). Aufgaben, die sich auf die Unterlage stützen, sind für Studierende ausgeblendet, bis erneut freigegeben (D-06). Versuche bleiben erhalten (LE-11). | Muss |
| IN-08 | Freigabeformen: **freigegeben** · **freigegeben unter Auflage** (mit Verantwortlicher und Frist) · **nicht freigebbar** (mit Begründung). | Muss |
| IN-09 | Herkunft je Unterlage und Abschnitt: Hochladende Person, Zeitpunkt, Version, Lektion. | Muss |
| IN-10 | Abschnitte haben eine stabile ID und eine Position (Absatz-Nummer) für die Zitierfähigkeit (LE-05, BS-02). | Muss |

### 5.5 Lernen und Üben (LE)

| ID | Anforderung | Prio |
|---|---|---|
| LE-01 | Studierende wählen **eine Lektion** und üben zu ihren Lernzielen. | Muss |
| LE-02 | Studierende wählen **mehrere oder alle Lektionen** eines Moduls. | Muss |
| LE-03 | Ein Wiederholungsplan schlägt Aufgaben zur Wiederholung vor. Die Planung ist deterministisch und von der Kompetenzeinschätzung getrennt (Abschnitt 6.3, D-13). | Muss |
| LE-04 | Das Lernprofil je Lernziel ist sichtbar, mit Datum der letzten Evidenz und Evidenzlage (Abschnitt 6.1). | Muss |
| LE-05 | Jede Aufgabe und jede Rückmeldung zeigt ihre Quelle (Unterlage, Version, Abschnitt). | Muss |
| LE-06 | Aufgaben entstehen nur aus Abschnitten freigegebener Unterlagen (NR-02). | Muss |
| LE-07 | **Erzeugung individueller Übungsaufgaben ist unmittelbar möglich.** Eine Vorabfreigabe jeder Aufgabe durch eine Lehrperson ist nicht vorgesehen (ersetzt Version 0.1; D-04). Die Aufgabe erhält Ebene B. | Muss |
| LE-08 | Studierende können eine Aufgabe melden (`fehlerhaft`, `unklar`, `nicht_aus_unterlagen`, `sonstiges`). Die Aufgabe wird sofort ausgesetzt; Dozierende entscheiden (LE-10). | Muss |
| LE-09 | Ebene C (fachlich geprüft) wird durch Dozierende über eine Prüfansicht vergeben. Sie ist optional für das Üben, Pflicht für Prüfungsrahmen nach PR-09. | Muss |
| LE-10 | Meldungen und ihre Entscheidung (`bestätigt, Aufgabe korrigiert`, `bestätigt, Aufgabe entfernt`, `abgewiesen, Begründung`) sind nachweisbar. | Muss |
| LE-11 | Ändert sich eine Aufgabe oder ihre Unterlage, bleiben alle bisherigen Versuche unverändert, mit Verweis auf die damalige Aufgabenversion (siehe Spezifikation §8). | Muss |
| LE-12 | Die Oberfläche macht deutlich, ob eine Aufgabe in einer Lektion mit Hilfe oder ohne Hilfe bearbeitet wurde (siehe PR-04). | Muss |

### 5.6 Testprüfungen und Prüfungsrahmen (PR)

| ID | Anforderung | Prio |
|---|---|---|
| PR-01 | Studierende erzeugen eine Testprüfung aus einer Auswahl von Lektionen. | Inkr. 3 |
| PR-02 | Schwierigkeit wird über einen Regler mit vier Stufen gewählt (einfach · mittel · schwer · sehr schwer). Die Stufen beschreiben **geforderte Lernhandlung, geschätzte Schwierigkeit, verfügbare Unterstützung und Antwortformat** getrennt (Spezifikation §5.4). | Inkr. 3 |
| PR-03 | Anzahl und Zeitlimit sind im Prüfungsrahmen festgelegt; Studierende wählen innerhalb der zulässigen Spanne. | Inkr. 3 |
| PR-04 | Im Lernmodus sind Hilfen erlaubt; jeder Versuch vermerkt, welche Hilfen vor der Antwort angezeigt wurden. Ein Versuch mit Hilfe zählt nicht als selbstständige Leistung (Abschnitt 6.1). | Muss (Inkr. 1) |
| PR-05 | Die Auswertung wird vom Code berechnet. Punkte sind auf die Maximalpunktzahl der Aufgabe begrenzt; Prozentwerte beziehen sich auf die Summe der Maximalpunkte und sind auf ganze Prozent gerundet. | Muss (Inkr. 1) |
| PR-06 | Jeder Versuch wird mit Zeitpunkt, Antwort, Aufgabenversion, Lösungsschlüssel-Version, Hilfen und Auswertung gespeichert. | Muss (Inkr. 1) |
| PR-07 | Übungen (Lernmodus) dürfen Ebene-B-Aufgaben unmittelbar verwenden. | Muss (Inkr. 1) |
| PR-08 | Reicht die Zahl passender Aufgaben nicht, wird das angezeigt; es wird nicht aufgefüllt. | Muss |
| PR-09 | Ein Prüfungsrahmen legt fest, ob nur Ebene-C-Aufgaben verwendet werden dürfen. | Muss (Inkr. 3) |
| PR-10 | Prüfungsrahmen legen Themengewichtung, Aufgabenformen, Punktevergabe, Zeit und Hilfsmittel fest. Abweichungen durch eine vom Studierenden gewählte Trainingsschwierigkeit sind sichtbar ausgewiesen. | Muss (Inkr. 3) |
| PR-11 | Modus **Prüfungssimulation**: Hinweise sind ausgeschaltet, Rückmeldung erfolgt zum im Rahmen vorgesehenen Zeitpunkt. Modus **Lernen**: Hinweise, unmittelbare Rückmeldung, Wiederholungen, Unterbrechung sind erlaubt. | Muss (Inkr. 3) |
| PR-12 | Ob eine Prüfung unterbrochen werden darf, legt der Prüfungsrahmen fest; es gibt keine pauschale Regel. | Muss (Inkr. 3) |
| PR-13 | Formativ: Prüfungssimulationen erzeugen Übungspunkte und Lernstandshinweise, **keine** Note. | Muss |

### 5.7 Auswertung, Rückmeldung und Lernbegleitung (BS)

| ID | Anforderung | Prio |
|---|---|---|
| BS-01 | Studierende können nach einem Versuch oder einer Übung ein Gespräch zum Ergebnis beginnen. | Muss (Inkr. 1) |
| BS-02 | Erklärungen stützen sich auf freigegebene Abschnitte und nennen ihre Quellen. Der Code prüft die Quellen-IDs gegen die übergebenen Abschnitte; unbekannte IDs führen zur Ablehnung der Antwort (NR-02). | Muss (Inkr. 1) |
| BS-03 | Erklärungen berücksichtigen das Lernprofil (Stärken, offene Lernziele, letzte Fehler), damit sie individuell sind. | Muss (Inkr. 1) |
| BS-04 | Jede Aussage mit Bewertungscharakter trägt einen Sicherheitsgrad (Abschnitt 6.4, RA-11). | Muss (Inkr. 1) |
| BS-05 | Fehlt eine belegte Grundlage, benennt der Lernbegleiter die Lücke, stellt eine gezielte Rückfrage und gibt kein unbelegtes Zusatzwissen als Kursinhalt aus. | Muss (Inkr. 1) |
| BS-06 | Der Lernbegleiter formuliert **formative** Rückmeldungen mit Begründung. Er vergibt keine Note und keine formale Leistungsentscheidung (NR-01). | Muss (Inkr. 1) |
| BS-07 | Gesprächsverläufe sind für die betroffene Person einsehbar. Lehrpersonen sehen sie nur mit Zustimmung der Studierenden. | Muss |
| BS-08 | Der Lernbegleiter wählt je nach Bedarf eine Form: **Hinweis**, **Beispiel**, **Rückfrage** oder **ausführliche Erklärung**. Die Form ist wählbar. | Muss (Inkr. 1) |
| BS-09 | Für geschlossene Aufgaben wertet der Code gegen den hinterlegten Lösungsschlüssel aus. Für offene Antworten gilt: Ein Bewertungsraster ist Pflicht; eine automatische Rückmeldung ist **KI-gestützt, formativ und nachvollziehbar begründet**, mit ausgewiesenen Grenzen (Spezifikation §7). Eine reine Stichwortsuche genügt nicht. | Muss (Inkr. 2) |
| BS-10 | Rückmeldungen zu falschen Antworten führen zu einem nächsten Lernschritt (Hinweis, verwandte Lektion, Wiederholung), nicht nur zur Feststellung des Fehlers. | Muss (Inkr. 1) |

### 5.8 Administration (AD)

| ID | Anforderung | Prio |
|---|---|---|
| AD-01 | Konten einzeln anlegen; Stapel-Import (CSV) ist Inkrement 4. | Soll |
| AD-02 | Die Administration sieht Module, Zuweisungen und Konten ihrer Lernorganisation. | Muss (Inkr. 1) |
| AD-03 | Die Administration sieht aggregierte Nutzungs- und Lernprofildaten, keine einzelnen Versuche ohne Zustimmung (BS-07). | Muss |
| AD-04 | Änderungen an Zuweisungen, Freigaben, Delegationen und Prüfstatus werden protokolliert (Wer, Wann, Was). | Muss (Inkr. 1) |

## 6 · Lernprofil, Wiederholung und Kompetenzeinschätzung (LE, Präzisierung)

Diese Festlegung ersetzt die widersprüchlichen Regeln aus Version 0.1 (`sicher`, `unsicher`, `beherrscht`).

- **Wiederholungsplanung** (LE-03) entscheidet, **wann** eine Aufgabe erneut erscheint. Sie ist eine austauschbare technische Funktion (aktuell SM-2, ADR-L-007).
- **Kompetenzeinschätzung** (LE-04) beschreibt, **wie sicher die Evidenz** für ein Lernziel ist. Sie ist eine eigene Funktion mit eigenen Regeln.
- Beide Funktionen teilen keine Felder. Eine Wiederholung ist keine Kompetenzaussage.

Das Lernprofil je Lernziel unterscheidet:

| Art | Bedeutung | Zählt als Evidenz? |
|---|---|---|
| **Selbsteinschätzung** | Die Person sagt, wie sicher sie sich fühlt. | Nein; ist Information für Gespräche und Erklärungen. |
| **Beobachtete selbstständige Leistung** | Richtige Antwort oder vollständige Lösung ohne Hilfe. | Ja. |
| **Leistung nach Hinweisen** | Richtige Antwort, nachdem Hilfen angezeigt wurden. | Teilweise: gesondert ausgewiesen, zählt nicht als selbstständig. |
| **Unzureichende Evidenz** | Noch keine oder zu wenige Leistungen. | — ausgewiesen als «noch nicht belegt». |

**Regel für «beherrscht» (vorläufig, D-13):** Ein Lernziel gilt erst als **belegt beherrscht**, wenn selbstständige Leistungen an **mindestens drei verschiedenen Aufgaben** dieses Lernziels vorliegen. Mehrere richtige Antworten auf dieselbe Aufgabe zählen nur einmal. Die Schwelle ist Konfiguration.

**Regel für Sicherheit (RA-11):** Die Oberfläche zeigt die Evidenzlage als Feld: `ausreichend belegt` · `teilweise belegt` · `noch nicht belegt`, jeweils mit Datum der letzten Evidenz. Diese Begriffe ersetzen «sicher» und «unsicher» als Lernzustände.

## 7 · Nicht-funktionale Anforderungen

| ID | Anforderung | Herkunft / Anmerkung |
|---|---|---|
| NF-01 | HTTPS für alle produktiven Zugriffe. Lokaler Betrieb läuft über `127.0.0.1` ohne TLS. Das Zertifikat für `lernen.kaspair.ch` ist in Erstellung. | Auftraggeber |
| NF-02 | Datenschutz nach revDSG (Schweiz): Datenminimierung, Zweckbindung, Löschkonzept (Fristen offen, D-09), Auskunft durch Export eigener Daten. Rechtliche Prüfung offen. | Annahme |
| NF-03 | Barrierefreiheit: Zielniveau WCAG 2.2 AA; Farbe nie einziges Signal; tastaturbedienbar (D-08 bestätigen). | Annahme |
| NF-04 | Nachweise: Prüfergebnisse, Freigaben, Modellaufrufe und Änderungen am Lernprofil erzeugen versionierte, unveränderliche Einträge (RA-13). | Referenzarchitektur |
| NF-05 | Deutsch, Schweizer Schreibweise («ss»). | Auftraggeber |
| NF-06 | Mandantentrennung ist durch Tests belegt (Testkonzept §4.1). | RA-08, NR-04 |
| NF-07 | Modellzugang nur über die Capability `ki_aufruf` mit vorgeschaltetem Vorschaltdienst (Pseudonymisierung). Kein Direktweg (RA-09, NR-03). | Referenzarchitektur |
| NF-08 | Promotion `develop → test → integration → main`, keine Stufe wird übersprungen. | Entwicklungsrichtlinien |
| NF-09 | Konfiguration vor Programmierung: Prüfungsrahmen, Lernprofil-Schwellen, Grenzwerte, Erscheinungsbild (RA-07). | Referenzarchitektur |
| NF-10 | Leistung: Seitenaufbau unter 1 s bei üblicher Last (Zielwert D-12). | Annahme |
| NF-11 | Verfügbarkeit: Zielwert offen (D-12). | offen |
| NF-12 | Keine Zugangsdaten und keine personenbezogenen Testdaten im Repository. | Projektregel |

## 8 · Andragogische Anforderungen

Die Anforderungen AG-01 bis AG-17 sind **projektinterne Kennungen**. Ihre Herkunft ist je Eintrag in [05 · Andragogik und SVEB](05_Andragogik_SVEB.md) ausgewiesen (geprüfte offizielle Quelle, allgemeine andragogische Grundsätze oder Produktentscheidung). Sie gelten als Anforderungen des Projekts, nicht als SVEB-Pflichten.

## 9 · Abnahmekriterien (Auszug)

Abnahme erfolgt, wenn:
1. alle Muss-Anforderungen des jeweiligen Inkrements im Testprotokoll als **bestanden** stehen (nicht «getestet»);
2. die Mandanten- und Berechtigungstests grün sind;
3. offene Muss-Befunde aus dem Konformitätsnachweis (07) nicht bestehen;
4. Abnahmen mit echtem Modell nur dort ausgewiesen werden, wo sie tatsächlich gelaufen sind.

## 10 · Änderungsprotokoll 0.1 → 0.2

| Kennung | Änderung | Grund |
|---|---|---|
| Abschnitt 1 | «keine Bewertung» ersetzt durch Abgrenzung formativ / summativ (D-21). | Auftrag: klare Abgrenzung statt pauschaler Verneinung. |
| Abschnitt 3 | Rollen-Tabelle und Berechtigungsregeln präzisiert; Freigabe als eigene Berechtigung. | D-02, D-03. |
| Abschnitt 4 (neu) | Drei Ebenen des Prüfstatus; Meldungen; Formativität. | D-04. |
| PL-02 | Präzisiert: nur Registrierungsdaten, keine verknüpfende Auswertung. | D-02, Befund B-01. |
| PL-06 (neu) | Erscheinungsbild auf Inkrement 4 verschoben. | Umsetzungsplan. |
| BE-02, BE-03, BE-07 | Argon2id, Sperre, Sitzungen präzisiert bzw. ergänzt. | Auftrag Anmeldung; D-14. |
| IN-01 | Inkrement 1 auf Text und Markdown begrenzt. | Auftrag: begrenzter Teilumfang. |
| IN-07 | Änderungsfolge: Aufgaben ausgeblendet statt Versuche verloren (siehe 06 D-06). | Versuche bleiben erhalten. |
| IN-10 (neu) | Stabile Abschnitt-IDs und Positionen. | Zitierfähigkeit. |
| LE-03, LE-04 | Getrennt von Kompetenzeinschätzung; Begriffe «sicher/unsicher» ersetzt. | Auftrag: Widersprüche bereinigen. |
| LE-07 | **Ersetzt:** Vorabfreigabe jeder Frage durch Ebene B. | D-04; Produktziel unmittelbare Übung. |
| LE-08 | Meldung setzt Aufgabe sofort aus. | D-04, Fehlerbehandlung. |
| LE-09 (neu) | Ebene-C-Prüfung durch Dozierende. | D-04. |
| LE-10 bis LE-12 (neu) | Meldungsentscheidung, Versionstreue, Hilfekennzeichnung. | Auftrag. |
| PR-01 bis PR-13 | Neu gegliedert: Prüfungsrahmen, Modi, Unterbrechung als Rahmenfrage, Punktelogik mit Maximum. | Auftrag Abschnitt Schwierigkeit und Auswertung. |
| BS-01 bis BS-08 | BS-06 präzisiert (formativ statt «keine Aussagen über Leistung»); BS-08 (Formen) und BS-09 (offene Antworten) neu; BS-10 neu. | Auftrag Lernbegleitung. |
| AG-01 bis AG-17 | Unverändert als Kennungen; Herkunft ausgewiesen (Dokument 05). | Auftrag. |
| NF-02, NF-04, NF-05, NF-07 | Unverändert im Kern, Verweise aktualisiert. | — |
| NF-12 (neu) | Keine Zugangsdaten im Repository. | Auftrag Git. |

## 11 · Glossar der Kennungen

| Präfix | Bedeutung |
|---|---|
| `PL`, `BE`, `MO`, `IN`, `LE`, `PR`, `BS`, `AD` | Funktionale Anforderungen nach Bereich |
| `NF` | Nicht-funktionale Anforderungen |
| `AG` | Andragogische Anforderungen (Dokument 05) |
| `RA-…`, `NR-…` | Referenzarchitektur der Suite |
| `D-…` | Projektentscheid oder offener Punkt (06) |
| `ADR-L…` | Architekturentscheid des Projekts (06) |
| `TC-…` | Testfall (04) |
| `B-…` | Befund an die Normen (06) |
