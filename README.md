# 🎁 De Grote Sinterklaas Spellenavond — Sintspel 2.1

Een lokale, interactieve familiespelshow. De route **`/screen`** gebruikt een aparte, groot weergegeven TV-layout voor 1440p en 4K met grotere opdrachten, jaartallen, kaarten, timers, het rad en de scores. Zet de TV-browser bij voorkeur in volledig scherm (F11) met 100% zoom; de laptop en telefoons blijven ongewijzigd. De **laptop** draait de spelserver en is de spelleider; de **TV** toont het spelrad, de kaarten, animaties en uitslagen; **vier telefoons** gebruiken dezelfde wifi voor geheime antwoorden en stemmingen. Geen cloudserver, database-abonnement of externe hosting nodig.

## Starten

1. Download de repository als ZIP of gebruik `git clone` en open de map.
2. Installeer Python 3.10 of nieuwer als dat nog niet is gebeurd.
3. Start op Windows `start.bat`; op Mac/Linux `./start.sh` of `python3 server.py`.
4. Open op de **serverlaptop** `http://127.0.0.1:8765/host`. De lokale server opent automatisch de beveiligde spelleiderlink. Je kunt ook de volledige link uit het terminalvenster gebruiken.
5. Open `/screen` op de TV. De TV toont een grote **QR-code voor spelers**. Scan deze met de telefooncamera; de spelcode is dan al ingevuld en iedereen kiest alleen nog zijn eigen naam. Handmatig `/play` openen en de code invullen kan ook. Tijdens de hele spelavond blijft een **kleine aanmeld-QR-code rechtsonder op het TV-scherm** zichtbaar, ook bij het rad, minigames, uitslagen en de cadeauverdeling. Na het per ongeluk sluiten of herladen van de telefoonpagina kun je opnieuw scannen; dezelfde browser herkent de eerder verbonden speler via het lokaal bewaarde aanmeldtoken. Gebruikt iemand een andere telefoon of browser, dan kan de spelleider die plek in de zijbalk met **Ontkoppel** vrijgeven.
6. Stel de namen en het aantal cadeaus in, verzamel de persoonlijke weetjes, en klik op **Start de spelshow**. Iedere gewonnen minigame levert per winnaar één cadeau op; reken grofweg op 3 à 4 minigames per uur bij het kiezen van het aantal cadeaus per speler.
7. Selecteer op de TV **Geluid aanzetten** om de alarmgeluiden van het verrassingsspel hoorbaar te maken. Zo nodig wordt hiervoor eerst een klik op de TV-browser gevraagd.

**Let op:** houd de hostlink met `?key=...` privé. Maak geen poort van de lokale server openbaar via de router. Bij updates de server afsluiten en opnieuw starten.

## Spellen

**De host bepaalt het tempo.** Geen enkele ronde wacht verplicht op vier antwoorden of stemmen: de spelleider kan een vraag of stemming ook met nul, één of twee deelnemers onthullen. Ontbrekende antwoorden krijgen geen punten. Bij Kaartenduel kunnen spelers die niet hebben gekozen niet per ongeluk winnen. Ook de boodschappenronde kan zonder vier ingediende lijstjes worden afgesloten. Dit maakt testen met één of twee telefoons mogelijk; op pakjesavond wacht de host gewoon op iedereen. Bij Wie van de 3? kan de host zonder keuze naar de volgende ronde gaan.

Het rad toont het gekozen spel **pas nadat** de draai-animatie stopt; daarna gaat de show verder naar het spel.

Het spelrad heeft **acht** vakken: zeven minigames en het intermezzo Pepernotenpong. Na elk spel verdwijnt dat vak; wanneer alle acht geweest zijn, begint een nieuwe cyclus. De spelshow loopt door tot alle ingestelde cadeaus zijn verdeeld.

| Spel | Verloop |
|---|---|
| Muziek Classic | Acht vragen. Spelers kiezen om de beurt makkelijk (1 punt), gemiddeld (2 punten) of moeilijk (4 punten). De geheime muziekkaart moet links, midden of rechts tussen twee zichtbare referentiekaarten worden geplaatst. Makkelijk: het geheime nummer ligt minstens 10 jaar van beide referenties. Gemiddeld: 4–8 jaar, binnen een periode van 25 jaar. Moeilijk: 1–3 jaar, alle drie de kaarten binnen 12 jaar. |
| Muziek Quiz | Acht nummers. Spelers kiezen om de beurt hun muzikale era. Een vraagtypenrad bepaalt artiest, titel, jaartal ±5, jaartal ±3 of vóór/vanaf een rond referentiejaar. Elk goed antwoord is één punt. |
| Quiplash | Vier grappige stellingen. Iedereen geeft een eigen antwoord; daarna stemt iedereen op een ander. De meeste stemmen levert één punt op; bij gelijkstand ieder één punt. |
| Wie van de 3? | Vier persoonlijke waargebeurde verhalen. Iedereen is één keer onderzoeker en mag maximaal tien vragen stellen aan de drie andere spelers om de eigenaar te achterhalen. Welk verhaal bij welke onderzoeker hoort, wordt willekeurig geloot (nooit je eigen verhaal). Goed: drie punten; fout: de drie anderen ieder één punt. Identiteiten worden pas aan het einde onthuld. Elk verhaal wordt één keer gebruikt: komt het spel later terug, dan vult iedereen eerst een nieuw weetje in. Tot die tijd slaat het rad dit spel over. |
| Yahtzee-sprint | Acht dobbelrondes met vijf **echte** dobbelstenen: hoogste som, meest gelijke dobbelstenen, meest van een bepaald getal en langste straat. Een Yahtzee levert altijd drie bonuspunten op; de gewone opdracht wordt daarna door de anderen uitgevochten om één punt. |
| Kaartenduel | Acht deals met vier kaarten uit een gewoon spel van 52 (zonder jokers). Voorspel rood/zwart, hoger/lager, binnen/buiten en de kaartsoort. Alleen goede voorspellers gaan door. Laatste overblijver of alle gelijk geëindigde spelers krijgen één punt. |
| Verboden woord | Acht beurten van één minuut; iedereen omschrijft twee keer. De omschrijver ziet het geheime woord en drie verboden woorden op de eigen telefoon. De rest typt antwoorden; bij een goede gok verdient zowel de gokker als de omschrijver punten. Omdat de spelleider meespeelt, staat het woord niet op het hostscherm; met **👁 Toon woord** kan de spelleider het bewust bekijken, bijvoorbeeld als de telefoon van de omschrijver uitvalt. |
| Pepernotenpong | Intermezzo om even in beweging te komen. Iedereen gooit om de beurt drie pepernoten naar bekertjes; onder elk bekertje ligt een klein cadeautje. Raak = dat bekertje optillen en het cadeautje houden. De app toont de volgorde en wiens beurt het is; treffers worden niet geteld en de cadeauzak blijft ongemoeid. |

### Verrassingsspel: Boodschappenlijst

Dit spel staat **niet op het rad**. Bij de overgang naar spel twee of drie gaat een rood alarm af; de TV toont twintig boodschappen gedurende zestig seconden. Na twee tot vier reguliere minigames onderbreekt opnieuw een alarm de show. Iedereen krijgt drie minuten om de boodschappen op de telefoon te noteren. Eén punt per uniek correct item; enkelvoud en meervoud tellen allebei (appel/appels, ei/eieren). De host controleert de uitslag vóór de cadeau-uitdeling.

## Cadeauregels

- De speler(s) met de hoogste score van de minigame winnen. Bij een gelijke hoogste score winnen ze allemaal; scoort iedereen 0 punten, dan wint niemand.
- Iedere winnaar kiest **één cadeau** uit de zak: een eigen cadeau, zolang die er nog tegoed heeft.
- Heeft een winnaar al zijn eigen cadeaus, dan kiest hij een cadeau voor een ander. De app toont dan de spelers met de minste cadeaus.
- Zijn er minder cadeaus over dan winnaars, dan kiezen de winnaars met de minste cadeaus eerst. Het spel eindigt zodra de volledige voorraad is verdeeld.
- Een verkeerd uitgegeven cadeau kan via **Laatste cadeau terugdraaien** worden hersteld, ook direct na het laatste cadeau van een ronde, tot het volgende spel begint.

## Muziekkaarten toevoegen

De app gebruikt een collectie met vier gegevens per kaart: de oorspronkelijke QR-inhoud (een URL), de **officiële artiestennaam**, de **officiële titel** en het **releasejaar**. Het kaartmateriaal zelf wordt niet als afbeelding gedigitaliseerd; de server genereert bij het afspelen een nieuwe QR-code met dezelfde informatie.

In het instelscherm kun je een CSV importeren met regels in deze volgorde:

```csv
"https://voorbeeld.invalid/001","Voorbeeldartiest","Voorbeeldnummer",1995
```

De URL hierboven is fictief. De app accepteert ook meerdere regels en controleert op dubbele URL's. Bestaande kaarten uit `party-state.json` blijven behouden bij een update.

De repository bevat nu **130 gecontroleerde muziekkaarten** in `data/music-library.json`. Deze laden automatisch bij het opstarten, zonder CSV-import. Twee kaarten zijn uitgesloten: één vanwege een QR-code die een ander lied afspeelt en één vanwege regionale onbeschikbaarheid van het nummer in Apple Music. Eerder lokaal geïmporteerde kaarten worden behouden; de meegeleverde bibliotheek corrigeert verouderde artiest-, titel- en jaartalgegevens van overeenkomstige kaarten. Nieuwe kaarten kun je nog steeds via CSV importeren.

Op 10 november is de collectie met **24 extra kaarten** uitgebreid, waaronder negen nummers van 2020 of later. Op verzoek blijven bij **Watermelon Sugar** zowel kaartjaar als quizjaar op **2020**. Bij **Bad Habits** staat het kaartjaar op **2024**, terwijl het quizjaar is gecorrigeerd naar **2021**.

Per meegeleverde kaart bewaren we zowel `card_year` (jaar op de fysieke kaart) als `year` (het gecontroleerde quizjaar). Voor de quiz gebruikt de app `year`. Bij de QR-weergave blijft de oorspronkelijke gescande tekst exact intact, ook als de QR-inhoud met `www.` begint en geen `https://` bevat.

De muziekspellen tonen een duidelijke melding als er niet genoeg geschikte kaarten zijn.

## Antwoordcontrole

De muziektitels en artiestennamen worden in hun officiële spelling getoond. Bij het antwoorden is de vergelijking **niet hoofdlettergevoelig**, negeert accenten en gebruikelijke leestekens, behandelt `&`, `and` en `en` gelijkwaardig, staat `the` vooraan bij artiesten toe of weg, en herkent beperkte typfouten en ingestelde aliassen. Een van meerdere artiesten is geldig. Artiest en titel krijgen suggesties uit de **hele** muziekbibliotheek, vanaf drie ingetypte tekens; vrij typen blijft mogelijk.

Bij de einduitslag kan de host foutgerekende antwoorden alsnog goedkeuren of eerdere beoordelingen aanpassen. Pas na **Uitslag bevestigen** begint de cadeau-uitdeling. Bevestigde alternatieve muziekantwoorden kunnen worden onthouden zonder de officiële weergavenaam te wijzigen.

## Voorkomen dat de spelavond vastloopt

Op de **hostlaptop** staat rechts onderin een aparte noodbediening, onafhankelijk van de gewone spelinterface. **Terug naar het rad** breekt het huidige onderdeel direct af, zonder bevestigingsdialoog en zonder eerder uitgedeelde cadeaus te wissen. **Spel uitschakelen** vraagt bevestiging, sluit een probleemspel af en haalt het **voor de rest van de lopende avond** uit alle volgende radcycli. Spellen kun je vanaf het rad via **Spellen beheren** ook vooraf uitschakelen of later opnieuw inschakelen. Als alle zeven spellen uitstaan, kun je vanuit dit menu weer een spel inschakelen.

Het rad mag beurtelings door de vier spelers **vanaf hun eigen telefoon** worden gedraaid. De beurt wisselt na een geslaagde draai; de host kan altijd namens een speler draaien als diens telefoon niet beschikbaar is. De noodstop kan ook een vastgelopen cadeau-uitdeling of boodschappenfase afbreken. Reeds gegeven cadeaus blijven staan; nog niet gegeven cadeaus in die uitdeling worden overgeslagen. Bij het overslaan van een vastgelopen boodschappenfase wordt de verrassing voor deze avond afgesloten.

**Nieuwe spelavond** (zijbalk van de host) wist scores, cadeaustand, weetjes en telefoonkoppelingen, zodat een testronde niet doorwerkt in de echte avond. Namen, aantallen cadeaus en de muziekbibliotheek blijven bewaard.

## Opslag, netwerk en updates

De server bewaart voortgang, telefoonverbindingen, punten, cadeauverdeling en de stand van het verrassingsspel in `party-state.json` (lokaal; niet committen). Is dat bestand beschadigd, dan wordt het niet overschreven maar bewaard als `party-state.beschadigd-<datum>.json`. Houdt een virusscanner of OneDrive het bestand even vast, dan probeert de server het opslaan opnieuw; mislukt het toch, dan wordt de actie volledig teruggedraaid en zie je een melding. De beheerlink wordt beveiligd met `.host-key`. Ook de bestaande kaartencollectie in de lokale spelstand blijft geladen.

**Bewaar** `party-state.json` en `.host-key` bij een software-update. Bij een ZIP-update kun je de nieuwe code uitpakken en deze bestanden terugzetten. `git pull` laat door `.gitignore` uitgesloten gebruikersbestanden normaal ongemoeid.

Bij foutmeldingen controleer je eerst of je de volledige hostlink gebruikt, alle apparaten op hetzelfde wifinetwerk staan en de Windows-firewall toegang op het privénetwerk toestaat.

### Bij een vastlopend laadscherm

De app toont nu de concrete JavaScript- of serverfout in plaats van onbeperkt op "klaarzetten" te blijven staan. Gebruik **Opnieuw proberen** of ververs de pagina; je hoeft de opgeslagen spelgegevens niet te verwijderen. De onafhankelijke hostnoodknoppen komen alleen tevoorschijn wanneer de spelshow werkelijk is begonnen. De JavaScript- en CSS-bestanden worden bij nieuwe versies opnieuw geladen.

## Technische tests

De spelregels, de cadeauverdeling en de muziekbibliotheek zijn te testen met:

```bash
python tests/test_show_v2.py -v
```

```bash
python tests/test_hitster.py -v
```

De HTTP-rooktest heeft een aparte, draaiende server nodig (die test wist de spelstand van die server):

```bash
PARTY_PORT=8766 python server.py
```

```bash
PARTY_PORT=8766 python tests/test_v2_http.py
```

## Ontwerp

De TV- en hostschermen volgen het Figma-ontwerp *Sintspel 2.0 — UI Design*. De speelkaarten (`static/cards.svg`, een publiek-domein kaartspel) en de kaartrug (`static/card-back.svg`) komen uit dat bestand.
