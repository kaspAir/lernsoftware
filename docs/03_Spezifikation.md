# 03 · Spezifikation

**Version:** 0.2 (2026-11-10) · Vorgänger 0.1
**Bezug:** [01 · Anforderungen](01_Anforderungen.md) (Kennungen) · [02 · Architektur](02_Architektur.md) · [05 · Andragogik](05_Andragogik_SVEB.md)

Diese Spezifikation legt fest, **was** das System tut: Felder, Zustände, Regeln, Schnittstellen. Die Umsetzung im Inkrement 1 ist mit **[Inkr. 1]** gekennzeichnet; alles andere ist geplant. Abweichungen im Code sind Rückgabegründe.

---

## 1 · Konventionen

- Zeitstempel: UTC, ISO 8601.
- Identifikatoren: UUID v4.
- Feldnamen: deutsch, `snake_case`, in Code und API identisch.
- Geschlossene Vokabulare (RA-12) sind Aufzählungen; unbekannte Werte werden abgewiesen.
- Geldbeträge und Punkte: Dezimal mit zwei Stellen (keine Fliesskomma-Rundung im Ergebnis).

## 2 · Rechte-Matrix

Legende: ✓ darf · – darf nicht · (Modul) nur für zugewiesene Module · (eig.) nur eigene Daten · (delegiert) nur wenn Freigabe delegiert ist.

| Funktion | Super-Admin | Admin | Dozierende | Assistenz | Studierende |
|---|---|---|---|---|---|
| Lernorganisation anlegen, deaktivieren, Erstadministration einrichten | ✓ | – | – | – | – |
| Registrierungsdaten lesen (Name, Status) | ✓ | ✓ (eig.) | – | – | – |
| Inhalte einer Lernorganisation lesen | – (PL-02) | – | – | – | – |
| Erscheinungsbild pflegen [Inkr. 4] | – | ✓ | – | – | – |
| Module anlegen, Zuweisungen ändern | – | ✓ | – | – | – |
| Konten anlegen, sperren, Passwort zurücksetzen | – | ✓ | – | – | – |
| Lektionen und Lernziele anlegen, ordnen, archivieren | – | – | ✓ (Modul) | ✓ (Modul) | – |
| Unterlagen hochladen, ersetzen | – | – | ✓ (Modul) | ✓ (Modul) | – |
| Unterlage fachlich freigeben (Ebene A) | – | – | ✓ (Modul) | ✓ (Modul, delegiert) | – |
| Aufgabe fachlich prüfen (Ebene C) | – | – | ✓ (Modul) | ✓ (Modul, delegiert) | – |
| Lernaufgabe vorbereiten (manuell) | – | – | ✓ (Modul) | ✓ (Modul) | – |
| Übung erzeugen und bearbeiten | – | – | – | – | ✓ (Modul, eig.) |
| Meldung einer Aufgabe | – | – | – | – | ✓ (Modul) |
| Meldung bearbeiten | – | – | ✓ (Modul) | – | – |
| Lernbegleiter nutzen | – | – | – | – | ✓ (eig.) |
| Aggregierte Lernprofile eines Moduls | – | ✓ (aggregiert) | ✓ (Modul, aggregiert) | – | – |
| Einzelne Versuche und Gespräche lesen | – | – | nur mit Zustimmung (BS-07) | – | ✓ (eig.) |

Die Rechte werden **serverseitig** an jedem Endpunkt geprüft. Ausblenden in der Oberfläche ersetzt keine Prüfung.

## 3 · Kernobjekte

### 3.1 Governance-Mixin (RA-03)

| Feld | Typ | Pflicht | Bedeutung |
|---|---|---|---|
| `id` | UUID | ja | Identität |
| `lernorganisation_id` | UUID | ja, außer Plattformobjekten | Mandant (RA-08) |
| `created_at`, `updated_at` | timestamptz | ja | Zeitpunkte |
| `version` | int | ja | erhöht sich bei inhaltlicher Änderung |
| `created_by` | Konto-ID oder `system:modell:<klasse>` oder `system:kern` | ja | Urheber; unterscheidet Mensch, Modell, Kern |
| `status` | Enum (je Objekt) | ja | Zustand |
| `schema_version` | text | ja | Fassung des Datenschemas (RA-06) |

### 3.2 Strukturobjekte

- **Lernorganisation** [Inkr. 1]: `name`, `kurzname` (eindeutig, Kleinbuchstaben), `status` (`aktiv` · `deaktiviert`).
- **Modul** [Inkr. 1]: `bezeichnung`, `beschreibung`, `zeitraum_von`, `zeitraum_bis` (optional), `status` (`aktiv` · `archiviert`).
- **Modulzuweisung** [Inkr. 1]: `modul_id`, `konto_id`, `rolle` (`dozierende` · `assistenz` · `studierende`), `freigabe_delegiert` (bool, nur Assistenz, Standard `false`), `gueltig_von`, `gueltig_bis` (optional). Je Kombination aus Modul, Konto und Rolle eindeutig, solange gültig.
- **Lektion** [Inkr. 1]: `modul_id`, `titel`, `reihenfolge` (eindeutig je Modul), `status` (`aktiv` · `archiviert`).
- **Lernziel** [Inkr. 1]: `lektion_id`, `text`, `handlungsstufe` (`wiedergeben` · `anwenden` · `analysieren` · `beurteilen_transfer`), `reihenfolge`.
- **Konto** [Inkr. 1]: `benutzername` (eindeutig, Kleinbuchstaben, 3–64 Zeichen), `anzeigename`, `passwort_hash` (Argon2id), `status` (`aktiv` · `gesperrt` · `deaktiviert`), `fehlversuche`, `gesperrt_bis`. Ein Konto kann mehreren Lernorganisationen zugeordnet sein.

### 3.3 Entwurf und Bestätigung (RA-04)

Getrennte Felder, nie überschrieben:

| Objekt | Entwurf (Modell oder Hochladende) | Bestätigung (Mensch) |
|---|---|---|
| Aufgabe | `entwurf_text`, `entwurf_optionen`, `entwurf_loesung`, `entwurf_erzeugt_von` | `fachlich_geprueft_von`, `fachlich_geprueft_am`, `pruefnotiz`, `aenderungen_gegenueber_entwurf` (Liste: Feld, alt, neu) |
| Unterlage | `hochgeladen_von`, `hochgeladen_am` | `freigegeben_von`, `freigegeben_am`, `freigabeform`, `auflage_verantwortlich`, `auflage_frist` |

Die Differenz zwischen Entwurf und menschlicher Endfassung ist das Divergenzprotokoll (RA-13).

### 3.4 Herkunft (RA-10)

Jeder Abschnitt, jede Aufgabe, jede Rückmeldung und jeder Versuch trägt `herkunft`:
- `quellen`: Liste `{unterlage_id, unterlage_version, abschnitt_id, position}`;
- `erzeugt_durch`: `kern` · `system:modell:<klasse>` · `mensch:<konto_id>`;
- `aufruf_nachweis_id` (falls ein Modell beteiligt war);
- `annahmen`: Liste offener Annahmen.

### 3.5 Quellenstatus: technisch gültig und fachlich gestützt

Zwei Angaben, nie vermischt:

| Feld | Bedeutung | Wer setzt sie |
|---|---|---|
| `quelle_technisch_gueltig` | Die Abschnitt-ID existiert, gehört zur Lernorganisation, ist für die Person zugänglich und die Unterlage ist freigegeben. | Kern, automatisch |
| `fachlich_gestuetzt` | Die konkrete Aussage wird vom zitierten Abschnitt getragen. | Kern nur für geschlossene Prüfung (Stichwort- und Lösungsabgleich ist **keine** fachliche Prüfung); sonst Lehrperson (Ebene C) oder Status `ungeprüft` |

Eine gültige Quellen-ID allein belegt keine inhaltliche Richtigkeit. Das Produkt zeigt beide Angaben getrennt, zum Beispiel: «Quelle: Unterlage X, Abschnitt 4 · Aussage: ungeprüft».

## 4 · Zustände der Unterlage

### 4.1 Status

| Status | Bedeutung | Übergänge nach |
|---|---|---|
| `hochgeladen` | Datei gespeichert, Extraktion ausstehend | `extrahiert`, `extraktion_fehlgeschlagen` |
| `extraktion_fehlgeschlagen` | keine oder unlesbare Textstelle; Grund angegeben | `hochgeladen` (neue Version) |
| `extrahiert` | Abschnitte gebildet | `entwurf` |
| `entwurf` | Wartet auf Freigabe; nicht für Studierende sichtbar | `freigegeben`, `freigegeben_unter_auflage`, `nicht_freigebbar` |
| `freigegeben` | Wirksam für Üben und Prüfung | `in_pruefung` (bei Inhaltsänderung) |
| `freigegeben_unter_auflage` | Wirksam; Auflage mit Verantwortlicher und Frist | `in_pruefung`, `freigegeben` |
| `in_pruefung` | Inhalt geändert. Nicht mehr freigegeben: Abschnitte werden nicht für neue Aufgaben oder Erklärungen verwendet. Aufgaben mit dieser Quelle sind für Studierende ausgeblendet (abgeleitet, keine Statusänderung der Aufgabe; D-06). | `freigegeben`, `freigegeben_unter_auflage`, `nicht_freigebbar` |
| `nicht_freigebbar` | Abgelehnt, mit Begründung | `entwurf` (neue Version) |
| `archiviert` | nicht mehr verwendet; Nachweise bleiben | — |

### 4.2 Regeln (verbindlich, NR-05)

1. Eine neue Version mit geändertem Inhalt setzt `freigegeben` oder `freigegeben_unter_auflage` auf `in_pruefung`. Das geschieht im selben Datenbankvorgang wie das Speichern der Version.
2. Eine Freigabe braucht eine menschliche Handlung mit `konto_id` und `freigabeform`. Bei Auflage sind `auflage_verantwortlich` und `auflage_frist` Pflicht; die Frist liegt in der Zukunft.
3. Eine überfällige Auflage wird berechnet und markiert (RA-11).
4. `nicht_freigebbar` verlangt eine Begründung.
5. Die Freigabe prüft die Berechtigung `freigabe` (Rolle Dozierende oder delegierte Assistenz, siehe Dokument 01 §3).

## 5 · Aufgaben, Übungen und Prüfungsrahmen

### 5.1 Aufgabe

| Feld | Typ | Regel |
|---|---|---|
| `aufgabe_text` | Text | 10–600 Zeichen |
| `fragetyp` | `single_choice` · `multiple_choice` · `luecke` · `offen_kurz` | geschlossen (RA-12). `offen_kurz` ist [Inkr. 2]. |
| `optionen` | Liste (2–6 bei Auswahl) | eindeutig |
| `loesungsschluessel` | Liste der richtigen Option-IDs, bei `luecke` Liste zulässiger Texte | Pflicht bei geschlossenen Typen |
| `lernziel_ids` | Liste, mindestens 1 | Pflicht (AG-04, MO-07) |
| `lektion_id` | UUID | Pflicht |
| `abschnitt_ids` | Liste, mindestens 1 | alle zur selben Lernorganisation und freigegeben |
| `handlungsstufe` | aus dem Lernziel übernommen | Pflicht |
| `denkschritte` | ganze Zahl 1–6 | Schätzung; Lehrperson kann ändern |
| `max_punkte` | Dezimal > 0 | Pflicht; Obergrenze der Punkte je Aufgabe |
| `erklaerung_kurz` | Text, bis 300 Zeichen | Pflicht |
| `pruefstatus` | `technisch_geprueft` · `fachlich_geprueft` · `gesperrt` · `verworfen` | siehe 5.3 |

**Technische Prüfung beim Erzeugen (Kern):**
- alle `abschnitt_ids` existieren, gehören zur Lernorganisation und sind freigegeben;
- Lösung verweist nur auf vorhandene Optionen; bei `single_choice` genau eine richtige;
- Dubletten (normalisierter Vergleich innerhalb der Lektion) werden abgelehnt;
- Länge und Format innerhalb der Grenzen der Konfiguration;
- ein Modell-Vorschlag mit einem Quellen-ID außerhalb der übergebenen Menge wird verworfen und gezählt.

Eine Aufgabe, die nicht besteht, wird verworfen und im Erzeugungsnachweis mit Grund gezählt.

### 5.2 Übung und Testprüfung

**Übung** (Lernmodus) [Inkr. 1]: `konto_id`, `modul_id`, `lektion_ids` (eine oder mehrere), `aufgaben` (eingefroren beim Start mit Aufgabenversion), `modus` = `lernen`, `status` (`offen` · `abgeschlossen`).

**Testprüfung** [Inkr. 3]: wie Übung, mit `pruefungsrahmen_id`, `modus` (`lernen` · `simulation`), `ergebnis` (Punkte, Maximum, Quote).

**Prüfungsrahmen** [Inkr. 3, Struktur — Inhalt fehlt, siehe D-22]: Struktur in §9.2.

### 5.3 Prüfstatus (D-04)

| Status | Bedeutung | Sichtbar in Übung | Sichtbar in Prüfungsrahmen mit «nur fachlich geprüft» |
|---|---|---|---|
| `technisch_geprueft` | Ebene B: KI-erzeugt, technisch geprüft. Kennzeichnung: «KI-erzeugt, technisch geprüft. Nicht von einer Lehrperson geprüft.» | ja | nein |
| `fachlich_geprueft` | Ebene C: von einer Lehrperson geprüft. Kennzeichnung: «Von Lehrperson geprüft (Name, Datum)». | ja | ja |
| `gesperrt` | nach Meldung ausgesetzt, bis Dozierende entschieden haben (LE-08, LE-10) | nein | nein |
| `verworfen` | nicht verwendbar; bleibt im Nachweis | nein | nein |

**Übergänge:** Erzeugung → `technisch_geprueft`. Fachliche Prüfung → `fachlich_geprueft` (Prüfnotiz Pflicht bei Änderungen). Meldung → `gesperrt`. Entscheid nach Meldung → `fachlich_geprueft` (korrigiert), `verworfen` (entfernt) oder zurück zu `technisch_geprueft` (abgewiesen mit Begründung). Jede Änderung eines Aufgabentexts oder Lösungsschlüssels erzeugt eine neue Aufgabenversion und setzt den Status auf `technisch_geprueft`, außer die Änderung wird von einer Lehrperson direkt freigegeben (Divergenzprotokoll).

**Sichtbarkeit abgeleitet:** Eine Aufgabe ist nicht sichtbar, wenn eine ihrer Quell-Unterlagen nicht `freigegeben` oder `freigegeben_unter_auflage` ist (siehe 4.1 `in_pruefung`).

### 5.4 Schwierigkeit: Regler und Dimensionen (PR-02, D-22)

Der Regler mit vier Stufen (einfach · mittel · schwer · sehr schwer) ist Auftraggeber-Vorgabe. **Eine Konzeptvorlage oder eine Stufenbeschreibung mit Inhalt liegt nicht vor.** Die folgende Struktur ist definiert; die Werte je Stufe sind leer und werden von Lehrpersonen gesetzt (keine Erfindung von Inhalten).

Vier Dimensionen werden getrennt geführt und dürfen nicht vermischt werden:

| Dimension | Frage | Ort der Angabe |
|---|---|---|
| **Geforderte Lernhandlung** | Was soll die Person tun? (wiedergeben, anwenden, analysieren, beurteilen/transfer) | Lernziel `handlungsstufe` |
| **Geschätzte Schwierigkeit** | Wie viele Denkschritte, wie komplex ist der Fall? | Aufgabe `denkschritte` |
| **Verfügbare Unterstützung** | Welche Hilfen sind erlaubt? (keine, Hinweis, Beispiel, Erklärung) | Prüfungsrahmen / Modus |
| **Antwortformat** | Wie wird geantwortet? (Auswahl, Lücke, offen kurz) | Aufgabe `fragetyp` |

**Regel gegen künstliche Erschwerung:** Eine höhere Stufe darf nur durch mehr fachliche Denkschritte und komplexere Fälle entstehen, nicht durch missverständliche Formulierung oder unbegründete Detailfragen. Aufgaben mit Mehrdeutigkeitsflag werden von Ebene C geprüft; der Flag kommt von der Lehrperson oder von der Meldung.

**Zuordnung Stufe → Dimensionen** (Struktur im Prüfungsrahmen; Werte offen):

```yaml
stufen:
  einfach:      { handlungsstufen: [], denkschritte: [], hinweise_erlaubt: null, fragetypen: [] }
  mittel:       { handlungsstufen: [], denkschritte: [], hinweise_erlaubt: null, fragetypen: [] }
  schwer:       { handlungsstufen: [], denkschritte: [], hinweise_erlaubt: null, fragetypen: [] }
  sehr_schwer:  { handlungsstufen: [], denkschritte: [], hinweise_erlaubt: null, fragetypen: [] }
```

Was fehlt, ist in D-22 festgehalten. Das Inkrement 1 nutzt keinen Regler; Übungen zeigen alle freigegebenen Aufgaben der gewählten Lektionen.

## 6 · Lernprofil und Wiederholung

### 6.1 Evidenz je Lernziel (Kompetenzeinschätzung)

Jeder Versuch wird je Lernziel der Aufgabe einer Kategorie zugeordnet:

| Kategorie | Bedingung |
|---|---|
| `selbststaendig_richtig` | richtig, keine Hilfe vor der Antwort |
| `mit_hilfe_richtig` | richtig, mindestens eine Hilfe vor der Antwort |
| `falsch` | nicht richtig (Punkte unter Maximum, bei Teilpunkten unter 50 % vgl. Hinweis unten) |

**Zählregeln:**
- Pro Lernziel zählen **verschiedene Aufgaben**: Mehrere richtige Antworten auf dieselbe Aufgabe zählen einmal (`selbststaendig_richtig_aufgaben`, eine Aufgabe, ein Zähler).
- Ein Versuch mit Hilfe ist nie `selbststaendig_richtig`.
- Teilpunkte: Eine Antwort gilt als `selbststaendig_richtig` nur bei vollen Punkten.

### 6.2 Evidenzlage (Regel für «beherrscht», D-13)

| Evidenzlage | Bedingung | Anzeige |
|---|---|---|
| `noch_nicht_belegt` | keine `selbststaendig_richtig`-Aufgabe | «noch nicht belegt» |
| `teilweise_belegt` | 1 bis N−1 verschiedene `selbststaendig_richtig`-Aufgaben | «teilweise belegt (k von N)» |
| `ausreichend_belegt` | mindestens N verschiedene `selbststaendig_richtig`-Aufgaben | «ausreichend belegt» |

N ist Konfiguration (`evidenz.schwelle_aufgaben`, Startwert 3). Die Anzeige nennt immer das Datum der letzten Evidenz. Ein Lernziel mit `ausreichend_belegt` und zwei folgenden `falsch` wird als «widersprüchlich, bitte erneut prüfen» angezeigt; die Evidenzlage bleibt unverändert.

**Selbsteinschätzung** (optional, je Versuch: `sicher` · `unsicher` · `unklar`) wird getrennt gespeichert und angezeigt. Sie ändert die Evidenzlage nicht (AG-02).

### 6.3 Wiederholungsplanung (SM-2, austauschbar, ADR-L-007)

Die Wiederholungsplanung entscheidet, **wann** eine Aufgabe erneut erscheint. Sie hat keinen Einfluss auf die Evidenzlage.

**Qualität `q` je Versuch:**

| Ergebnis | Selbsteinschätzung | `q` |
|---|---|---|
| falsch | — | 1 |
| richtig mit Hilfe | — | 3 |
| richtig ohne Hilfe | `unsicher` oder `unklar` | 3 |
| richtig ohne Hilfe | keine | 4 |
| richtig ohne Hilfe | `sicher` | 5 |

**Algorithmus:** Zustand je Aufgabe und Person: `ease` (Start 2,5), `intervall_tage` (Start 0), `wiederholungen`, `naechste_faelligkeit`.
1. Wenn `q` < 3: `wiederholungen` = 0; `intervall_tage` = 1.
2. Sonst: `wiederholungen` += 1; Intervall 1 Tag (1. Wiederholung), 6 Tage (2.), danach `intervall_tage` × `ease`, gerundet, höchstens 365 Tage.
3. `ease` = max(1,3; `ease` + (0,1 − (5 − q) × (0,08 + (5 − q) × 0,02))).
4. `naechste_faelligkeit` = Datum des letzten Versuchs + `intervall_tage`.

Parameter sind Konfiguration (§9). Ein Wechsel des Verfahrens ist ein Übergang für Bestandsdaten (RA-06).

### 6.4 Sichtbarkeit von Unsicherheit (RA-11)

Jede Lernzielanzeige zeigt: Evidenzlage (6.2), Anzahl Aufgaben, Datum der letzten Evidenz und ggf. «fällig zur Wiederholung am …» (aus 6.3). Keine Formulierung wie «sicher» oder «beherrscht» ohne Zahlen.

## 7 · Bewertung und Auswertung

### 7.1 Geschlossene Aufgaben (Code, Inkr. 1)

| Typ | Punkte |
|---|---|
| `single_choice` | `max_punkte` bei korrekter Option, sonst 0 |
| `multiple_choice` | `max_punkte` × clamp(richtig_gewählt − falsch_gewählt, 0, n_richtig) ÷ n_richtig; mit Maximum `max_punkte`, nie negativ |
| `luecke` | `max_punkte` bei Übereinstimmung mit einem zulässigen Text nach Normalisierung (Kleinschreibung, Leerzeichen, Umlaute), sonst 0 |

**Normalisierung** ist Konfiguration; sie ändert nie die Bedeutung (keine Synonyme im Code).

**Qualitätsrisiko:** Der Lösungsschlüssel ist nur so gut wie seine fachliche Prüfung. Aufgaben ohne Ebene C tragen den Hinweis aus 5.3.

### 7.2 Offene Antworten (KI-gestützt, Inkr. 2)

- Bewertungsraster: Kriterien mit `punkte`, `indikatoren` (beobachtbare Merkmale) und `quellen` (Abschnitte, die das Kriterium stützen). Das Raster ist Pflicht und Teil der Aufgabenversion.
- Das Modell schlägt je Kriterium eine Stufe vor, mit Begründung, Textstelle der Antwort und Sicherheitsgrad (RA-11). Es erzeugt keine Punkte ohne Raster.
- Der Kern summiert, begrenzt auf `max_punkte` je Kriterium und gesamt, und berechnet die Quote.
- Sinngleiche Formulierungen, Negationen, Teilrichtigkeit und vertretbare Lösungsvarianten sind die Stärken und Grenzen des Modells. Jede Rückmeldung nennt die Grenzen, und Ergebnisse mit Sicherheitsgrad `unbestaetigt` werden als Vorschlag markiert.
- Stichwortsuche allein ist kein zulässiges Verfahren.

### 7.3 Vokabular (RA-12)

| Liste | Werte |
|---|---|
| `handlungsstufe` | `wiedergeben` · `anwenden` · `analysieren` · `beurteilen_transfer` |
| `fragetyp` | `single_choice` · `multiple_choice` · `luecke` · `offen_kurz` |
| `pruefstatus` | `technisch_geprueft` · `fachlich_geprueft` · `gesperrt` · `verworfen` |
| `freigabeform` | `freigegeben` · `freigegeben_unter_auflage` · `nicht_freigebbar` |
| `meldungsgrund` | `fehlerhaft` · `unklar` · `nicht_aus_unterlagen` · `sonstiges` |
| `meldungsentscheid` | `korrigiert` · `entfernt` · `abgewiesen` |
| `rolle` | `admin` · `dozierende` · `assistenz` · `studierende` |
| `evidenzlage` | `noch_nicht_belegt` · `teilweise_belegt` · `ausreichend_belegt` · `widerspruechlich` |
| `sicherheitsgrad` (Modellaussage) | `sicher` · `wahrscheinlich` · `unbestaetigt` |
| `hilfeart` | `hinweis` · `beispiel` · `erklaerung` |

Erweiterung ist ein bewusster Akt mit Versionssprung und Übergangsregel.

### 7.4 Punkteberechnung und Prozentwerte (PR-05)

- Maximum einer Übung: Summe der `max_punkte` aller ihrer Aufgaben.
- Punkte: Summe der erreichten Punkte, je Aufgabe auf `max_punkte` begrenzt.
- Quote: `round(Punkte ÷ Maximum × 100)` als ganze Prozent; bei Maximum 0 keine Quote, sondern Hinweis.
- Die Summe der Punkte ist nie größer als das Maximum (Test TC-PRF-01).

## 8 · Versionierung, Versuchstreue und Nachweise (RA-06, LE-11)

- Jedes gespeicherte Objekt trägt `schema_version`. Aufgaben tragen `aufgabe_version`, Lösungsschlüssel-Version und Raster-Version.
- **Versuchstreue:** Ein Versuch speichert eine Kopie des Aufgabenzustands, auf den er sich bezieht (Text, Optionen, Lösungsschlüssel, Raster, Aufgabenversion). Spätere Änderungen an der Aufgabe verändern den Versuch nicht. Die Diskussion eines Versuchs zeigt das **ursprüngliche** Ergebnis und, falls geändert, den Hinweis «Aufgabe seit diesem Versuch geändert (Version x → y)».
- Der Versuch vermerkt Hilfen mit Zeitpunkt (`hilfen: [{art, zeitpunkt, aufgabe_version}]`) und die Selbsteinschätzung.
- Eine Auswertung ist nach Abgabe unveränderlich. Eine Korrektur (z. B. nach einer Meldung) ist eine **neue Auswertung** mit Verweis auf die alte; die alte bleibt sichtbar (NR-10).
- Nachweise (Abschnitt 6 in Dokument 02) sind unveränderlich.

## 9 · Konfiguration (RA-07)

### 9.1 Dateien

| Datei | Inhalt | Geltung |
|---|---|---|
| `config/basis.yaml` | Standardwerte: Evidenzschwelle, SM-2-Parameter, Limits (Dateigröße, Abschnittslänge), Normalisierung, verbotene Muster in Erklärungen, Sitzungsdauer, Sperrgrenzen | Plattform |
| `config/vokabular.yaml` | geschlossene Listen (7.3) | Plattform |
| `config/pruefungsrahmen/<name>.yaml` | Prüfungsrahmen (9.2) | Lernorganisation |
| `config/lernorganisation/<kurzname>.yaml` [Inkr. 4] | Erscheinungsbild | Lernorganisation |

Jede Datei trägt `schema_version` und `version`. Ein Delta, das auf keinen Basiswert zeigt, ist ungültig.

### 9.2 Prüfungsrahmen (Struktur)

```yaml
schema_version: 1
version: 1
name: "<Bezeichnung des Rahmens>"      # INHALT FEHLT — siehe D-22
herkunft: "<Quelle des Rahmens>"       # INHALT FEHLT
modus: simulation                      # lernen | simulation
nur_fachlich_geprueft: false           # Ebene C erforderlich (PR-09)
unterbrechbar: false                   # Frage des Rahmens (PR-12)
rueckmeldung: nach_pruefung            # sofort | nach_pruefung
zeit_minuten: null                     # Frage des Rahmens; null = keine Zeitvorgabe
hinweise_erlaubt: false
themengewichtung: []                   # je Lernziel oder Lektion, Anteil in Prozent — INHALT FEHLT
aufgabenformen: []                     # erlaubte fragetypen mit Anteil — INHALT FEHLT
punkte:
  maximum: null                        # INHALT FEHLT
  verteilung: null
anzahl:
  minimum: null                        # PR-03
  maximum: null
  standard: null
```

**Kennzeichnung:** Ein Rahmen mit leeren Feldern ist als **unvollständig** markiert und kann nicht für eine Prüfungssimulation verwendet werden. Ein Beispielrahmen für die Tests ist als `synthetisch: true` gekennzeichnet und erscheint nie als Rahmen der Lernorganisation.

### 9.3 Erscheinungsbild [Inkr. 4] (PL-03, PL-04)

Farben im Format `#RRGGBB`: `primaer`, `sekundaer`, `hintergrund`, `text`, `flaeche`. Logo: SVG oder PNG, höchstens 512 kB, `alt_text` Pflicht. Prüfung: Text auf Hintergrund mindestens 4,5 : 1, Schaltflächen und Oberflächenelemente mindestens 3 : 1. Verstoss blockiert die Speicherung mit Angabe des Werts und der verletzten Regel.

## 10 · Lernbegleiter: Vertrag mit dem Modell

**Eingabe an `ki_aufruf` (Modellklasse «Sprache»), Inkr. 1:**

```json
{
  "aufgabe": "rueckmeldung | rueckfrage | erklaerung | hinweis | beispiel",
  "versuch": {"id": "…", "aufgabe_version": 3, "aufgabe_text": "…", "gegeben": "…",
              "richtig": false, "punkte": 0, "maximum": 1},
  "loesung": {"text": "…", "begruendung_schluessel": "…"},
  "abschnitte": [{"id": "…", "text": "…"}],
  "lernprofil": {"staerken": ["…"], "offen": ["…"], "letzte_fehler": ["…"]},
  "lernziel_ids": ["…"],
  "pseudonym": "Person A"
}
```

- Das Lernprofil wird **pseudonymisiert** übergeben: keine Klarnamen, keine Matrikelnummern, keine E-Mail-Adressen (NF-02, RA-09). Die Pseudonymisierung ist Aufgabe des Vorschaltdienstes; das Produkt sendet den Namen nie.
- Abschnitte sind die einzige Quelle. Andere Unterlagen werden nicht übergeben (NR-04, NR-02).
- **Mandant:** Jeder Aufruf trägt `X-Pseudo-Mandant` = Lernorganisation, `X-Pseudo-Projekt` = Versuchs-ID-Gruppe (stabil je Sitzung), `X-Pseudo-Anwendung` = `lernsoftware`.

**Erwartete Ausgabe (Schema, Kern-geprüft):**

```json
{
  "form": "hinweis | rueckfrage | beispiel | erklaerung",
  "text": "…",
  "schritte": ["…"],
  "quellen": [{"abschnitt_id": "…", "aussage": "…"}],
  "luecke": null,
  "sicherheitsgrad": "sicher | wahrscheinlich | unbestaetigt",
  "annahmen": ["…"]
}
```

**Kern-Prüfung:**
1. Schema vollständig und typgerecht; bei Fehler ein Wiederholungsversuch mit fester Obergrenze (Konfiguration, Startwert 1), danach Standardantwort. Wiederholungen werden protokolliert.
2. Jede `abschnitt_id` ∈ übergebener Menge; sonst Ablehnung des Textes (BS-02). Das Ergebnis trägt dann keine Quelle und wird nicht als Aussage angezeigt.
3. `quellen` leer und `luecke` leer → Antwort wird als `unbelegt` gekennzeichnet; Standardtext nach BS-05.
4. Verbotene Muster (Bewertungssprache, z. B. Note, Bestanden, Versagt) → Ablehnung (BS-06).
5. `sicherheitsgrad` ≠ `sicher` → `annahmen` ist Pflicht und wird angezeigt.

**Anzeige:** Text, Quellen mit Link auf den Abschnitt, Angabe «Aussage: fachlich ungeprüft», Sicherheitsgrad und Annahmen. Bei Ablehnung: «In den freigegebenen Unterlagen finde ich dazu keine belegte Antwort. Du kannst die Frage an die Lehrperson weiterleiten.»

**Standardantwort bei Modellausfall:** «Der Lernbegleiter ist gerade nicht erreichbar. Deine Antwort ist gespeichert.» Keine erfundene Erklärung.

## 11 · Upload und Extraktion

**Inkrement 1:** `.txt` und `.md`. **Inkrement 2:** PDF, DOCX, PPTX (siehe ADR-L-004).

| Regel | Festlegung |
|---|---|
| zulässige Typen | Prüfung über Inhalt (UTF-8-Text, kein Binärinhalt), nicht nur Endung |
| Größe | Konfiguration; Startwert 2 MB für Text |
| Speicherort | unterhalb des Werkverzeichnisses, Pfad aus interner ID abgeleitet, nie aus dem Dateinamen; Pfad, der hinausführt, wird abgewiesen |
| Dateiname | bereinigt; nur Anzeige |
| Extraktion | synchron im Inkrement 1 (Text ist klein); Status sichtbar |
| Abschnitte | Absatzgrenzen; Länge 300–1 200 Zeichen; Markdown-Überschriften als Abschnittsgrenze; Position = Absatznummer |
| Einbettung | im Inkrement 1 nicht genutzt (Suche über Lektion, keine Vektorsuche) |
| Löschung | Unterlage entfernen → Datei und Abschnitte entfernt; Aufgaben, die darauf beruhen, werden `gesperrt`; Versuche bleiben |

## 12 · Fehlerverhalten

- Fehlende Pflichtfelder: Abbruch, kein Platzhalter.
- Modell nicht erreichbar: klare Meldung (10), keine stille Ersatzantwort. Übung und Versuch bleiben nutzbar; nur Rückmeldung mit Modell und Erzeugung sind betroffen. Im Inkrement 1 ist die **deterministische Rückmeldung** (Lösungsschlüssel + Quelle) vom Modell unabhängig.
- Zeitüberschreitung: Abbruch nach konfigurierter Grenze (Startwert 20 s); Wiederholung nur auf ausdrückliche Aktion.
- Jede Ablehnung durch den Kern erzeugt einen Nachweis mit Kennung (z. B. `NR-02`, `BS-02`).

## 13 · Schnittstellen (Inkrement 1)

Alle Endpunkte unter `/api/v1/`. JSON. Fehler: `{"fehler": {"code": "…", "nachricht": "…", "felder": {}}}`. Sitzungscookie: HttpOnly, SameSite=Lax; `Secure` ab HTTPS. CSRF-Token bei schreibenden Anfragen.

| Methode | Pfad | Zweck | Rolle |
|---|---|---|---|
| POST | `/auth/anmelden` | Anmelden (Rate-Limit) | öffentlich |
| POST | `/auth/abmelden` | Abmelden | alle |
| GET | `/superadmin/lernorganisationen` | Liste (Registrierungsdaten) | Super-Admin |
| POST | `/superadmin/lernorganisationen` | anlegen mit Erstadministration | Super-Admin |
| GET/POST | `/module` | Module lesen, anlegen | Admin; Lesen auch Zugewiesene |
| POST | `/module/{id}/zuweisungen` | Zuweisung, Delegation | Admin |
| POST | `/module/{id}/lektionen` | Lektion anlegen | Dozierende, Assistenz (Modul) |
| POST | `/lektionen/{id}/lernziele` | Lernziel anlegen | Dozierende, Assistenz (Modul) |
| POST | `/module/{id}/unterlagen` | Unterlage hochladen (Text/Markdown) | Dozierende, Assistenz (Modul) |
| POST | `/unterlagen/{id}/freigabe` | Freigabe, Auflage | Dozierende, delegiert Assistenz |
| POST | `/module/{id}/aufgaben` | Lernaufgabe manuell anlegen | Dozierende, Assistenz |
| POST | `/module/{id}/uebungen` | Übung erzeugen (Lektionen wählen) | Studierende (Modul) |
| GET | `/uebungen/{id}` | Übung lesen (eingefrorener Stand) | Studierende (eig.) |
| POST | `/uebungen/{id}/versuche` | Antwort abgeben, Hilfen vermerkt | Studierende (eig.) |
| POST | `/aufgaben/{id}/hilfe` | Hilfe anfordern (vermerkt) | Studierende (eig.) |
| POST | `/versuche/{id}/meldung` | Aufgabe melden | Studierende |
| POST | `/meldungen/{id}/entscheid` | Meldung entscheiden | Dozierende |
| GET | `/module/{id}/lernprofil` | eigenes Lernprofil bzw. aggregiert | Studierende (eig.), Dozierende (aggregiert) |
| POST | `/versuche/{id}/gespraech` | Lernbegleiter-Nachricht | Studierende (eig.) |
| GET | `/gespraech/{id}` | Verlauf | Studierende (eig.) |

Inkrement 3 ergänzt Prüfungsrahmen und Testprüfungen; Inkrement 4 Erscheinungsbild und CSV-Import.

## 14 · Datenschutz

- Gespräche: Aufbewahrung 12 Monate als Vorschlag (D-09); danach Löschung oder Anonymisierung.
- Export eigener Daten als JSON für Studierende (NF-02).
- Konto-Löschung: Versuche und Gespräche werden gelöscht oder pseudonymisiert; Nachweise mit Personenbezug werden durch ein Pseudonym ersetzt. Aufbewahrungspflichten sind rechtlich offen (D-09).
- Protokolle enthalten keine Passwörter, Sitzungs-IDs oder vollständige Versuchstexte.
- Modellaufrufe erhalten keine Klarnamen (10).

---

## 15 · Festlegungen Inkrement 1.1 (Ergänzung zu den Abschnitten oben)

**§2.1 Modulrolle (D-25).** Je Konto und Modul gibt es genau eine Zuweisung. Eine neue Zuweisung ersetzt die alte; der Nachweis `zuweisung` enthält die bisherige Rolle unter `vorher`. Die Organisationsrolle `admin` gilt unabhängig davon.

**§3.2 Sitzung (D-24).** Die Sitzung endet 120 Minuten nach der Anmeldung (`app/sitzung.py`). Bei jeder Anfrage werden Konto, Organisation und Modulzuweisung neu geladen (`rechte.lade_kontext`). Deaktivierung wirkt damit sofort, auch bei bestehender Sitzung.

**§5.5 Antwortformat (D-26).**

| Fragetyp | Format | Fehler |
|---|---|---|
| `single_choice` | Liste mit genau einer gültigen Option-ID, z. B. `["antwort_b"]` | nicht Liste; keine oder mehrere Optionen; unbekannte ID |
| `multiple_choice` | Liste mit mindestens einer eindeutigen, gültigen Option-ID | leere Liste; Duplikate; unbekannte ID |
| `luecke` | Text, 1 bis 200 Zeichen nach dem Trimmen | Liste oder Zahl; leer; zu lang |

Die Prüfung erfolgt in `kern/antwort.py`, bevor eine Abgabe entsteht. Fehler: HTTP 422, Code `antwort_ungueltig`, verständlicher Text.

**§6.1 Hilfe und frühere Lösung (D-28).** Eine Hilfe, die vor einer Abgabe angezeigt wurde, wird am Versuch vermerkt (`hilfen`). Hat dieselbe Person die Aufgabe schon einmal abgegeben, enthält jede weitere Abgabe zusätzlich den Eintrag `loesung_gesehen`. Beide Fälle zählen nicht als selbstständige Leistung.

**§8 Abgabe und Gesprächsfrage: Anfrage-Schlüssel (D-27).** Schreibende Abgaben (`POST /uebungen/{id}/versuche`) und Fragen (`POST /versuche/{id}/gespraech`) verlangen den Kopf `Idempotency-Key` (8 bis 64 Zeichen aus `A–Z a–z 0–9 _ -`). Die Eindeutigkeit `(konto_id, idempotenz_schluessel)` bzw. `(konto_id, anfrage_schluessel)` ist in der Datenbank festgelegt.

- Derselbe Schlüssel für dieselbe Aufgabe liefert die gespeicherte Auswertung mit `wiederholt: true` und Status 200. Es wird weder ein Versuch noch eine Wiederholungsplanung neu geschrieben.
- Derselbe Schlüssel für eine andere Aufgabe oder Übung: HTTP 409, `schluessel_wiederverwendet`.
- Parallele Anfragen mit demselben Schlüssel: Die zweite scheitert an der Eindeutigkeit, wird zurückgerollt und liefert die gespeicherte Auswertung.
- Eine bewusste neue Bearbeitung hat einen neuen Schlüssel und erhält die nächste `versuchsnummer`. Die Oberfläche kennzeichnet sie als «Erneute Bearbeitung».

**§10 Modellkontext und Validierung (D-30).** Der Auftrag enthält: Aufgabentext und Version zum Zeitpunkt der Abgabe, Optionen mit Text, Lösung und Begründung, verwendete Hilfen, die letzten 6 Nachrichten des Gesprächs, die Evidenzlage des Lernziels und die zulässigen Abschnitte. Die Obergrenze beträgt 6 000 Zeichen; zuerst wird der Verlauf gekürzt. Personenbezogene Angaben fehlen.

Jede Modellausgabe wird vor der Verarbeitung vollständig geprüft (`kern/modellpruefung.py`): Pflichtfelder, keine unbekannten Felder, zulässige Form und Sicherheitsgrade, Quellenobjekte (höchstens 5, nur übergebene Abschnitts-IDs), Annahmen als Liste von höchstens 5 Texten, Lücke als Text oder `null`, keine Bewertungssprache. Ungültige Ausgaben führen zu einer Wiederholung (`schema_wiederholungen`), danach zu einer Systemmeldung. Inhaltliche Verstöße (Quelle, Bewertung) werden ohne Wiederholung abgelehnt und mit Kennung nachgewiesen (NR-02, BS-06).

Herkunft je Antwort: `echt` (Vorschaltdienst), `SIMULIERT` (Testadapter), `system` (Fehler, Blockade) oder `kern`.

**§10.1 Zulässigkeit einer neuen Erklärung (D-29).** Eine neue Erklärung entsteht nur, wenn alle zitierten Abschnitte der aktuell freigegebenen Fassung entsprechen. Andernfalls antwortet das System mit einer Begründung; der bisherige Verlauf bleibt erhalten, und es erfolgt kein Modellaufruf.

**§13 Ergänzte Schnittstellen (Inkrement 1.1).**

| Methode | Pfad | Zweck |
|---|---|---|
| GET | `/uebungen/{id}` | Übung mit aktuellem Stand je Aufgabe (Verfügbarkeit, offene Hilfe, Versuche) |
| GET | `/versuche/{id}` | dauerhaft abrufbare Versuchssicht mit Verlauf und Quellen |
| GET | `/abschnitte/{id}` | zitierter Abschnitt mit historischem Stand und aktuellem Status |
| GET | `/modell` | wirksamer Modellmodus |

Die Ausgabe von `POST /versuche/{id}/gespraech` enthält `frage_id`, `frage`, `antwort` (mit `herkunft`, `quellen`, `sicherheitsgrad`, `annahmen`, `luecke`) und `wiederholt`.
