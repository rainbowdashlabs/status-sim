<script setup lang="ts">
import { onMounted } from 'vue'
import Footer from './components/Footer.vue'
import StatusBadge from './components/StatusBadge.vue'

onMounted(() => {
  document.title = 'Hilfe - Funk Simulator'
})
</script>

<template>
  <div class="page">
    <div class="flex-1">
      <h1 class="section-title text-2xl mb-2 text-center">Hilfe</h1>
      <p class="text-themed-muted text-center text-sm mb-8">
        <a href="/" class="text-primary hover:underline">Zurück zur Startseite</a>
      </p>

      <div class="max-w-3xl mx-auto flex flex-col gap-8">

        <!-- Überblick -->
        <section class="card p-5">
          <h2 class="section-title text-lg mb-3">Was ist der Funk Simulator?</h2>
          <p class="text-themed-muted leading-relaxed">
            Der Funk Simulator bildet die Kommunikation zwischen einer Leitstelle, Fahrzeugen und Staffelführern
            im Einsatzdienst ab. Er eignet sich zum Üben von Funksprüchen, Statusmeldungen und Einsatzabläufen.
          </p>
          <p class="text-themed-muted leading-relaxed mt-2">
            Es gibt drei Rollen, die über unterschiedliche Codes beitreten:
          </p>
          <div class="flex flex-wrap gap-3 mt-3">
            <span class="btn btn-primary px-3 py-1.5 text-sm cursor-default">Leitstelle (Admin-Code)</span>
            <span class="btn btn-success px-3 py-1.5 text-sm cursor-default">Fahrzeug (Fahrzeug-Code)</span>
            <span class="btn btn-info px-3 py-1.5 text-sm cursor-default">Staffelführer (SF-Code)</span>
          </div>
        </section>

        <!-- Erste Schritte -->
        <section class="card p-5">
          <h2 class="section-title text-lg mb-3">Erste Schritte</h2>
          <ol class="text-themed-muted leading-relaxed list-decimal list-inside flex flex-col gap-2">
            <li>
              <strong class="text-themed">Leitstelle erstellen:</strong>
              Auf der Startseite einen Namen eingeben (z.B. "Florian Berlin") und auf
              <span class="btn btn-primary px-2 py-0.5 text-xs cursor-default">Erstellen</span> klicken.
            </li>
            <li>
              <strong class="text-themed">Codes verteilen:</strong>
              Nach dem Erstellen werden drei Codes angezeigt. Den <strong>Fahrzeug-Code</strong> an die Fahrzeugbesatzungen
              und den <strong>Staffelführer-Code</strong> an die Staffelführer weitergeben.
              <div class="mt-2 flex gap-3">
                <div class="text-center">
                  <span class="block mb-0.5 font-bold text-themed-muted text-[0.7rem] uppercase">Fahrzeug-Code</span>
                  <span class="bg-themed-overlay p-1.5 px-2.5 rounded border border-themed font-mono font-bold text-primary text-lg">A1B2C3D4</span>
                </div>
                <div class="text-center">
                  <span class="block mb-0.5 font-bold text-themed-muted text-[0.7rem] uppercase">Staffelführer-Code</span>
                  <span class="bg-themed-overlay p-1.5 px-2.5 rounded border border-themed font-mono font-bold text-success text-lg">E5F6G7H8</span>
                </div>
              </div>
            </li>
            <li>
              <strong class="text-themed">Beitreten:</strong>
              Auf der Startseite den erhaltenen Code und einen Funkrufnamen eingeben und
              <span class="btn btn-success px-2 py-0.5 text-xs cursor-default">Beitreten</span> klicken.
              Je nach Code wird man als Fahrzeug oder Staffelführer verbunden.
            </li>
          </ol>
        </section>

        <!-- Statusmeldungen -->
        <section class="card p-5">
          <h2 class="section-title text-lg mb-3">Statusmeldungen</h2>
          <p class="text-themed-muted leading-relaxed mb-4">
            Fahrzeuge melden ihren aktuellen Zustand über numerische Status-Codes.
            Die Tasten auf dem Statusfeld ändern den Status des Fahrzeugs.
          </p>
          <div class="flex flex-col gap-3">
            <div class="flex items-center gap-3">
              <StatusBadge status="1" />
              <div>
                <strong class="text-themed">Status 1</strong>
                <span class="text-themed-muted"> — Einsatzbereit auf Funk (frei auf Wache)</span>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <StatusBadge status="2" />
              <div>
                <strong class="text-themed">Status 2</strong>
                <span class="text-themed-muted"> — Einsatzbereit auf Wache (Grundstatus)</span>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <StatusBadge status="3" />
              <div>
                <strong class="text-themed">Status 3</strong>
                <span class="text-themed-muted"> — Einsatz übernommen / auf Anfahrt</span>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <StatusBadge status="4" />
              <div>
                <strong class="text-themed">Status 4</strong>
                <span class="text-themed-muted"> — An Einsatzstelle eingetroffen</span>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <StatusBadge status="7" />
              <div>
                <strong class="text-themed">Status 7</strong>
                <span class="text-themed-muted"> — Sprechwunsch mit Transportziel (nur aus Status 4)</span>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <StatusBadge status="8" />
              <div>
                <strong class="text-themed">Status 8</strong>
                <span class="text-themed-muted"> — Am Transportziel eingetroffen (nur aus Status 7)</span>
              </div>
            </div>
          </div>

          <h3 class="text-themed font-bold mt-5 mb-2">Sondersignale</h3>
          <div class="flex flex-col gap-3">
            <div class="flex items-center gap-3">
              <span class="bg-accent text-black font-extrabold uppercase text-sm p-1.5 px-3 rounded min-w-[90px] text-center">0 Blitz</span>
              <span class="text-themed-muted">Dringender Sprechwunsch (Blitzmeldung) — wird sofort in der Leitstelle angezeigt</span>
            </div>
            <div class="flex items-center gap-3">
              <span class="bg-accent text-black font-extrabold uppercase text-sm p-1.5 px-3 rounded min-w-[90px] text-center">5 Spr-W</span>
              <span class="text-themed-muted">Normaler Sprechwunsch — Fahrzeug möchte mit der Leitstelle sprechen</span>
            </div>
          </div>

          <h3 class="text-themed font-bold mt-5 mb-2">Erlaubte Übergänge</h3>
          <p class="text-themed-muted text-sm mb-2">Nicht jeder Status kann aus jedem anderen Status erreicht werden:</p>
          <div class="bg-themed-overlay border border-themed rounded p-3 text-sm font-mono text-themed-muted">
            <div>2 (Wache) → 1, 3</div>
            <div>1 (Funk) → 2, 3</div>
            <div>3 (Anfahrt) → 1, 2, 4</div>
            <div>4 (Einsatzstelle) → 1, 3, 7</div>
            <div>7 (Transport) → 8</div>
            <div>8 (Transportziel) → 1</div>
          </div>
        </section>

        <!-- Leitstelle -->
        <section class="card p-5">
          <h2 class="section-title text-lg mb-3">Leitstelle (Disponent)</h2>
          <p class="text-themed-muted leading-relaxed mb-3">
            Die Leitstelle sieht alle verbundenen Fahrzeuge und verwaltet den Einsatzbetrieb.
            Mehrere Disponenten können gleichzeitig arbeiten — jeder gibt sich oben rechts einen Namen.
          </p>

          <h3 class="text-themed font-bold mt-4 mb-2">Fahrzeuge übernehmen</h3>
          <p class="text-themed-muted leading-relaxed mb-2">
            Jeder Disponent übernimmt Fahrzeuge, für die er zuständig ist.
            Nicht übernommene Fahrzeuge erscheinen in einem eigenen Bereich am Ende der Seite.
          </p>
          <div class="flex gap-2 mb-3">
            <span class="btn bg-primary/80 text-white p-1 px-2.5 text-xs cursor-default">Übernehmen</span>
            <span class="btn bg-danger/80 text-white p-1 px-2.5 text-xs cursor-default">Freigeben</span>
          </div>

          <h3 class="text-themed font-bold mt-4 mb-2">Bereiche in der Übersicht</h3>
          <p class="text-themed-muted leading-relaxed mb-2">
            Die Fahrzeugliste ist in mehrere Bereiche unterteilt, sortiert nach Dringlichkeit:
          </p>
          <div class="flex flex-col gap-2 text-sm">
            <div class="vehicle-group border-t-4 border-t-accent p-2 px-3">
              <span class="text-accent font-bold uppercase tracking-wider">Sprechwünsche</span>
              <span class="text-themed-muted ml-2">— Fahrzeuge mit Blitz (0) oder Sprechwunsch (5)</span>
            </div>
            <div class="vehicle-group border-t-4 border-t-danger p-2 px-3">
              <span class="text-danger font-bold uppercase tracking-wider">Gespräch mit SF</span>
              <span class="text-themed-muted ml-2">— Fahrzeuge, die gerade mit dem Staffelführer sprechen</span>
            </div>
            <div class="vehicle-group border-t-4 border-t-primary p-2 px-3">
              <span class="text-primary font-bold uppercase tracking-wider">Aktion erforderlich (LS)</span>
              <span class="text-themed-muted ml-2">— Fahrzeuge, bei denen die Leitstelle als nächstes dran ist</span>
            </div>
            <div class="vehicle-group p-2 px-3">
              <span class="text-primary font-bold uppercase tracking-wider">Alle Fahrzeuge</span>
              <span class="text-themed-muted ml-2">— Restliche übernommene Fahrzeuge</span>
            </div>
            <div class="vehicle-group border-t-4 border-t-warning p-2 px-3 opacity-70">
              <span class="text-warning font-bold uppercase tracking-wider">Nicht übernommen</span>
              <span class="text-themed-muted ml-2">— Fahrzeuge, die noch keinem Disponenten zugeordnet sind</span>
            </div>
          </div>

          <h3 class="text-themed font-bold mt-4 mb-2">Aktionen pro Fahrzeug</h3>
          <p class="text-themed-muted leading-relaxed mb-2">
            Klicke auf ein Fahrzeug, um es aufzuklappen. Dort kannst du:
          </p>
          <ul class="text-themed-muted leading-relaxed list-disc list-inside flex flex-col gap-1">
            <li>Den <strong class="text-themed">Status manuell setzen</strong> (Tasten 1–4)</li>
            <li>Einen <strong class="text-themed">Einsatz erstellen</strong> — generiert ein Szenario mit Funksprüchen</li>
            <li><strong class="text-themed">Nachrichten senden</strong> an das Fahrzeug</li>
            <li><strong class="text-themed">Notizen</strong> hinterlegen</li>
            <li><strong class="text-themed">Sprechwunsch / Blitz löschen</strong></li>
            <li><strong class="text-themed">Kurzlagemeldung</strong> bestätigen</li>
          </ul>
        </section>

        <!-- Fahrzeug -->
        <section class="card p-5">
          <h2 class="section-title text-lg mb-3">Fahrzeug (Funkrufname)</h2>
          <p class="text-themed-muted leading-relaxed mb-3">
            Als Fahrzeug siehst du ein Tastenfeld, mit dem du Statusmeldungen absetzt.
            Drücke die entsprechende Zahl, um den Status zu wechseln.
          </p>

          <h3 class="text-themed font-bold mt-4 mb-2">Tastenfeld</h3>
          <p class="text-themed-muted text-sm mb-3">
            Das Tastenfeld zeigt 0–9 an. Die aktuelle Statustaste leuchtet grün, Sondersignale orange.
            Nicht erlaubte Übergänge werden vom System ignoriert.
          </p>
          <div class="grid grid-cols-3 gap-2 mx-auto w-full max-w-[200px] mb-4">
            <div class="aspect-square flex items-center justify-center text-sm font-extrabold rounded-xl border-2 keypad-idle">1</div>
            <div class="aspect-square flex items-center justify-center text-sm font-extrabold rounded-xl border-2 bg-success text-white border-success">2</div>
            <div class="aspect-square flex items-center justify-center text-sm font-extrabold rounded-xl border-2 keypad-idle">3</div>
            <div class="aspect-square flex items-center justify-center text-sm font-extrabold rounded-xl border-2 keypad-idle">4</div>
            <div class="aspect-square flex items-center justify-center text-sm font-extrabold rounded-xl border-2 keypad-idle">5</div>
            <div class="aspect-square flex items-center justify-center text-sm font-extrabold rounded-xl border-2 keypad-idle">6</div>
            <div class="aspect-square flex items-center justify-center text-sm font-extrabold rounded-xl border-2 keypad-idle">7</div>
            <div class="aspect-square flex items-center justify-center text-sm font-extrabold rounded-xl border-2 keypad-idle">8</div>
            <div class="aspect-square flex items-center justify-center text-sm font-extrabold rounded-xl border-2 keypad-idle">9</div>
            <div class="aspect-square flex items-center justify-center text-sm font-extrabold rounded-xl border-2 keypad-idle">*</div>
            <div class="aspect-square flex items-center justify-center text-sm font-extrabold rounded-xl border-2 bg-accent text-black border-accent">0</div>
            <div class="aspect-square flex items-center justify-center text-sm font-extrabold rounded-xl border-2 keypad-idle">#</div>
          </div>

          <h3 class="text-themed font-bold mt-4 mb-2">Kurzlagemeldung</h3>
          <p class="text-themed-muted leading-relaxed mb-2">
            Unter dem Tastenfeld kannst du eine vordefinierte Kurzlagemeldung auswählen.
            Diese wird der Leitstelle angezeigt und kann von dort bestätigt werden.
          </p>
          <div class="border border-themed rounded-lg overflow-hidden text-sm">
            <div class="p-2 px-3 bg-themed-alt border-b border-themed">Lage bestä., Maßn. eing.</div>
            <div class="p-2 px-3 bg-info/20 text-info font-bold border-b border-themed">Fehlalarm BMA (ausgewählt)</div>
            <div class="p-2 px-3 bg-themed-alt">Müco, 1 C-Rohr, EstuK</div>
          </div>

          <h3 class="text-themed font-bold mt-4 mb-2">Gespräch mit Staffelführer</h3>
          <p class="text-themed-muted leading-relaxed">
            Über den Button
            <span class="btn btn-info px-2 py-0.5 text-xs cursor-default">Mit SF sprechen</span>
            signalisiert das Fahrzeug, dass es gerade mit dem Staffelführer spricht.
            Die Leitstelle sieht dies und weiß, dass das Fahrzeug vorübergehend nicht auf dem Hauptkanal erreichbar ist.
          </p>
        </section>

        <!-- Staffelführer -->
        <section class="card p-5">
          <h2 class="section-title text-lg mb-3">Staffelführer</h2>
          <p class="text-themed-muted leading-relaxed mb-3">
            Der Staffelführer koordiniert mehrere Fahrzeuge vor Ort. Er kann:
          </p>
          <ul class="text-themed-muted leading-relaxed list-disc list-inside flex flex-col gap-1 mb-3">
            <li><strong class="text-themed">Fahrzeuge übernehmen</strong> — nur übernommene Fahrzeuge können angefordert werden</li>
            <li><strong class="text-themed">Anfrage senden</strong> — das Fahrzeug erhält eine Aufforderung, den Funkkanal zu wechseln</li>
            <li><strong class="text-themed">Funkkanal setzen</strong> — wird bei Anfragen automatisch an die Fahrzeuge übermittelt</li>
            <li><strong class="text-themed">Szenario-Checkliste</strong> bearbeiten</li>
            <li><strong class="text-themed">Nachrichten und Notizen</strong> an Fahrzeuge senden</li>
          </ul>

          <h3 class="text-themed font-bold mt-4 mb-2">Anfrage-Ablauf</h3>
          <div class="flex flex-col gap-2 text-sm text-themed-muted">
            <div class="flex items-center gap-2">
              <span class="font-mono text-themed">1.</span>
              SF klickt <span class="btn btn-primary px-2 py-0.5 text-xs cursor-default">Anfrage</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="font-mono text-themed">2.</span>
              Fahrzeug sieht blinkende Benachrichtigung mit neuem Funkkanal
            </div>
            <div class="flex items-center gap-2">
              <span class="font-mono text-themed">3.</span>
              Fahrzeug bestätigt mit <span class="btn btn-success px-2 py-0.5 text-xs cursor-default">Kanal gewechselt</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="font-mono text-themed">4.</span>
              SF sieht "Spricht" und schließt mit <span class="btn btn-success px-2 py-0.5 text-xs cursor-default">Fertig</span> ab
            </div>
          </div>
        </section>

        <!-- Szenarien -->
        <section class="card p-5">
          <h2 class="section-title text-lg mb-3">Szenarien & Checklisten</h2>
          <p class="text-themed-muted leading-relaxed mb-3">
            Die Leitstelle kann jedem Fahrzeug ein Szenario zuweisen. Szenarien generieren realistische
            Funksprüche, die als Checkliste abgearbeitet werden.
          </p>
          <p class="text-themed-muted leading-relaxed mb-3">
            Jeder Funkspruch zeigt an, wer sprechen muss:
          </p>
          <div class="flex gap-3 mb-3">
            <span class="text-sm font-bold text-primary">LS</span><span class="text-themed-muted text-sm">= Leitstelle spricht</span>
            <span class="text-sm font-bold text-danger">SF</span><span class="text-themed-muted text-sm">= Staffelführer spricht</span>
            <span class="text-sm font-bold text-success">FZ</span><span class="text-themed-muted text-sm">= Fahrzeug (Melder) spricht</span>
          </div>
          <p class="text-themed-muted leading-relaxed mb-3">
            In der Fahrzeugliste wird angezeigt, wer als nächstes dran ist
            (<span class="bg-themed-input border border-themed px-2 py-0.5 rounded text-xs text-themed-muted font-bold">LS</span> oder
            <span class="bg-themed-input border border-themed px-2 py-0.5 rounded text-xs text-themed-muted font-bold">SF</span>).
            Fahrzeuge, bei denen du als nächstes handeln musst, werden in einem eigenen Bereich hervorgehoben.
          </p>
          <p class="text-themed-muted leading-relaxed">
            Ist ein Szenario vollständig abgehakt, kann über
            <span class="btn btn-secondary px-2 py-0.5 text-xs cursor-default">Neuer Einsatz</span>
            ein neues Szenario gestartet werden. Es wird automatisch ein unbenutztes ausgewählt.
          </p>
        </section>

        <!-- Tipps -->
        <section class="card p-5">
          <h2 class="section-title text-lg mb-3">Tipps</h2>
          <ul class="text-themed-muted leading-relaxed list-disc list-inside flex flex-col gap-2">
            <li>Die Seite aktualisiert sich automatisch alle 2 Sekunden. Nach Aktionen wird sofort aktualisiert.</li>
            <li>Codes können durch Klicken kopiert werden — halte die Maus gedrückt, um den Code sichtbar zu machen.</li>
            <li>Unten auf jeder Seite kannst du zwischen <strong class="text-themed">Light Mode</strong> und <strong class="text-themed">Dark Mode</strong> wechseln.</li>
            <li>Mehrere Disponenten/Staffelführer können gleichzeitig arbeiten. Jeder übernimmt seine Fahrzeuge.</li>
            <li>Die Leitstellen-URL kann geteilt werden — andere Disponenten öffnen sie mit einem eigenen Namen.</li>
          </ul>
        </section>

      </div>
    </div>
    <Footer />
  </div>
</template>
