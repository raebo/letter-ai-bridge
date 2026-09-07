# Arbeitsregeln für Agenten

## Geltung und Projekt

Diese Datei gilt für das gesamte Repository. Explizite Nutzeranweisungen und
übergeordnete Vorgaben haben Vorrang. Die kanonische Schreibweise ist `AGENTS.md`.

`letter-ai-bridge` verarbeitet TEI-XML-Briefe für eine RAG-Anwendung:

- `scripts/process_letters.py`: Briefe aus PostgreSQL lesen, Chunks bilden,
  SentenceTransformer-Embeddings erzeugen und nach `letter_embeddings` schreiben.
- `app/indexer/`: XML-Chunking, Textbereinigung und elementbezogene Handler.
- `app/database/`: psycopg2-Verbindungen, SQL-Modelle, Entitätsanreicherung und Import.
- `app/api/`: separate FastAPI-Anwendungen für Suche und Ollama-Chat.
- `app/core/config.py`: YAML-Konfiguration mit `APP_ENV`, standardmäßig `development`.
- `config/settings.yml.example`: Konfigurationsvorlage; lokale Einstellungen sind
  keine Freigabe für Zugriffe auf die dort eingetragene Datenbank.
- `tests/`, `tests/fixtures/`: Tests und XML-Fixtures; `data/letters/`: Quelldokumente.
- `pyproject.toml`, `requirements.txt`: derzeit nicht deckungsgleiche Abhängigkeiten.

Bekannte Fehler und Prüfgrenzen stehen in `AUDIT.md`. Diese Beschreibung des
Ist-Zustands garantiert weder Startfähigkeit noch sichere Skriptausführung.

## Zugehöriges Backend und Datenbankverantwortung

Die Bridge greift auf die Datenbank des Metamw-Backends zu. Das zugehörige
Ruby-on-Rails-Projekt liegt unter
`~/development/customers/hu-berlin/metamw/metamw` (Geschwisterverzeichnis `../metamw`).
Dessen `db/migrate/` und `app/models/` sind bei Fragen zu Quelltabellen,
Beziehungen und Feldbedeutungen heranzuziehen. Die dortige `AGENTS.md` beachten;
sie legt für Analysen `master` als Referenz fest. Ein lokaler Migrationsstand
belegt nicht, welche Migrationen auf einer tatsächlich angebundenen DB angewandt sind.

Backend-Dateien im Rahmen einer Bridge-Analyse nur lesen. Änderungen am Backend,
seinen Migrationen oder seiner Datenbank benötigen einen entsprechenden Auftrag.
Die Bridge darf Quelltabellen wie `letters`, `people`, `places` und Werk-/Beziehungstabellen
nicht als eigene Testdaten behandeln. Auch `letter_embeddings` liegt im Kontext
der gemeinsam genutzten Datenbank; Eigentümerschaft und Abhängigkeiten vor Änderungen
prüfen. Keine Rails-Befehle wie `db:reset`, `db:drop`, `db:prepare` oder Migrationen
zur bloßen Analyse ausführen. Lokale Datenbank-Zugangsdaten nicht ausgeben.

## Ticketbasierte Arbeit

1. Vor Änderungen `git status --short`, vorhandene Vorgaben und relevante Dateien
   prüfen. Fremde Änderungen bewahren. Keine automatischen Bereinigungen.
2. Jede fachliche Änderung einem Ticket zuordnen. Eine externe Ticket-ID übernehmen;
   fehlt sie, selbstständig ein lokales Ticket `LAB-NNN` in `AUDIT.md` anlegen.
   Kein externes Ticketsystem und keine Rückfrage sind dafür erforderlich.
3. Ticketfelder: ID/Titel, Priorität, Status, Problem/Ziel, Umfang, Fundstellen oder
   Reproduktion, Abnahmekriterien, Prüfung/Ergebnis und Risiken. Unbekanntes ausdrücklich
   kennzeichnen. Status: `offen`, `in Arbeit`, `blockiert`, `erledigt`.
4. Nur den beauftragten Umfang bearbeiten. Ein Analyseauftrag autorisiert die
   Dokumentation von Fehlern, aber keine pauschale Umsetzung aller gefundenen Tickets.
5. Änderungen klein und nachvollziehbar halten; keine unabhängigen Refactorings,
   Formatierungen oder Dependency-Upgrades beimischen.
6. Bei Umsetzung zuerst `in Arbeit` setzen, passende Regression absichern, Änderung
   prüfen und Ergebnis im Ticket dokumentieren. `erledigt` erst bei erfüllten
   Abnahmekriterien; fehlende Infrastruktur als Prüfgrenze vermerken.
7. Zum Abschluss Ticket-IDs, Änderungen, tatsächlich ausgeführte Prüfungen und
   verbleibende Risiken nennen. Keine Commits, Pushes oder Veröffentlichungen ohne Auftrag.

## Defensive Ausführung

Vor jedem Kommando Ziel, Arbeitsverzeichnis, Seiteneffekte und Reichweite prüfen.
Skriptnamen wie `test`, `debug` oder `development` sind kein Sicherheitsnachweis.
Importe, Test-Fixtures, Hooks und Konfigurations-Fallbacks können Seiteneffekte auslösen.

Ohne zusätzliche Freigabe im beauftragten Umfang zulässig: gezielte Dateilesen und
Suchen, Git-Status/Diffs, reversible lokale Änderungen sowie zuvor geprüfte,
isolierte Tests ohne externe Zugriffe. Nicht unnötig für solche Arbeiten nachfragen.

Potenziell destruktive oder schwer rückgängig zu machende Aktionen nur bei bereits
vorliegender, konkreter Autorisierung für Ziel und Umfang ausführen. Fehlt diese:
erst konkrete Vorschau, betroffene Ressourcen, Folgen und Wiederherstellung vorbereiten,
dann gezielt nach Freigabe fragen. Allgemeine Aufträge wie „analysieren“, „testen“ oder
„Fehler beheben“ reichen für Datenlöschung nicht aus.

Hierzu zählen insbesondere:

- `rm -rf`, rekursive Löschungen, Wildcard-Löschungen, `find -delete`, Überschreiben
  fremder Dateien, `git clean`, `git reset --hard`, verwerfendes `git restore` oder
  `git checkout --`, History-Rewrites und Force-Pushes.
- SQL `TRUNCATE`, `DROP`, Massen-`DELETE`/`UPDATE`, Schemaänderungen, Datenbank-Restores,
  vollständige Neuindexierung und Änderungen an gemeinsam genutzten Datenbanken.
- `docker compose down -v`, Volume-Löschungen, Prune-Kommandos, Änderungen an Diensten,
  produktiver Infrastruktur, Dateirechten oder Systempaketen.

Zusätzliche Projektregeln:

- `scripts/process_letters.py` nicht als Smoke-Test starten: Es ruft derzeit
  `LetterEmbedding.truncate_table()` mit `RESTART IDENTITY CASCADE` auf und committet
  die Löschung vor dem Import. Auch indirekte Aufrufe sind betroffen.
- Vor freigegebenen Datenmutationen tatsächlichen Host, Datenbanknamen, Schema und
  Umgebung prüfen; Umfang per lesender Vorschau bestimmen. Bei Löschungen außerdem
  verwendbare Sicherung und Wiederherstellungsweg festlegen. Bei Unklarheit stoppen.
- `APP_ENV=test` allein ist kein Schutz: Die APIs verwenden derzeit fest
  `development`. Keine realen DB-Verbindungen in Unit-Tests; Verbindungsaufbau mocken
  oder explizit blockieren. Integrationstests nur gegen eine ausdrücklich dafür
  bestimmte, isolierte Datenbank ausführen.
- Keine vorhandene `config/settings.yml`, `.env*` oder Quelldaten überschreiben.
  Zugangsdaten weder ausgeben noch in Tickets, Logs oder Commits übernehmen.
- API-Importe können Modelle laden und CUDA initialisieren. Modell-Downloads,
  Dependency-Installationen und Live-Skripte nicht nebenbei zur Codeanalyse starten.
- Pfade und Symlinks vor Löschung/Überschreiben auflösen; Ziele innerhalb des
  autorisierten Bereichs halten. Keine dynamischen Löschpfade aus ungeprüften Variablen.
- Sandbox- oder Freigabesperren niemals durch andere Werkzeuge oder Kommandoformen umgehen.

## Prüfung und Codekonventionen

- Vorhandene Python-Umgebung nutzen; keine automatische Neuinstallation.
- Tests zunächst lesen. Nach Prüfung der Seiteneffekte gezielt unter `tests/`
  starten, nicht pauschal das gesamte Repository einschließlich Live-Skripten sammeln:

  ```sh
  PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest tests -q -p no:cacheprovider
  ```

- Aktueller Ausgangsstand: 6 fehlgeschlagen, 1 bestanden (2026-09-07).
  Bestehende Fehler nicht durch abgeschwächte Assertions oder pauschale Skips verdecken.
- Handlervertrag beachten: `handle` liefert `(text, context_stack, metadata)`,
  `TEICleaner.process_node` liefert `(text, metadata)`.
- TEI-Namespace, verschachtelte Elemente, Text/Tails, versteckte Registerdaten und
  Entitätsschlüssel anhand realistischer Fixtures prüfen. Historische Schreibweisen
  und reguläre Bindestriche nicht ohne fachliche Grundlage verändern.
- SQL-Werte parametrisieren, dynamische SQL-Identifier sicher zusammensetzen.
  Verbindungen auch bei Fehlern schließen; Fehler nicht als Erfolg ausgeben.
- Relevante Prüfungen und `git diff --check` ausführen. Nicht ausgeführte Prüfungen
  ausdrücklich nennen; lokale Mock-Tests sind kein Nachweis für Live-DB/GPU/Ollama.
