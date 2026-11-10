# 05 · Andragogik und SVEB

**Version:** 0.2 (2026-11-10) · Vorgänger: 0.1 (ersetzt; die dort genannten Grundlagen waren nicht geprüft)
**Bezug:** [01 · Anforderungen](01_Anforderungen.md) §8 · [04 · Testkonzept](04_Testkonzept.md) §4.11

Dieses Dokument trennt drei Ebenen ausdrücklich:

1. **Tier 1 · Aussagen aus geprüften offiziellen SVEB-Unterlagen.** Nur hier stehen Aussagen mit Quelle, Fassung und Fundstelle.
2. **Tier 2 · Allgemeine andragogische Grundsätze und persönliche didaktische Leitlinien.** Sie sind keine SVEB-Aussagen. Die Leitlinien stammen vom Auftraggeber.
3. **Tier 3 · Produktentscheidungen.** Unsere Ableitungen aus Tier 1 und Tier 2. Sie sind keine SVEB-Pflichten.

> **Keine Zertifizierung.** Die Software ist nicht vom SVEB anerkannt oder zertifiziert. Die geprüften Dokumente sind eine Grundlage für die didaktische Ausrichtung. Sie werden nicht als Zertifizierungsnachweis verwendet.

---

## 1 · Geprüfte Quellen (Tier 1)

Die Dokumente wurden am 2026-11-10 über die angegebenen URLs abgerufen. Die automatische Zusammenfassung des Abrufwerkzeugs war nicht verwertbar, weil die PDF-Textströme komprimiert vorlagen. Der Text wurde deshalb lokal mit `pypdf` extrahiert und **vollständig gelesen**. Sämtliche Fundstellen beziehen sich auf den extrahierten Text. Die Seitenzahlen sind die Seitenzahlen des PDF.

| Kürzel | Titel | Fassung | Umfang | URL |
|---|---|---|---|---|
| **ZA-DL** | SVEB-Zertifikat Ausbilderin/Ausbilder – Durchführung von Lernveranstaltungen · Modulbeschreibung AdA ZA-DL, Lernveranstaltungen mit Gruppen von Erwachsenen durchführen | Dokumentkopf «11.05.2023» | 7 S. | https://alice.ch/app/uploads/2023/06/SVEB-ZA-DL.pdf |
| **ZA-BE** | SVEB-Zertifikat Ausbilderin/Ausbilder – Einzelbegleitungen · Modulbeschreibung AdA ZA-BE, Lernbegleitungen mit erwachsenen Einzelpersonen durchführen | Dokumentkopf «11.05.2023» | 8 S. | https://alice.ch/app/uploads/2022/11/SVEB_ZA-BE-1.pdf |
| **FA-AMD** | Modulbeschreibung AdA FA-AMD, Aufbaumodul Didaktik: Lernveranstaltungen für Erwachsene didaktisch konzipieren und gestalten | Dokumentkopf «11.05.2023» | 7 S. | https://alice.ch/app/uploads/2023/05/FA-AMD.pdf |
| **FA-VNM** | Modulbeschreibung AdA FA-VNM, Vernetzungsmodul: Lerntransfer gestalten und ermöglichen | Dokumentkopf «11.05.2023» | 6 S. | https://alice.ch/app/uploads/2023/05/FA-VNM.pdf |
| **FA-VM-OL** | Modulbeschreibung AdA FA-VM-OL, Vertiefungsmodul: Online-Lernangebote didaktisch konzipieren und gestalten | Dokumentkopf «11.05.2023» | 6 S. | https://alice.ch/app/uploads/2023/05/FA-VM-OL.pdf |

**Einordnung der Dokumente (laut ZA-DL S.1–2):** Modulbeschreibungen des SVEB-Zertifikats Ausbilderin/Ausbilder und der Berufsprüfung Ausbilderin/Ausbilder. Sie beschreiben **Kompetenzen von Ausbildenden** (Lehrpersonen), nicht Anforderungen an Software. Die Modulbeschreibungen dienen laut ZA-DL S.6 als Grundlage für das Anerkennungsverfahren der Modulanbieter. Die Kompetenzcodes (A1 bis I9) stammen aus dem Qualifikationsprofil.

**Versionsangabe:** Die Dokumente tragen keine separate Versionsnummer. Als Fassung gilt das Datum im Dokumentkopf (11.05.2023). Die Metadaten der PDF-Dateien nennen abweichende Erstellungsdaten (Mai/Juni 2023); sie werden nicht als Fassung verwendet.

### 1.1 Fundstellen (Tier 1)

**Kompetenzen von Ausbildenden, die für die Plattform relevant sind:**

| Fundstelle | Kompetenz (Originaltext, gekürzt) | Modul |
|---|---|---|
| ZA-DL S.3, Kompetenz entwickelt und nachgewiesen | A2: Lehr- und Lerneinheiten lernprozessorientiert in einer Feinplanung konstruieren und dokumentieren | ZA-DL |
| ZA-DL S.3 | A3: Operationalisierte Lernziele aus vorgegebenen Kompetenzen formulieren | ZA-DL |
| ZA-DL S.3 | A5: Kompetenz- und lernzielorientierte Lernaufgaben entwickeln | ZA-DL |
| ZA-DL S.3 | B1: Verschiedene Lehr- und Lernformen lernprozess- und zielorientiert einsetzen | ZA-DL |
| ZA-DL S.3 | B2: Arbeitsprozesse und Lernschritte anleiten | ZA-DL |
| ZA-DL S.3 | B4: Feinplanung adaptiv und prozessorientiert umsetzen | ZA-DL |
| ZA-DL S.3 | B5: Lernergebnisse im Lernprozess kollektiv sichern | ZA-DL |
| ZA-DL S.3 | B6: Lernleistung und Verhalten beurteilen sowie bewerten | ZA-DL |
| ZA-DL S.3 | E1: Teilnehmenden Rückmeldungen zu Kompetenzen und Lernfortschritten geben | ZA-DL |
| ZA-DL S.3 | E3: Begleitprozesse unter Berücksichtigung der Selbstorganisation und Selbstwirksamkeit gestalten | ZA-DL (teils), ZA-BE |
| ZA-DL S.3 | B7: Geeignete Methoden und Verfahren zum Transfer und zur Überprüfung der Lernergebnisse einsetzen | ZA-DL (teils) |
| ZA-DL S.3 | C1: Vollständige Feedbackprozesse mit geeigneten Instrumenten durchführen | ZA-DL (teils) |
| ZA-BE S.3 | E4: Unterstützende Gespräche mit einzelnen Teilnehmenden im Bewusstsein der eigenen Haltung und Rolle führen | ZA-BE |
| ZA-BE S.3 | E5: Lernverhalten wahrnehmen, Lernschwierigkeiten und Ressourcen der Teilnehmenden erkennen und sie in ihrer Entwicklung unterstützen | ZA-BE (teils) |
| ZA-BE S.3 | E6: Methoden zur Lernbegleitung begründet wählen | ZA-BE (teils) |
| ZA-DL S.3 / ZA-BE S.3 | E2: Aus Kompetenzen abgeleitete Lernziele bestimmen und deren Erreichung überprüfen (gemeinsam mit Teilnehmenden möglich) | AMB (Pflicht) |
| ZA-DL S.4 | H2: Das eigene Lehr-/Lernverständnis … reflektieren | AMB, AMD, VNM |
| FA-AMD S.3 | G1: Bildungsbedarf sowie Interessen und Voraussetzungen der Adressatinnen und Adressaten abklären | FA-AMD |
| FA-AMD S.3 | G3: Didaktisches Design für eine vorbestimmte Ausbildungseinheit entwickeln | FA-AMD |
| FA-AMD S.3 | G4: Die Überprüfung der Erreichung von Kompetenzen konzipieren | FA-AMD |
| FA-AMD S.3 | A7: Valide Prüfungsverfahren planen | FA-AMD |
| FA-AMD S.3 | B10: Handlungsorientierte Methoden in komplexen Lehr-/Lernsituationen einsetzen | FA-AMD |
| FA-AMD S.4 (Mögliche Inhalte) | «Ebenen und Verfahren zur Überprüfung von Lernergebnissen»; «Prüfungsverfahren: Aufgabetypen, Beurteilungsinstrumente und Bezugsnormen» | FA-AMD |
| FA-VNM S.3 | A6: Transfer mit geeigneten Konzeptionen und Methoden planen | VNM |
| FA-VNM S.3 | G5: Für eine Ausbildungseinheit ein Transferkonzept entwickeln | VNM (teils) |
| FA-VNM S.3 | G6: Lehr-/Lernveranstaltungen subjekt- und biographieorientiert konzipieren | VNM (teils) |
| FA-VNM S.4 (Vorgaben) | Im Projekt steht «die eigene Lernentwicklung» und der Transfer ins Berufsfeld im Zentrum; ein Schwerpunkt der Reflexion bildet «der eigene Lerngewinn» | VNM |
| FA-VM-OL S.3 | A9: Blended-Learning-Settings planen; G3: didaktisches Design entwickeln | FA-VM-OL |
| FA-VM-OL S.3–4 (Mögliche Inhalte) | «Synchrone und asynchrone, begleitete und angeleitete Selbstlernzeiten»; «Angepasste Methoden zur Aktivierung der Teilnehmenden in digitalen Lernsettings»; «Auswahl und Gestaltung von einfachen technologiebasierten Medien» | FA-VM-OL |

**Beurteilung und Transparenz (Tier 1, Vorgaben für den Kompetenznachweis):**

| Fundstelle | Aussage | Bedeutung für uns |
|---|---|---|
| ZA-DL S.5 | «Die konkreten Beurteilungskriterien mit entsprechenden, beobachtbaren Indikatoren … werden … allen Beteiligten bei der Auftragserteilung … transparent gemacht.» | Bewertungsraster und Lösungsschlüssel werden Lernenden zugänglich gemacht (PR-04, BS-09). |
| ZA-DL S.6 | Beurteilungskriterien: Lernsituation ist auf eine geforderte Kompetenz oder gesetzte Lernziele ausgerichtet; Selbsteinschätzung und Reflexion sind nachvollziehbar; aus Planung, Durchführung und Feedback gezogene Schlüsse sind folgerichtig. | Spiegelt sich im Ablauf Lernziel → Aufgabe → Rückmeldung → nächster Schritt (BS-10). |
| ZA-DL S.6 | «Die Beurteilung des Kompetenznachweises erfolgt schriftlich … und ist für Aussenstehende nachvollziehbar begründet.» | Begründung jeder Rückmeldung (BS-06, BS-02). |
| ZA-DL S.7 | Lernjournal oder Kompetenzportfolio zum Nachweis der Reflexion; die Reflexion wird «nicht qualifiziert; ein Feedback ist fakultativ». | Reflexion kann Teil des Lernablaufs sein, wird aber nicht bewertet. |
| ZA-BE S.6 | Zur Durchführung gehört eine Reflexion der Ausbildungssequenz oder Lernbegleitung. | Reflexionsfragen nach Versuchen und Übungen (BS-01, Anwendungsfall). |
| ZA-BE S.6 | «Als Erwachsene gelten Teilnehmende ab der Sekundarstufe II beziehungsweise ab 16 Jahren.» | Zielgruppe für die Plattform (Begründung im Dokument 01). |
| FA-VNM S.4 | Die Reflexion bezieht Rückmeldungen aus dem Kolloquium und den eigenen Lerngewinn ein. | Rückmeldungen sollen in die Reflexion eingebettet sein, nicht isoliert stehen. |
| FA-AMD S.7 | Rückmeldungen der beobachtenden Person werden «mit der eigenen Wahrnehmung verglichen und reflektiert». | Gegenüberstellung Selbsteinschätzung und Ergebnis im Lernprofil (LE-04). |

**Lernzeit und Rahmen** (ZA-DL S.5, ZA-BE S.5): Kontaktlernzeit, Selbstlernzeit und Praxis sind dort Ausbildungsmerkmale. Sie sind für die Software nicht Anforderung, werden aber als Hinweis zu Selbststeuerung (AG-01) gewertet.

### 1.2 Lücken in den geprüften Grundlagen

| Lücke | Auswirkung |
|---|---|
| **Wegleitung zur Prüfungsordnung Berufsprüfung** mit dem **Qualifikationsprofil** (im Anhang) liegt nicht vor. Die Kompetenzen wurden nur über die Modulbeschreibungen erfasst. | Die Kompetenzlisten sind vollständig für die fünf geprüften Module, nicht für das gesamte Berufsbild. |
| **Weitere Modulbeschreibungen** (FA-AMB, FA-TVM, FA-VM, ZA-… weitere) sind nicht geprüft. | Aussagen zu Begleitung in Gruppen (AMB) und zu Transversalkompetenzen (TVM) fehlen. |
| **Kursunterlagen und Lehrmittel** des SVEB liegen nicht vor. | Keine Aussagen zu konkreten Methoden oder Lernspielen. |
| **Anerkennungsverfahren AKV** (Anbieterseite) ist nicht geprüft. | Keine Aussagen dazu, ob ein Werkzeug als Teil eines Modulangebots verwendbar ist. |
| **SVEB-Berufsbild und Qualitätsstandards** (eigenständige Dokumente) liegen nicht vor. | Die Grundsätze der Erwachsenenbildung in Tier 2 sind nicht daraus belegt. |

Diese Lücken sind in [06 · D-17](06_Entscheidungen_und_offene_Punkte.md) als offen geführt. Die Arbeit mit den vorhandenen Grundlagen geht weiter.

---

## 2 · Allgemeine andragogische Grundsätze und didaktische Leitlinien (Tier 2)

### 2.1 Allgemeine Grundsätze (ohne SVEB-Zitat)

- Erwachsene bringen Vorwissen, Erfahrungen, eigene Ziele und unterschiedliche Voraussetzungen mit.
- Erwachsene lernen wirksam, wenn sie ihren Lernweg mitbestimmen können.
- Lernen braucht verständliche Orientierung über Ziel, Stand und nächsten Schritt.

### 2.2 Didaktische Leitlinien des Auftraggebers

1. Lernziele, Lernaufgaben, Beurteilungskriterien und Rückmeldungen müssen zusammenpassen.
2. Lernende sollen ihren Lernweg mitbestimmen und verständliche Orientierung erhalten.
3. Die Plattform soll Erklären, Begründen, Anwenden und Reflektieren unterstützen.
4. Fehler sollen zu hilfreichem Feedback und geeigneten nächsten Lernschritten führen.
5. Der Lernbegleiter bietet je nach Bedarf Hinweise, Beispiele, Rückfragen oder ausführliche Erklärungen an.
6. Anwendung und Transfer in Studien- oder Berufssituationen sind vorgesehen.
7. Didaktische Modelle sind begründet und situationsgerecht einzusetzen.

**Leitgedanke des Auftraggebers:** Struktur, eigene Erfahrung, Reflexion und Transfer verbinden. **Das ist kein obligatorischer Ablauf für jede einzelne Frage.** Das Produkt bietet die Verbindung als Angebot, nicht als Zwang.

### 2.3 Abgrenzung

Tier 2 belegt keine SVEB-Anforderung. Eine Aussage aus Tier 2 wird im Produkt nie als «SVEB-konform» bezeichnet.

---

## 3 · Produktentscheidungen (Tier 3) und Herkunft

Jede Anforderung nennt ihre Herkunft: **T1** (Fundstelle Tier 1), **T2** (Tier 2), **T3** (Produktentscheidung, ohne eigene Quelle außer der angegebenen Begründung).

| ID | Anforderung (projektintern) | Herkunft | Umsetzung | Prüfung |
|---|---|---|---|---|
| AG-01 | Selbststeuerung: Lernende wählen Lektion, Umfang, Schwierigkeit und Zeitpunkt. | T1 (ZA-BE S.3, E3; VM-OL S.3 «begleitete und angeleitete Selbstlernzeiten») + T2 (1) | Lektionswahl, Übungsumfang, Regler (Inkr. 3) | TC-AG-01 |
| AG-02 | Vorwissen einbeziehen. | T2 (Grundsatz 2.1) + T1 (ZA-BE E5 «Ressourcen erkennen») | optionale Selbsteinschätzung je Lernziel; geht als Selbsteinschätzung (nicht Evidenz) in das Lernprofil | TC-AG-02 |
| AG-03 | Lebensweltbezug und Anwendung. | T2 (6) + T1 (VNM A6, G6) | Aufgabentyp «Anwendungsfall» mit Fallbeschreibung aus Unterlage; Fundstelle im Fall | TC-AG-03 |
| AG-04 | Transparente Lernziele und Zusammenpassen mit Beurteilung. | T1 (ZA-DL A3, E2; ZA-DL S.5 Transparenz) + T2 (1) | Lernziele sichtbar je Lektion; Aufgaben tragen Lernzielbezug (LE-05, MO-07); Bewertungsschlüssel einsehbar (PR-04) | TC-AG-04 |
| AG-05 | Kompetenzorientierung: Aufgaben fordern mehr als Wiedergabe. | T1 (ZA-DL A5; FA-AMD «Aufgabentypen») | Lernhandlungsstufe je Lernziel; Aufgaben tragen Stufe. Regler in Inkr. 3 (Spez. §5.4) | TC-AG-05 |
| AG-06 | Unmittelbare, konstruktive Rückmeldung. | T1 (ZA-DL E1, C1) + T2 (4) | Rückmeldung unmittelbar nach Antwort, mit Quelle und nächstem Schritt (BS-10) | TC-AG-06 |
| AG-07 | Fehler als Lernanlass. | T2 (4) + T3 | Keine Punktabzüge ausser Teilpunkte bei Mehrfachauswahl (PR-05); neutrale Sprache; Rückmeldung mit nächstem Schritt | TC-AG-07 |
| AG-08 | Individualisierung nach Lernprofil. | T1 (ZA-BE E5; ZA-DL B4 «adaptiv») + T2 (1) | Erklärungen und Vorschläge nutzen Lernprofil (BS-03, LE-03) | TC-AG-08 |
| AG-09 | Denken anregen statt Lösung nennen. | T1 (ZA-BE E4, E6) + T2 (5) | Lernbegleiter-Form «Rückfrage» vor «Lösung» wählbar (BS-08) | TC-AG-09 |
| AG-10 | Motivation und Selbstwirksamkeit ohne Druck. | T1 (ZA-DL E3 «Selbstwirksamkeit») + T3 | sachliche Evidenzanzeige; keine Rangliste, keine Serien-Mechanik | TC-AG-10 |
| AG-11 | Partizipation und Rückkopplung. | T1 (ZA-DL S.5 Beteiligte; E2) + T3 | Meldungen (LE-08) mit Entscheidungsnachweis (LE-10); Modul-Feedback Phase 2 | TC-AG-11 |
| AG-12 | Grenzen und Lernberatung. | T1 (ZA-BE E4) + T3 | Fragen ausserhalb der Unterlagen → Lücke benennen (BS-05); Weiterleitung an Lehrperson | TC-AG-12 |
| AG-13 | Verständlichkeit und Zugänglichkeit. | T2 + T3 (NF-03) | WCAG 2.2 AA; einfache Sprache | TC-A11Y-01…04 |
| AG-14 | Transparenz über Herkunft und Unsicherheit. | T2 (3, Orientierung) + T3 (RA-10, RA-11) | Quelle und Evidenzlage je Aussage (BS-02, BS-04, Abschnitt 6 Dok. 01) | TC-BEG-01, -06 |
| AG-15 | Flexibilität im Ablauf. | T1 (VM-OL S.3 Selbstlernzeiten) + T3 | Unterbrechung ist Prüfungsrahmen-Regel (PR-12), nicht pauschal | TC-AG-15 |
| AG-16 | Lehrperson bleibt verantwortlich. | T1 (ZA-DL B6 «Lernleistung … bewerten»; ZA-DL S.6 Beurteilung durch Moduldozent) + T3 (NR-01) | Keine Note im Produkt; fachliche Freigabe und Ebene C durch Lehrpersonen | TC-MOD-04, TC-BEG-03, TC-PRF-05 |
| AG-17 | Datenschutz und Vertrauen. | T3 (NF-02, BS-07) | Gespräche einsehbar für Lernende; Lehrpersonen nur mit Zustimmung | TC-BEG-04, TC-BEG-08 |
| AG-18 | Erklären, Begründen, Anwenden und Reflektieren unterstützen. | T2 (3) + T1 (VNM S.4 Reflexion; ZA-BE S.6 Reflexion) | Übungstypen mit Begründung; Reflexionsfrage nach Versuch (optional, nicht bewertet) | TC-AG-18 |
| AG-19 | Struktur, Erfahrung, Reflexion und Transfer verbinden, **ohne Zwang je Frage**. | T2 (Leitgedanke) + T3 | Reflexion und Transfer sind optionale Schritte; Übungen funktionieren ohne sie | TC-AG-19 |
| AG-20 | Didaktische Modelle begründet und situationsgerecht einsetzen. | T2 (7) + T1 (ZA-BE E6 «Methoden begründet wählen») | Jede Lernform (Übung, Prüfungssimulation, Lernbegleitung) trägt ihren Zweck und ihre Grenze im Produkt | TC-AG-20 |

**Hinweis zu technischen Entscheidungen:** Der Repetitionsalgorithmus (SM-2, ADR-L-007), der Regler mit vier Stufen (PR-02) und der Freigabeablauf (Abschnitt 4 Dok. 01) sind **Produktentscheidungen (T3)**. Sie werden nicht als SVEB-Pflicht bezeichnet. Die Stufenbezeichnungen «einfach · mittel · schwer · sehr schwer» sind Auftraggeber-Vorgabe; die Zuordnung zu Lernhandlungen ist Produktentscheid und in der Spezifikation §5.4 begründet.

---

## 4 · Prüffälle TC-AG (Auszug)

| ID | Prüfung | Erwartung |
|---|---|---|
| TC-AG-01 | Lektionswahl und Übungsumfang ohne Rückfrage bei Dozierenden | Auswahl wirkt in Übung |
| TC-AG-02 | Selbsteinschätzung verändert die Evidenz nicht | Lernprofil: Evidenz unverändert |
| TC-AG-03 | Anwendungsaufgabe enthält einen Fall aus der Unterlage | Quelle des Falls vorhanden |
| TC-AG-04 | Lernziel steht auf der Lektionsseite und bei jeder zugehörigen Aufgabe | Lernziel-ID in Aufgabe |
| TC-AG-05 | Jede Aufgabe trägt eine Lernhandlungsstufe | kein Feld leer |
| TC-AG-06 | Rückmeldung erscheint unmittelbar nach Antwort, mit Quelle | Quelle vorhanden |
| TC-AG-07 | Falsche Antwort: keine Punktabzüge, neutrale Sprache | Textprüfung gegen Musterliste |
| TC-AG-08 | Zwei Lernprofile erzeugen unterschiedliche Erklärungen | Unterschied im Eingabevertrag nachweisbar |
| TC-AG-09 | Form «Rückfrage» liefert zuerst eine Frage | Ausgabe-Schema |
| TC-AG-10 | Keine Rangliste, keine Serienanzeige | Oberflächenprüfung |
| TC-AG-11 | Meldung erscheint bei Dozierenden mit Entscheidungsnachweis | — |
| TC-AG-12 | Frage ausserhalb der Unterlagen → Lückenhinweis und Weiterleitung | TC-BEG-05 |
| TC-AG-15 | Unterbrechung nur, wenn Prüfungsrahmen es erlaubt | Zustand |
| TC-AG-18 | Reflexionsfrage ist vorhanden und hat keinen Einfluss auf Punkte | Punkte unverändert |
| TC-AG-19 | Übung ist ohne Reflexion vollständig nutzbar | Ablauf ohne Schritt |
| TC-AG-20 | Jede Lernform zeigt Zweck und Grenze | Oberflächenprüfung |

---

## 5 · Abnahme dieses Kapitels

1. Jede AG-Kennung hat eine Herkunftsangabe (T1, T2 oder T3).
2. Keine T2- oder T3-Aussage wird als SVEB-Pflicht bezeichnet (Textprüfung der Oberfläche und der Dokumentation).
3. Die offenen Lücken (Abschnitt 1.2) sind bestätigt oder geschlossen.
4. Die Abnahme durch Auftraggeberin oder Auftraggeber und eine Person mit Erwachsenenbildungs-Hintergrund ist ausstehend.
