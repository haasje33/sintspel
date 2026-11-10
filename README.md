# 🎁 De Grote Sinterklaas Spellenavond — Sintspel 2.0

Een lokale, interactieve familiespelshow. De **laptop** draait de spelserver en is de spelleider; de **TV** toont het spelrad, de kaarten, animaties en uitslagen; **vier telefoons** gebruiken dezelfde wifi voor geheime antwoorden en stemmingen. Geen cloudserver, database-abonnement of externe hosting nodig.

## Starten

1. Download de repository als ZIP of gebruik `git clone` en open de map.
2. Installeer Python 3.10 of nieuwer als dat nog niet is gebeurd.
3. Start op Windows `start.bat`; op Mac/Linux `./start.sh` of `python3 server.py`.
4. Open op de **serverlaptop** `http://127.0.0.1:8765/host`. De lokale server opent automatisch de beveiligde spelleiderlink. Je kunt ook de volledige link uit het terminalvenster gebruiken.
5. Open `/screen` op de TV en `/play` op vier telefoons, via het netwerkadres uit het terminalvenster.
6. Stel de namen en het aantal cadeaus in (standaard negen per speler), verzamel de persoonlijke weetjes, en klik op **Start de spelshow**.
7. Selecteer op de TV **Geluid aanzetten** om de alarmgeluiden van het verrassingsspel hoorbaar te maken. Zo nodig wordt hiervoor eerst een klik op de TV-browser gevraagd.

**Let op:** houd de hostlink met `?key=...` privé. Maak geen poort van de lokale server openbaar via de router. Bij updates de server afsluiten en opnieuw starten.

## Spellen

Het spelrad heeft **zeven** vakken. Na elke minigame verdwijnt dat vak; wanneer alle zeven geweest zijn, begint een nieuwe cyclus. De spelshow loopt door tot alle ingestelde cadeaus zijn verdeeld.

| Spel | Verloop |
|---|---|
| Muziek Classic | Acht vragen. Spelers kiezen om de beurt makkelijk (1 punt), gemiddeld (2 punten) of moeilijk (4 punten). De geheime muziekkaart moet links, midden of rechts tussen twee zichtbare referentiekaarten worden geplaatst. |
| Muziek Quiz | Acht nummers. Spelers kiezen om de beurt hun muzikale era. Een vraagtypenrad bepaalt artiest, titel, jaartal ±5, jaartal ±3 of vóór/vanaf een rond referentiejaar. Elk goed antwoord is één punt. |
| Quiplash | Vier grappige stellingen. Iedereen geeft een eigen antwoord; daarna stemt iedereen op een ander. De meeste stemmen levert één punt op; bij gelijkstand ieder één punt. |
| Wie van de 3? | Vier persoonlijke waargebeurde verhalen. Iedereen is één keer onderzoeker en mag maximaal tien vragen stellen aan de drie andere spelers om de eigenaar te achterhalen. Goed: drie punten; fout: de drie anderen ieder één punt. Identiteiten worden pas aan het einde onthuld. |
| Yahtzee-sprint | Acht dobbelrondes met vijf **echte** dobbelstenen: hoogste som, meest gelijke dobbelstenen, meest van een bepaald getal en langste straat. Een Yahtzee levert altijd drie bonuspunten op; de gewone opdracht wordt daarna door de anderen uitgevochten om één punt. |
| Kaartenduel | Acht deals met vier digitale kaarten. Voorspel rood/zwart, hoger/lager, binnen/buiten en de kaartsoort. Alleen goede voorspellers gaan door. Laatste overblijver of alle gelijk geëindigde spelers krijgen één punt. |
| Verboden woord | Acht beurten van één minuut; iedereen omschrijft twee keer. De omschrijver ziet het geheime woord en drie verboden woorden op de eigen telefoon. De rest typt antwoorden; bij een goede gok verdient zowel de gokker als de omschrijver punten. |

### Verrassingsspel: Boodschappenlijst

Dit spel staat **niet op het rad**. Bij de overgang naar spel twee of drie gaat een rood alarm af; de TV toont twintig boodschappen gedurende zestig seconden. Na twee tot vier reguliere minigames onderbreekt opnieuw een alarm de show. Iedereen krijgt drie minuten om de boodschappen op de telefoon te noteren. Eén punt per uniek correct item. De host controleert de uitslag vóór de cadeau-uitdeling.

## Cadeauregels

- De speler(s) met de hoogste totaalscore van de minigame winnen **allemaal**.
- Iedere winnaar mag maximaal **twee cadeaus** uit de zak laten pakken: één voor zichzelf, zolang die nog eigen cadeaus tegoed heeft, en één voor een ander.
- Als een winnaar zelf klaar is, gaan beide keuzes naar anderen. De app laat alleen ontvangers met nog openstaande cadeaus zien; bij cadeaukeuzes voor anderen krijgen spelers met de laagste cadeaustand voorrang.
- Zijn er minder cadeaus over dan mogelijke cadeaukeuzes, dan eindigt het spel zodra de volledige voorraad is verdeeld.
- Een verkeerd uitgegeven cadeau kan via **Laatste cadeau terugdraaien** worden hersteld.

## Muziekkaarten toevoegen

De app gebruikt een collectie met vier gegevens per kaart: de oorspronkelijke QR-inhoud (een URL), de **officiële artiestennaam**, de **officiële titel** en het **releasejaar**. Het kaartmateriaal zelf wordt niet als afbeelding gedigitaliseerd; de server genereert bij het afspelen een nieuwe QR-code met dezelfde informatie.

In het instelscherm kun je een CSV importeren met regels in deze volgorde:

```csv
"https://voorbeeld.invalid/001","Voorbeeldartiest","Voorbeeldnummer",1995
```

De URL hierboven is fictief. De app accepteert ook meerdere regels en controleert op dubbele URL's. Bestaande kaarten uit `party-state.json` blijven behouden bij een update.

Een gecontroleerde basisbibliotheek kan later afzonderlijk in de repository worden opgenomen. Totdat die beschikbaar is, werkt de **CSV-import** zoals voorheen. De muziekspellen tonen een duidelijke melding als er niet genoeg geschikte kaarten zijn.

## Antwoordcontrole

De muziektitels en artiestennamen worden in hun officiële spelling getoond. Bij het antwoorden is de vergelijking **niet hoofdlettergevoelig**, negeert accenten en gebruikelijke leestekens, behandelt `&`, `and` en `en` gelijkwaardig, staat `the` vooraan bij artiesten toe of weg, en herkent beperkte typfouten en ingestelde aliassen. Een van meerdere artiesten is geldig. Artiest en titel krijgen suggesties uit de **hele** muziekbibliotheek, vanaf drie ingetypte tekens; vrij typen blijft mogelijk.

Bij de einduitslag kan de host foutgerekende antwoorden alsnog goedkeuren of eerdere beoordelingen aanpassen. Pas na **Uitslag bevestigen** begint de cadeau-uitdeling. Bevestigde alternatieve muziekantwoorden kunnen worden onthouden zonder de officiële weergavenaam te wijzigen.

## Opslag, netwerk en updates

De server bewaart voortgang, telefoonverbindingen, punten, cadeauverdeling en de stand van het verrassingsspel in `party-state.json` (lokaal; niet committen). De beheerlink wordt beveiligd met `.host-key`. Ook de bestaande kaartencollectie in de lokale spelstand blijft geladen.

**Bewaar** `party-state.json`, `.host-key` en eventuele eigen audiobestanden bij een software-update. Bij een ZIP-update kun je de nieuwe code uitpakken en deze bestanden terugzetten. `git pull` laat door `.gitignore` uitgesloten gebruikersbestanden normaal ongemoeid.

Bij foutmeldingen controleer je eerst of je de volledige hostlink gebruikt, alle apparaten op hetzelfde wifinetwerk staan en de Windows-firewall toegang op het privénetwerk toestaat.

## Technische tests

De pure spelregels zijn te testen met:

```bash
python tests/test_show_v2.py -v
```

De bestaande HTTP-rooktest is gebouwd voor de vorige spelversie; de nieuwe spelmotor gebruikt een nieuwe reeks `v2_`-acties en wordt afzonderlijk getest.

De toepassing is bedoeld voor een besloten privésessie. Voeg alleen content toe waarvan je de vereiste gebruiksrechten hebt; openbaar publiceren van de repository geeft op zichzelf geen rechten op bronmateriaal.
