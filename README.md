# Status Simulator (Leitstelle Simulator)

[English](#english) | [Deutsch](#deutsch)

---

<a name="english"></a>
## English

### Project Overview
The **Status Simulator** is a web-based application designed to simulate the status reporting and communication between emergency vehicles and a central dispatch (Leitstelle). It allows for real-time status updates, messaging, and coordination between different roles: Dispatch (Leitstelle), Unit Leader (Staffelführer), and Vehicles.

### Features
- **Leitstelle (Dispatch) View**: Create a dispatch center, manage vehicle connections, send broadcast or private messages, and clear special status requests.
- **Vehicle Status View**: Simulated keypad for status updates (e.g., Status 1-4, 7-8), special signals (Blitz, Sprechwunsch), and pre-defined short status messages (Kurzstatus).
- **Staffelführer (Unit Leader) View**: Monitor assigned vehicles and communicate with them.
- **Real-time Communication**: Powered by WebSockets for instantaneous updates across all connected clients.
- **Status Transition Logic**: Enforces realistic status flows (e.g., Status 7 only after Status 4, Status 8 only after Status 7).
- **License**: Released under the GPL-3.0 License.

### Technology Stack
- **Backend**: Python, FastAPI
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Templating**: Jinja2
- **Infrastructure**: Docker, Pipenv

### Getting Started

#### Prerequisites
- Docker and Docker Compose
- *OR* Python 3.14 with Pipenv

#### Running with Docker
1. Build the image:
   ```bash
   docker build -t status-sim .
   ```
2. Run the container:
   ```bash
   docker run -p 8000:8000 status-sim
   ```
3. Access the application at `http://localhost:8000`.

#### Running Locally
1. Install dependencies:
   ```bash
   pipenv install
   ```
2. Run the application:
   ```bash
   pipenv run uvicorn src.main:app --reload
   ```

---

<a name="deutsch"></a>
## Deutsch

### Projektübersicht
Der **Status Simulator** ist eine webbasierte Anwendung zur Simulation der Statusmeldungen und Kommunikation zwischen Einsatzfahrzeugen und einer zentralen Leitstelle. Die Anwendung ermöglicht Echtzeit-Status-Updates, Nachrichtenversand und die Koordination zwischen verschiedenen Rollen: Leitstelle, Staffelführer und Fahrzeuge.

### Funktionen
- **Leitstellen-Ansicht**: Erstellen einer Leitstelle, Verwalten von Fahrzeugverbindungen, Senden von Rundspruch- oder Privatnachrichten und Zurücksetzen von Sonderrechten.
- **Fahrzeug-Status-Ansicht**: Simuliertes Tastenfeld für Statusmeldungen (z.B. Status 1-4, 7-8), Sondersignale (Blitz, Sprechwunsch) und vordefinierte Kurzstatusmeldungen.
- **Staffelführer-Ansicht**: Überwachung der zugewiesenen Fahrzeuge und Kommunikation mit diesen.
- **Echtzeit-Kommunikation**: Basierend auf WebSockets für sofortige Aktualisierungen bei allen verbundenen Clients.
- **Status-Logik**: Erzwingt realistische Statusabfolgen (z.B. Status 7 nur nach Status 4, Status 8 nur nach Status 7).
- **Lizenz**: Veröffentlicht unter der GPL-3.0 Lizenz.

### Technologie-Stack
- **Backend**: Python, FastAPI
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Templating**: Jinja2
- **Infrastruktur**: Docker, Pipenv

### Erste Schritte

#### Voraussetzungen
- Docker und Docker Compose
- *ODER* Python 3.14 mit Pipenv

#### Ausführung mit Docker
1. Image erstellen:
   ```bash
   docker build -t status-sim .
   ```
2. Container starten:
   ```bash
   docker run -p 8000:8000 status-sim
   ```
3. Anwendung aufrufen unter `http://localhost:8000`.

#### Lokale Ausführung
1. Abhängigkeiten installieren:
   ```bash
   pipenv install
   ```
2. Anwendung starten:
   ```bash
   pipenv run uvicorn src.main:app --reload
   ```
