# Projektanalyse und lokale Tickets

Stand: 2026-09-07. Gegenstand: vorhandener Python-Code, Konfiguration, Abhängigkeiten,
Skripte und Tests. Anwendungscode wurde nicht geändert. Keine Live-Datenbank,
Importpipeline, API, GPU oder Ollama gestartet; keine Pakete oder Modelle installiert.

## Projektstand

TEI-XML → paragraphenbasierte Bereinigung/Entitätsanreicherung → mehrsprachige
SentenceTransformer-Vektoren → PostgreSQL/pgvector → getrennte Such- und Chat-APIs.
Der Import liest Datenbankbriefe, nicht den konfigurierten XML-Dateipfad. Beide APIs
verwenden beim direkten Start Port 8000. Die Datenbank gehört zum Metamw-Backend
unter `~/development/customers/hu-berlin/metamw/metamw` (`../metamw`), einem
Ruby-on-Rails-Projekt. Quelltabellen und Beziehungen sind dort in `db/migrate/`
und `app/models/` definiert, nicht in diesem Bridge-Repository.

Ergänzende lesende Prüfung gemäß Backend-Vorgabe gegen `master`, Commit
`bac51e8a36fd7d5f2f9612ad71ea9300baef3afc`: Die ursprünglichen Migrationen bestätigen
`letters.content`, `letters.name` und die grundlegenden Orts-/Ländertabellen.
Die Suche nach `letter_embeddings`, `pgvector` und einer Vector-Extension-Aktivierung
unter `db`, `app/models` und `Gemfile` dieses Referenzstands lieferte keine Treffer.
Die Einrichtung der Embedding-Tabelle ist damit dort nicht nachgewiesen; daraus
folgt nicht, dass sie in der realen Datenbank fehlt. Vollständige Migrationshistorie,
angewandter DB-Stand und SQL-Kompatibilität zur echten Datenbank bleiben ungeprüft.

## Nachweise

Ausgeführt:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest tests -q -p no:cacheprovider
```

Ergebnis: **6 fehlgeschlagen, 1 bestanden**. Zwei Tests brechen am Orts-Handler ab,
zwei an fehlenden Argumenten für `assemble_entity_package`, einer am veralteten
Handler-Unpacking und einer an der Notiz-Erwartung. Erfolg: Worttrennungs-Test.

Zusätzliche In-Memory-Prüfungen mit gesperrtem `psycopg2.connect` und gemockter
Entitätsauflösung/Uploadverbindung bestätigen LAB-004 bis LAB-008 und LAB-014.
Diese Prüfungen änderten keine Projektdateien und griffen nicht auf die Datenbank zu.
`importlib.util.find_spec` findet lokal weder `fastapi` noch `ollama` noch `uvicorn`.

Prioritäten: P0 = unmittelbares Datenverlustrisiko bei Ausführung; P1 = zentrale
Funktion defekt oder erhebliche Datenverluste im Verarbeitungsergebnis;
P2 = Robustheit, Betrieb oder Testzuverlässigkeit. Alle Fehler-Tickets sind offen;
Abnahmekriterien beschreiben die spätere Behebung, nicht bereits ausgeführte Arbeit.

## LAB-000 — Projektregeln und Erstprüfung

- Priorität/Status: P2 / erledigt.
- Ziel/Umfang: Projekt erfassen, defensive ticketbasierte `AGENTS.md` erstellen,
  Fehler analysieren und nachprüfbare Tickets dokumentieren.
- Ergebnis: `AGENTS.md` und dieser Bericht erstellt; statische Prüfung, bestehende
  Tests und isolierte Reproduktionen durchgeführt.
- Abnahme: Projektübersicht, Freigabegrenzen, Ticketprozess, priorisierte Befunde
  und Prüfgrenzen dokumentiert. Keine Umsetzung der Fehler-Tickets beauftragt.

## LAB-001 — Unbedingte Löschung des gesamten Embedding-Bestands

- Priorität/Status: P0 / offen.
- Fundstellen: `scripts/process_letters.py:29`, `app/database/models/letter_embedding.py:17`.
- Problem: Jeder Pipeline-Lauf führt `TRUNCATE ... RESTART IDENTITY CASCADE` aus
  und committet separat vor dem ersten Brief. Nachfolgende XML-, Modell- oder
  DB-Fehler lassen einen leeren oder unvollständigen Index zurück. `CASCADE` kann
  zusätzlich referenzierende Tabellen erfassen, abhängig vom externen Schema.
- Nachweis: statischer Aufrufpfad; absichtlich nicht ausgeführt.
- Umfang/Abnahme: Standardlauf erhält bestehende Daten; expliziter Reset nur mit
  überprüftem Ziel und Freigabe. Vollständigen Ersatz erst nach erfolgreichem Aufbau
  veröffentlichen. Abbruchtest mit DB-Doubles belegt Erhalt des bisherigen Bestands.
- Risiko: Höchste Behebungspriorität vor jedem echten Import.

## LAB-002 — Import verarbeitet höchstens 100 Briefe

- Priorität/Status: P1 / offen.
- Fundstelle: `app/database/models/letter.py:22`.
- Problem/Nachweis: `find_all_with_xml` enthält fest `limit 100`; `batch_size`
  verändert nur die Leseportion. Alle weiteren Briefe fehlen. Zusammen mit LAB-001
  werden zuvor vorhandene Embeddings dieser Briefe dauerhaft entfernt.
- Umfang/Abnahme: Vollimport ohne versteckte Gesamtbegrenzung; optionale Begrenzung
  ausdrücklich konfigurierbar. Prüfung mit mehr als 100 simulierten Datensätzen
  und mehreren Batchgrößen belegt vollständige Verarbeitung.

## LAB-003 — Orts-Handler bricht jeden betroffenen Brief ab

- Priorität/Status: P1 / offen.
- Fundstelle: `app/indexer/handler/place_handler.py:11`.
- Problem: Rückgabe referenziert undefiniertes `new_stach`. Auch bloße Korrektur
  zu `new_stack` reicht nicht: Es fehlen die dritten Rückgabedaten für den Dispatcher.
- Nachweis: `test_mendelssohn_chunking` und `test_contextual_place_note_linkage`
  scheitern mit `NameError`. Die Pipeline fängt den Fehler pro Brief und überspringt ihn.
- Umfang/Abnahme: konsistentes Dreiertupel; Ortsname, Schlüssel und Kontext werden
  korrekt weitergegeben; realistischer Brief mit Ort wird vollständig verarbeitet.

## LAB-004 — Gesammelte Entitätsmetadaten werden verworfen

- Priorität/Status: P1 / offen.
- Fundstellen: `app/indexer/tei_chunker.py:59`, `app/indexer/tei_chunker.py:75`.
- Problem: `chunk_metadata['entities']` wird gefüllt, beim Append aber ein neues
  Dictionary ohne Entitäten erzeugt. Dadurch fehlen Such-/Filtermetadaten selbst
  bei erfolgreicher Entitätsauflösung.
- Reproduktion: Absatz mit `<persName key="PSN1">Felix</persName>` und gemocktem
  Profil liefert nur `paragraph_id`, `type`, `letter_year`.
- Umfang/Abnahme: vereinbartes Entitätsschema bis zum Upload erhalten; Test sichert
  Schlüssel und Profilfelder im finalen Chunk. Bestehender Parser-Test erwartet
  abweichend `entity_keys.persons`; Schema und Verbraucher gemeinsam abstimmen.

## LAB-005 — Personenschlüssel der vorhandenen XML-Struktur werden übersehen

- Priorität/Status: P1 / offen.
- Fundstelle: `app/indexer/handler/pers_name_handler.py:7`.
- Problem: Nur `persName/@key` wird gelesen. In `tests/fixtures/sample_letter.xml`
  stehen Schlüssel im versteckten Kind `name/@key`. Gleichzeitig zieht `.//text()`
  dessen Registertext ungefiltert in den sichtbaren Namen.
- Reproduktion: `<persName>Felix<name key="PSN2" style="hidden">Master Name</name></persName>`
  ergibt `FelixMaster Name`, leere Metadaten und null Aufrufe der Entitätsauflösung.
- Umfang/Abnahme: direkte und verschachtelte Schlüssel unterstützen, sichtbaren Text
  von Registerdaten trennen; beide Formen mit Fixtures prüfen.

## LAB-006 — Titel-Handler ist nicht eingebunden; Briefprofile verlieren ihren Text

- Priorität/Status: P1 / offen.
- Fundstellen: `app/indexer/tei_cleaner.py:18`,
  `app/database/services/entity_resolution/info_builders.py:22`.
- Problem: `TitleHandler` existiert, fehlt aber in der Dispatcher-Registrierung.
  Titel laufen durch `DefaultHandler`, ohne Werk-/Briefauflösung. Unabhängig davon
  liefert `Letter.entity_profile` bereits `info`, während `InfoBuilder` für `LET`
  auf `name` zurückfällt. Selbst ein direkt aufgerufener Titel-Handler bekommt
  deshalb einen leeren Informationstext für Briefreferenzen.
- Nachweise: Titel mit verstecktem `name` ergibt ungetrennten Registertext und `{}`;
  `assemble_entity_package('LET', key, {'info': 'Letter from A to B', 'metadata': {}})`
  liefert `info: ''`.
- Umfang/Abnahme: Titel registrieren und LET-Vertrag korrigieren; Tests über den
  tatsächlichen Dispatcher für Werk, Autor und Brief sichern Text und Metadaten.

## LAB-007 — Cache verändert das Metadatenschema

- Priorität/Status: P2 / offen.
- Fundstellen: `app/indexer/handler/base_handler.py:28`, `app/indexer/tei_cleaner.py:48`.
- Problem: `report_key` sammelt `**metadata`, erhält aber `metadata=res['metadata']`.
  Damit entsteht bei Wiederverwendung eine zusätzliche Verschachtelung.
- Reproduktion: erster Abruf `{'PSN1': {'key': 'PSN1'}}`; zweiter Abruf
  `{'PSN1': {'metadata': {'key': 'PSN1'}}}`.
- Umfang/Abnahme: erster Abruf und Cache-Treffer liefern identische Datenformen;
  Test sichert zusätzlich nur einen Aufruf des Datenservices bei Wiederholung.

## LAB-008 — Uploadfehler werden als erfolgreicher Durchlauf ausgegeben

- Priorität/Status: P1 / offen.
- Fundstellen: `app/database/services/ingest_chunks_service.py:38`,
  `scripts/process_letters.py:67`, `scripts/process_letters.py:73`.
- Problem: Upload rollt bei Fehlern zurück, druckt aber nur eine Meldung und liefert
  wie im Erfolgsfall `None`. Auch Fehler pro Brief werden nur protokolliert. Am Ende
  erscheint bedingungslos „All letters successfully transferred“ ohne Fehlerstatus.
- Nachweis: gemocktes `executemany` wirft; `upload_chunks` kehrt regulär mit `None`
  zurück, ein Rollback ist erfolgt. Fehlende Briefe bleiben für Aufrufer unsichtbar.
- Umfang/Abnahme: Fehler propagieren oder strukturiert zählen; Teilfehler ergeben
  einen eindeutig fehlgeschlagenen Lauf und keinen pauschalen Erfolg. Verbindung
  auch bei Fehlern außerhalb der inneren Schleife zuverlässig schließen.

## LAB-009 — APIs ignorieren die konfigurierte Umgebung

- Priorität/Status: P1 / offen.
- Fundstellen: `app/api/search_service.py:15`, `app/api/chat_service.py:19`.
- Problem/Nachweis: Beide APIs lesen fest YAML-Abschnitt `development`, auch bei
  `APP_ENV=test` oder `production`. Der Dateipfad hängt außerdem vom Arbeitsverzeichnis
  ab, anders als in `app/core/config.py`.
- Umfang/Abnahme: gemeinsame umgebungsabhängige Konfiguration verwenden; Test mit
  unterschiedlichen fiktiven DB-Zielen belegt richtige Auswahl ohne echte Verbindung.
- Risiko: Zugriff auf falsche Datenbestände; Umgebungsname allein isoliert Tests nicht.

## LAB-010 — API-Installation und CPU-Start funktionieren nicht zuverlässig

- Priorität/Status: P1 / offen.
- Fundstellen: `pyproject.toml:10`, `requirements.txt`,
  `app/api/search_service.py:12`, `app/api/chat_service.py:10`.
- Problem: `fastapi`, `ollama`, `uvicorn` fehlen in beiden Dependency-Listen und
  der vorhandenen Umgebung. `PyYAML` fehlt zusätzlich in den Projektabhängigkeiten,
  obwohl schon Core-Importe es benötigen. Beide APIs erzwingen CUDA beim Import;
  der Importprozess selbst kann bereits einen Modelldownload starten.
- Nachweis: Dependency-Listen und lokale Modulverfügbarkeit geprüft; kein API-Import
  oder Modelldownload ausgeführt. CUDA-Problem statisch aus `device="cuda"` abgeleitet.
- Umfang/Abnahme: reproduzierbare Runtime-/API-Abhängigkeiten definieren, Gerätewahl
  konfigurieren bzw. CPU-Fallback anbieten; Starttests mit Modell-Doubles auf CPU
  und sauberer deklarierter Umgebung. Keine Downloads beim reinen Modulimport.

## LAB-011 — Bestehende Tests passen nicht zu den aktuellen Verträgen

- Priorität/Status: P2 / offen.
- Fundstellen: `tests/chunk_generation/handler/test_note_handler.py:12`,
  `tests/chunk_generation/test_cleaner.py:10`,
  `tests/chunk_generation/test_tei_processing.py:25`,
  `tests/database/services/test_retrieve_entity.py:37` und `:80`.
- Problem: veraltetes Tuple-Unpacking, String-Erwartungen für Tupel, fehlendes
  `key`-Argument und Platzhalter-Assertion `"TEST"`. Nach vorgeschalteten Fixes
  werden weitere Abweichungen sichtbar, etwa erwartetes `lifespan` und Notizformat.
- Nachweis: oben dokumentierter Testlauf; weitere Widersprüche statisch geprüft.
- Umfang/Abnahme: fachliche Verträge festlegen, aussagekräftige Assertions erhalten,
  DB-Zugriffe in Unit-Tests blockieren/mocken. Alle Tests unter `tests/` grün, ohne
  Live-Datenbank und ohne Platzhalter oder pauschale Skips.

## LAB-012 — API-Fehlerpfade schließen Verbindungen nicht zuverlässig

- Priorität/Status: P2 / offen.
- Fundstellen: `app/api/search_service.py:30`, `app/api/chat_service.py:21`.
- Problem: `conn.close()` steht nur hinter erfolgreicher Abfrage, nicht in `finally`.
  Bei SQL-Fehlern ist explizite Ressourcenfreigabe nicht gewährleistet. Beide
  `async`-Endpunkte führen zudem Modellberechnung, psycopg2 und im Chat Ollama synchron
  aus; lange Anfragen blockieren die Ereignisschleife des jeweiligen Workers.
- Nachweis: statischer Kontrollfluss; Lastverhalten nicht live gemessen.
- Umfang/Abnahme: Fehlerpfade mit Connection-Doubles prüfen; blockierende Arbeit in
  geeignetem Ausführungskontext erledigen und Nebenläufigkeit mit Stubs prüfen.

## LAB-013 — Satzlimit wird ignoriert

- Priorität/Status: P2 / offen.
- Fundstelle: `app/indexer/tei_chunker.py:22`.
- Problem/Nachweis: `sentences_per_chunk` wird angenommen, aber nirgends verwendet;
  immer ein Chunk pro Absatz. Aufrufer übergeben ausdrücklich `3`. Sehr lange
  Absätze können das Eingabelimit des Embedding-Modells überschreiten; wie viel
  Text tatsächlich abgeschnitten wird, wurde ohne Modellstart nicht gemessen.
- Umfang/Abnahme: fachliche Chunk-/Overlap-Strategie definieren und Größenlimit am
  Tokenizer ausrichten; langer Testabsatz bleibt vollständig über die Chunks erhalten.

## LAB-014 — Wortheilung entfernt reguläre Bindestriche

- Priorität/Status: P2 / offen.
- Fundstelle: `app/indexer/tei_cleaner.py:38`.
- Problem: Regex erlaubt null Whitespace und entfernt deshalb auch Bindestriche
  ohne Trennungsnachweis. Das verändert Namen, Ortsverbindungen und Datumsangaben.
- Reproduktion: `heal_word_breaks('Berlin-Leipzig 1841-07-02')` ergibt
  `BerlinLeipzig 184107-02`.
- Umfang/Abnahme: nur nachgewiesene Zeilen-/Worttrennungen heilen; normale Bindestriche
  und ISO-Daten erhalten. Positive und negative Beispiele als Regression prüfen.

## LAB-015 — Zugehöriges Backend als Datenbankreferenz dokumentieren

- Priorität/Status: P2 / erledigt.
- Anlass/Umfang: Nutzerhinweis auf die gemeinsam genutzte Metamw-Datenbank aufnehmen;
  Backend-Vorgaben und grundlegende Tabellendefinitionen ausschließlich lesend prüfen.
- Fundstellen: `../metamw/AGENTS.md`,
  `../metamw/db/migrate/2018/20180222153938_create_letters.rb`,
  `../metamw/db/migrate/2018/20180222182538_create_places.rb`,
  `../metamw/db/migrate/2018/20180414191520_create_countries.rb`.
- Ergebnis/Abnahme: Backend-Pfad, Referenzstand, Verantwortung für Quelltabellen und
  Grenzen für Datenbank-/Backend-Änderungen in `AGENTS.md` und Projektübersicht ergänzt.
  Risiko aus LAB-001 betrifft eine gemeinsam genutzte Backend-Datenbank.
- Prüfung: Git-/Dateilesen und gezielte Suche, keine Backend-Dateien verändert,
  keine Rails-Kommandos oder Datenbankverbindungen ausgeführt. Keine erneuten
  Anwendungstests, da ausschließlich Dokumentation ergänzt wurde.

## Weitere Prüfgrenzen

Unbekannte Entitätsprefixe führen in `RetrieveInfosService.get_info` nach einer
Warnung zum Zugriff auf `None.entity_profile`; aktuelle interne Handler verwenden
bekannte Prefixe. Der global geteilte Cleaner-Zustand ist bei parallelem Chunking
nicht isoliert; die vorhandene Importpipeline arbeitet sequenziell. Diese beiden
Punkte sind Robustheitsrisiken für Erweiterungen, keine nachgewiesenen Ausfälle
des derzeitigen sequenziellen Aufrufpfads.

Kein Live-Nachweis zu SQL-Schema, pgvector-Dimensionen, Fremdschlüssel-Kaskaden,
CUDA-Kompatibilität, Modell-Tokenlimit, Ollama-Verfügbarkeit oder API-Lastverhalten.
Keine externe Recherche und keine Dependency-Sicherheitsprüfung durchgeführt.
