"""Pydantic-Modelle zum Definieren und Laden von Alarm-Szenarien aus JSON.

Die JSON-Dateien enthalten nur Metainformationen. Die Funksprüche werden
daraus generiert.
"""

from typing import Dict, List, Literal, Optional, Union, Annotated
from pydantic import BaseModel, Field
import random


class Einheit(BaseModel):
    """Eine Einheit (z.B. C-Dienst, NEF, RTW)."""
    typ: Literal["FD", "NEF", "RTW"]
    anzahl: int = 1
    kennung: Optional[str] = None # Optional, falls eine spezifische Kennung gewünscht ist

    def _generate_single_name(self) -> str:
        if self.kennung and self.anzahl == 1:
            return self.kennung
        num = random.choice([n for n in range(11, 66) if n % 10 != 0])
        if self.typ == "FD":
            return f"C-Dienst {num}17"
        elif self.typ == "NEF":
            return f"NEF {num}05"
        elif self.typ == "RTW":
            x = random.randint(1, 6)
            return f"RTW {num}00/{x}"
        return "Unbekannte Einheit"

    def generate_names(self) -> List[str]:
        # Wenn eine spezifische Kennung angegeben ist und anzahl==1, diese verwenden
        if self.kennung and self.anzahl == 1:
            return [self.kennung]
        names = set()
        while len(names) < max(1, self.anzahl):
            names.add(self._generate_single_name())
        return list(names)


class FunkEntry(BaseModel):
    actor: Literal["LS", "SF", "FZ"]
    message: Optional[str] = None
    status: Optional[str] = None


class FunkContext(BaseModel):
    fk: str
    ls: str
    einsatz_adresse: str
    einsatz_ortsteil: str
    einsatz_stichwort: str
    enr_counter: int = 1

    def next_enr(self) -> str:
        val = str(self.enr_counter)
        self.enr_counter += 1
        return val


class Lagemeldung(BaseModel):
    """Lagemeldung in der richtigen Reihenfolge (wird für SF geshuffled)."""
    lage: str = "Einsatzstelle unter Kontrolle (EstuK)"
    geraete: Optional[str] = None  # z.B. "1 C-Rohr, 2 PA"
    beschreibung: str  # z.B. "Kellerbrand, Mehrfamilienhaus, Keller voll ausgebrannt"
    verletzte: str = "Keine Verletzten"  # z.B. "4 verletzte Person(en) an RTW übergeben"
    uebergabe: str  # z.B. "Einsatzstelle an Anwohner übergeben" oder "Einsatzstelle an Pol übergeben"


class EigenunfallSchritt(BaseModel):
    """Eigenunfall während der Anfahrt."""
    typ: Literal["eigenunfall"]
    mit_personenschaden: bool
    verletzte: int = 1
    adresse: str  # Unfallort
    ortsteil: str

    def generate_entries(self, ctx: FunkContext) -> List[FunkEntry]:
        e: List[FunkEntry] = []
        if self.mit_personenschaden:
            # Pro Verletzten einen RTW und zusätzlich einen C-Dienst generieren
            rtw_namen = Einheit(typ="RTW", anzahl=max(1, self.verletzte)).generate_names()
            cd_name = Einheit(typ="FD").generate_names()[0]
            rtw_liste = ", ".join(rtw_namen)
            e += [
                FunkEntry(actor="SF", message=f"Melder {ctx.fk} von Staffelführer {ctx.fk}, kommen."),
                FunkEntry(actor="FZ", message=f"Hier Melder {ctx.fk}, kommen."),
                FunkEntry(actor="SF", message=f"Wir hatten einen Unfall mit Personenschaden {self.verletzte}, bitte nachalarmieren."),
                FunkEntry(actor="LS", message=f"Florian {ctx.fk} Blitz, kommen."),
                FunkEntry(actor="FZ", message=f"Hier {ctx.fk} mit Eigenunfall mit Personenschaden, kommen."),
                FunkEntry(actor="LS", message="Wo befinden sie sich?, kommen."),
                FunkEntry(actor="FZ", message=f"{self.adresse} {self.ortsteil}, kommen."),
                FunkEntry(actor="LS", message=f"{self.adresse} {self.ortsteil} so recht? Kommen."),
                FunkEntry(actor="FZ", message="So richtig, kommen."),
                FunkEntry(actor="LS", message="Wie viele Verletzte, kommen."),
                FunkEntry(actor="FZ", message=f"Verletzte: {self.verletzte}, kommen."),
                FunkEntry(actor="LS", message=f"Verstanden, sie dann in Status 4, {rtw_liste} und {cd_name} sind auf dem Weg, {ctx.ls} Ende.", status="4"),
            ]
        else:
            cd_name = Einheit(typ="FD").generate_names()[0]
            e += [
                FunkEntry(actor="SF", message=f"Melder {ctx.fk} von Staffelführer {ctx.fk}, kommen."),
                FunkEntry(actor="FZ", message=f"Hier Melder {ctx.fk}, kommen."),
                FunkEntry(actor="SF", message="Wir hatten einen Unfall ohne Personenschaden, nachalarmieren, kommen."),
                FunkEntry(actor="FZ", message="Wir hatten einen Unfall ohne Personenschaden, kommen."),
                FunkEntry(actor="SF", message="So richtig, Ende"),
                FunkEntry(actor="LS", message=f"Florian {ctx.fk} Blitz, kommen."),
                FunkEntry(actor="FZ", message=f"Hier {ctx.fk} mit Eigenunfall ohne Personenschaden, kommen."),
                FunkEntry(actor="LS", message="Wo befinden sie sich?, kommen."),
                FunkEntry(actor="FZ", message=f"{self.adresse} {self.ortsteil}, kommen."),
                FunkEntry(actor="LS", message=f"{self.adresse} {self.ortsteil} so recht? Kommen."),
                FunkEntry(actor="FZ", message="So richtig, kommen."),
                FunkEntry(actor="LS", message=f"Verstanden, sie dann in Status 4, {cd_name} ist auf dem Weg, {ctx.ls} Ende.", status="4"),
            ]
        return e


class NeueTaetigkeitMitFznSchritt(BaseModel):
    """Neue Tätigkeit mit Fahrzeugnennung während der Anfahrt."""
    typ: Literal["neue_taetigkeit_mit_fzn"]
    ereignis: str  # z.B. "bewusstlose Person", "Brand"
    adresse: str  # Neue Adresse
    ortsteil: str

    def generate_entries(self, ctx: FunkContext) -> List[FunkEntry]:
        e: List[FunkEntry] = [
            FunkEntry(actor="SF", message=f"Melder {ctx.fk} von Staffelführer {ctx.fk}, kommen."),
            FunkEntry(actor="FZ", message=f"Hier Melder {ctx.fk}, kommen."),
            FunkEntry(actor="SF", message=f"Wir haben eine neue Tätigkeit mit Fahrzeugnennung in der {self.adresse} {self.ortsteil}, {self.ereignis}, kommen."),
            FunkEntry(actor="FZ", message=f"Verstanden, neue Tätigkeit mit Fahrzeugnennung in der {self.adresse} {self.ortsteil}, {self.ereignis}, kommen."),
            FunkEntry(actor="SF", message="So richtig, Ende."),
            FunkEntry(actor="LS", message=f"Florian {ctx.fk} Sprechwunsch, kommen."),
            FunkEntry(actor="FZ", message=f"Hier Florian {ctx.fk} mit neuer Tätigkeit ohne Fahrzeugnennung, kommen."),
            FunkEntry(actor="LS", message="Wo befinden sie sich und das Ereignis, kommen."),
            FunkEntry(actor="FZ", message=f"{self.adresse} {self.ortsteil}, {self.ereignis}, kommen."),
            FunkEntry(actor="LS", message=f"{self.adresse} {self.ortsteil}, {self.ereignis} so recht, kommen."),
            FunkEntry(actor="FZ", message="So richtig, kommen."),
            FunkEntry(actor="LS", message=f"Verstanden, Einsatz unter Nummer {ctx.next_enr()} angelegt. Sie dann weiter mit Status 4, {ctx.ls} Ende.", status="4"),
        ]
        # Update Einsatzkontext auf neue Adresse? Das überlässt man dem Aufrufer, hier nur Funksprüche.
        return e


class NeueTaetigkeitOhneFznSchritt(BaseModel):
    """Neue Tätigkeit ohne Fahrzeugnennung während der Anfahrt."""
    typ: Literal["neue_taetigkeit_ohne_fzn"]
    ereignis: str  # z.B. "Baum auf Straße", "Ölspur"
    adresse: str
    ortsteil: str

    def generate_entries(self, ctx: FunkContext) -> List[FunkEntry]:
        return [
            FunkEntry(actor="SF", message=f"Melder {ctx.fk} von Staffelführer {ctx.fk}, kommen."),
            FunkEntry(actor="FZ", message=f"Hier Melder {ctx.fk}, kommen."),
            FunkEntry(actor="SF", message=f"Wir haben eine neue Tätigkeit ohne Fahrzeugnennung in der {self.adresse} {self.ortsteil}, {self.ereignis}, kommen."),
            FunkEntry(actor="FZ", message=f"Verstanden, neue Tätigkeit ohne Fahrzeugnennung in der {self.adresse} {self.ortsteil}, {self.ereignis}, kommen."),
            FunkEntry(actor="SF", message="So richtig, Ende."),
            FunkEntry(actor="LS", message=f"Florian {ctx.fk} Sprechwunsch, kommen."),
            FunkEntry(actor="FZ", message=f"Hier Florian {ctx.fk} mit neuer Tätigkeit ohne Fahrzeugnennung, kommen."),
            FunkEntry(actor="LS", message="Wo befinden sie sich und das Ereignis, kommen."),
            FunkEntry(actor="FZ", message=f"{self.adresse} {self.ortsteil}, {self.ereignis}, kommen."),
            FunkEntry(actor="LS", message=f"{self.adresse} {self.ortsteil}, {self.ereignis} so recht, kommen."),
            FunkEntry(actor="FZ", message="So richtig, kommen."),
            FunkEntry(actor="LS", message=f"Verstanden, {ctx.ls} Ende."),
        ]


class EinsatzstellenkorrekturSchritt(BaseModel):
    """Einsatzstellenkorrektur während der Anfahrt."""
    typ: Literal["einsatzstellenkorrektur"]
    adresse: str  # Neue Adresse (nur Hausnummer anders)
    ortsteil: str

    def generate_entries(self, ctx: FunkContext) -> List[FunkEntry]:
        return [
            FunkEntry(actor="LS", message=f"Florian {ctx.fk}, kommen."),
            FunkEntry(actor="FZ", message=f"Hier Florian {ctx.fk}, kommen."),
            FunkEntry(actor="LS", message="Wir haben eine Einsatzstellenkorrektur, kommen."),
            FunkEntry(actor="FZ", message="Anfangen, kommen."),
            FunkEntry(actor="LS", message=f"{self.adresse} {self.ortsteil}, kommen."),
            FunkEntry(actor="FZ", message=f"{self.adresse} {self.ortsteil}, kommen."),
            FunkEntry(actor="LS", message=f"So richtig, {ctx.ls} Ende."),
            FunkEntry(actor="FZ", message=f"Staffelführer {ctx.fk} von Melder {ctx.fk} kommen."),
            FunkEntry(actor="SF", message=f"Hier Staffelführer {ctx.fk}, kommen."),
            FunkEntry(actor="FZ", message=f"Einsatzstellenkorrektur auf {self.adresse} {self.ortsteil}, kommen."),
            FunkEntry(actor="SF", message=f"Einsatzstellenkorrektur auf {self.adresse} {self.ortsteil} verstanden, kommen."),
            FunkEntry(actor="FZ", message="So richtig, Ende."),
        ]


class AnkommenSchritt(BaseModel):
    """Ankommen ohne Ereignis."""
    typ: Literal["ankommen"]

    def generate_entries(self, ctx: FunkContext) -> List[FunkEntry]:
        return [
            FunkEntry(actor="SF", message=f"Melder {ctx.fk} von Staffelführer {ctx.fk}, kommen."),
            FunkEntry(actor="FZ", message=f"Hier Melder {ctx.fk}, kommen."),
            FunkEntry(actor="SF", message="Wir sind an der Einsatzstelle eingetroffen, kommen."),
            FunkEntry(actor="FZ", message="Wir sind an der Einsatzstelle eingetroffen, kommen."),
            FunkEntry(actor="SF", message="So richtig, Ende.", status="4"),
        ]


class KurzlagemeldungSchritt(BaseModel):
    """Kurzlagemeldung über FMS an der Einsatzstelle."""
    typ: Literal["kurzlagemeldung"]
    text: str  # z.B. "Müco, 1 C-Rohr, EstuK" oder "Fehlalarm BMA"

    def generate_entries(self, ctx: FunkContext) -> List[FunkEntry]:
        return [
            FunkEntry(actor="SF", message=f"Melder {ctx.fk} von Staffelführer {ctx.fk}, kommen."),
            FunkEntry(actor="FZ", message=f"Hier Melder {ctx.fk}, kommen."),
            FunkEntry(actor="SF", message=f"Kurzlagemeldung über FMS {self.text}, kommen."),
            FunkEntry(actor="FZ", message=f"Kurzlagemeldung über FMS {self.text}, kommen."),
            FunkEntry(actor="SF", message="So richtig, Ende."),
        ]


class LagemeldungSchritt(BaseModel):
    """Abschließende Lagemeldung (Mit Lagemeldung)."""
    typ: Literal["lagemeldung"]
    lagemeldung: Lagemeldung

    def generate_entries(self, ctx: FunkContext) -> List[FunkEntry]:
        lm = self.lagemeldung
        teile_sf = [t for t in [lm.lage, lm.geraete or "", lm.beschreibung, lm.verletzte, lm.uebergabe] if t]
        random.shuffle(teile_sf)
        return [
            FunkEntry(actor="SF", message=f"Melder {ctx.fk} von Staffelführer {ctx.fk}, kommen."),
            FunkEntry(actor="FZ", message=f"Hier Melder {ctx.fk}, kommen."),
            FunkEntry(actor="SF", message="Mit Lagemeldung, kommen."),
            FunkEntry(actor="FZ", message="Lage ist, kommen."),
            FunkEntry(actor="SF", message=f"{', '.join(teile_sf)}, kommen."),
            FunkEntry(actor="FZ", message=f"{', '.join(teile_sf)}, kommen."),
            FunkEntry(actor="SF", message="So richtig, Ende.", status="5"),
            FunkEntry(actor="LS", message=f"Florian {ctx.fk} Sprechwunsch, kommen."),
            FunkEntry(actor="FZ", message="Mit Lagemeldung, kommen."),
            FunkEntry(actor="LS", message="Lage ist, kommen."),
            FunkEntry(actor="FZ", message=f"{ctx.einsatz_adresse} {ctx.einsatz_ortsteil}, {lm.lage}{', ' + lm.geraete if lm.geraete else ''}, {lm.beschreibung}, {lm.verletzte}, {lm.uebergabe}, kommen."),
            FunkEntry(actor="LS", message=f"Verstanden, {ctx.ls} Ende."),
            FunkEntry(actor="FZ", message=f"Staffelführer {ctx.fk} von Melder {ctx.fk} kommen."),
            FunkEntry(actor="SF", message=f"Hier Staffelführer {ctx.fk}, kommen."),
            FunkEntry(actor="FZ", message="Lagemeldung abgegeben, kommen."),
            FunkEntry(actor="SF", message="Verstanden, wir wieder status 1 kommen..", status="1"),
            FunkEntry(actor="FZ", message="Status 1 verstanden, Ende.", status="1"),
        ]


class OhneLagemeldungSchritt(BaseModel):
    """Einsatz beendet ohne Lagemeldung."""
    typ: Literal["ohne_lagemeldung"]

    def generate_entries(self, ctx: FunkContext) -> List[FunkEntry]:
        return [
            FunkEntry(actor="SF", message=f"Melder {ctx.fk} von Staffelführer {ctx.fk}, kommen."),
            FunkEntry(actor="FZ", message=f"Hier Melder {ctx.fk}, kommen."),
            FunkEntry(actor="SF", message="Einsatz beendet, wir wieder Status 1, kommen.", status="1"),
            FunkEntry(actor="FZ", message="Status 1 verstanden, kommen.", status="1"),
            FunkEntry(actor="SF", message="So richtig, Ende."),
        ]


class NachalarmierungSchritt(BaseModel):
    """Nachalarmierung an der Einsatzstelle."""
    typ: Literal["nachalarmierung"]
    stichwort: str  # z.B. "Brand 4"
    begruendung: str  # z.B. "Feuer breitet sich aus"

    def generate_entries(self, ctx: FunkContext) -> List[FunkEntry]:
        return [
            FunkEntry(actor="SF", message=f"Melder {ctx.fk} von Staffelführer {ctx.fk}, kommen."),
            FunkEntry(actor="FZ", message=f"Hier Melder {ctx.fk}, kommen."),
            FunkEntry(actor="SF", message=f"Nachalarmierung auf {self.stichwort} {self.begruendung}, kommen."),
            FunkEntry(actor="FZ", message=f"Nachalarmierung auf {self.stichwort} {self.begruendung}, kommen."),
            FunkEntry(actor="SF", message="So richtig, Ende."),
            FunkEntry(actor="LS", message=f"Florian {ctx.fk} Blitz, kommen."),
            FunkEntry(actor="FZ", message=f"Hier Florian {ctx.fk} mit Nachalarmierung auf {self.stichwort}, kommen."),
            FunkEntry(actor="LS", message=f"Begründung für {self.stichwort}, kommen."),
            FunkEntry(actor="FZ", message=f"{self.begruendung}, kommen."),
            FunkEntry(actor="LS", message=f"Verstanden, {ctx.ls} Ende."),
        ]


class FehlalarmLagemeldungSchritt(BaseModel):
    """Lagemeldung bei Fehlalarm BMA."""
    typ: Literal["fehlalarm_lagemeldung"]

    def generate_entries(self, ctx: FunkContext) -> List[FunkEntry]:
        return [
            FunkEntry(actor="SF", message=f"Melder {ctx.fk} von Staffelführer {ctx.fk}, kommen."),
            FunkEntry(actor="FZ", message=f"Hier Melder {ctx.fk}, kommen."),
            FunkEntry(actor="SF", message="Mit Lagemeldung, kommen."),
            FunkEntry(actor="FZ", message="Lage ist, kommen."),
            FunkEntry(actor="SF", message="Fehlalarm BMA, kommen."),
            FunkEntry(actor="FZ", message="Fehlalarm BMA, kommen."),
            FunkEntry(actor="SF", message="So richtig, Ende.", status="5"),
            FunkEntry(actor="LS", message=f"Florian {ctx.fk} Sprechwunsch, kommen."),
            FunkEntry(actor="FZ", message="Mit Lagemeldung, kommen."),
            FunkEntry(actor="LS", message="Lage ist, kommen."),
            FunkEntry(actor="FZ", message=f"{ctx.einsatz_adresse}, {ctx.einsatz_ortsteil}, Fehlalarm BMA, Staffelführer {ctx.fk}, kommen."),
            FunkEntry(actor="LS", message=f"Verstanden, {ctx.ls} Ende."),
            FunkEntry(actor="FZ", message=f"Staffelführer {ctx.fk} von Melder {ctx.fk} kommen."),
            FunkEntry(actor="SF", message=f"Hier Staffelführer {ctx.fk} von Melder {ctx.fk}, kommen."),
            FunkEntry(actor="FZ", message="Lagemeldung abgegeben, kommen."),
            FunkEntry(actor="SF", message="Verstanden, wir wieder status 1 kommen..", status="1"),
            FunkEntry(actor="FZ", message="Status 1 verstanden, Ende.", status="1"),
        ]


# Union aller möglichen Schritte
from typing import Union

Schritt = Union[
    "EigenunfallSchritt",
    "NeueTaetigkeitMitFznSchritt",
    "NeueTaetigkeitOhneFznSchritt",
    "EinsatzstellenkorrekturSchritt",
    "AnkommenSchritt",
    "KurzlagemeldungSchritt",
    "LagemeldungSchritt",
    "OhneLagemeldungSchritt",
    "NachalarmierungSchritt",
    "FehlalarmLagemeldungSchritt",
]


class Einsatz(BaseModel):
    """Ein einzelner Einsatz innerhalb eines Szenarios."""
    stichwort: str
    adresse: str
    ortsteil: str
    einheiten: List[Einheit] = Field(default_factory=list)
    schritte: List[Annotated[Schritt, Field(discriminator="typ")]]
    einsatznummer: Optional[str] = None

    def generate_alarmierung(self, ctx: FunkContext) -> List[FunkEntry]:
        # Einheiten-Namen generieren (FD/NEF im Zusatz erwähnen)
        einheiten_namen: List[str] = []
        for e in self.einheiten:
            einheiten_namen.extend(e.generate_names())
        relevant = [n for n in einheiten_namen if n.startswith("C-Dienst") or n.startswith("NEF")]
        zusatz = f" (zusammen mit {', '.join(relevant)})" if relevant else ""
        enr_str = self.einsatznummer or ctx.next_enr()
        return [
            FunkEntry(actor="LS", message=f"Florian {ctx.fk} mit Blitz, kommen."),
            FunkEntry(actor="FZ", message=f"Hier Florian {ctx.fk}, kommen."),
            FunkEntry(actor="LS", message=f"Neuer Alarm, Nummer {enr_str} {self.stichwort} in der {self.adresse} in {self.ortsteil}{zusatz}, kommen."),
            FunkEntry(actor="FZ", message=f"Einsatznummer {enr_str} {self.stichwort} in der {self.adresse} in {self.ortsteil}{zusatz}, kommen."),
            FunkEntry(actor="LS", message=f"So richtig, {ctx.ls} Ende.", status="3"),
            FunkEntry(actor="FZ", message=f"Staffelführer {ctx.fk} von Melder {ctx.fk} kommen."),
            FunkEntry(actor="SF", message=f"Hier Staffelführer {ctx.fk}, kommen."),
            FunkEntry(actor="FZ", message=f"Neuer Alarm, {self.stichwort} in der {self.adresse} in {self.ortsteil}{zusatz}, Quittung kommen."),
            FunkEntry(actor="SF", message=f"Neuer Alarm, {self.stichwort} in der {self.adresse} in {self.ortsteil}{zusatz}, kommen."),
            FunkEntry(actor="FZ", message="So richtig, Ende."),
        ]


class Scenario(BaseModel):
    """Ein komplettes Szenario bestehend aus einem oder mehreren Einsätzen."""
    name: str
    beschreibung: str
    einsaetze: List[Einsatz]

    def generate_funksprueche(self, fk: str = "FK-01", ls: str = "LS", start_enr: int = 1) -> List[FunkEntry]:
        ctx = FunkContext(
            fk=fk, ls=ls,
            einsatz_adresse="", einsatz_ortsteil="", einsatz_stichwort="",
            enr_counter=start_enr,
        )
        result: List[FunkEntry] = []
        for einsatz in self.einsaetze:
            # Einsatzkontext aktualisieren
            ctx.einsatz_adresse = einsatz.adresse
            ctx.einsatz_ortsteil = einsatz.ortsteil
            ctx.einsatz_stichwort = einsatz.stichwort
            # Alarmierung
            result.extend(einsatz.generate_alarmierung(ctx))
            # Schritte delegiert generieren
            for schritt in einsatz.schritte:
                gen = getattr(schritt, "generate_entries", None)
                if callable(gen):
                    result.extend(gen(ctx))
        return result
