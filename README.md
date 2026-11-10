# 🎁 De Grote Sinterklaas Spellenavond

Een lokaal, interactief partyspel voor **vier volwassenen**, met een eigen spelrad op de TV en een eigen antwoordscherm op vier telefoons. De feestavond gebruikt jullie eigen Hitster-, Party & Co-, Yahtzee-, Pictionary-, Rummikub- en kaartspellen. Geen betaald abonnement of extra bordspel nodig.

## Snel starten vanuit GitHub

1. Download de repository met **Code → Download ZIP** op GitHub, of voer `git clone https://github.com/haasje33/sintspel.git` uit.
2. Open de uitgepakte map `sintspel` (of de gekloonde repository).
3. Start op Windows met **`start.bat`**, of op macOS/Linux met `python3 server.py`.
4. Open de Host-, TV- en telefoonlinks die in het terminalvenster verschijnen.

**GitHub Pages is bewust niet ingeschakeld.** Dit is een lokale multiplayer-app; de laptop draait de server en de spelers verbinden via hetzelfde wifinetwerk. Er is geen externe hosting of database nodig.

## Wat heb je nodig?

- **Eén Windows-, Mac- of Linux-computer** (de spelserver en spelleider), met **Python 3.10 of nieuwer**. Python is gratis verkrijgbaar op [python.org](https://www.python.org/downloads/).
- **Vier telefoons** met een webbrowser op dezelfde wifi als de computer.
- **Een TV** met een browser, of een laptop die naar de TV kan casten of aansluiten.
- Jullie fysieke spellen, pen en papier, en de zak met cadeautjes.

**Er zijn geen extra Python-pakketten nodig.** Ook de QR-code wordt volledig lokaal gemaakt.

## Starten op Windows

1. Open de projectmap op je computer (na het downloaden of clonen van de GitHub-repository).
2. Dubbelklik op **`start.bat`**. Zie je 'Python not found'? Installeer Python 3.10+ en vink bij de installatie *Add Python to PATH* aan.
3. Er verschijnt een zwart venster met drie links: **Host/laptop**, **TV-scherm** en **Telefoons**, plus een viercijferige spelcode.
4. Open de volledige **Host/laptop-link** op je computer. Alleen deze link heeft de beheerrechten.
5. Zet vier spelersnamen klaar. Ken je het exacte aantal ingepakte cadeaus per persoon, vul die dan in; anders laat je alle vier aantallen op `0`.
6. Open de **TV-scherm-link** op de TV (of projecteer die tab vanaf de computer).
7. Iedereen opent de **Telefoons-link**, kiest de eigen naam en voert de viercijferige code in.
8. Klik op **Start de spelshow** en daarna **Draai aan het rad**. Wil je Hitster testen zonder te wachten, gebruik dan op de hostpagina **Minigame direct kiezen → Hitster → Start gekozen minigame**.
9. Via **Annuleer minigame (zonder cadeau)** kom je terug bij het rad zonder punten of cadeaus uit te delen. Bij een rechtstreeks gekozen minigame wordt ook de eerdere selectievolgorde en Hitster-gebruiksgeschiedenis hersteld.

**Mac/Linux:** open Terminal in de uitgepakte map en voer `python3 server.py` uit. Of gebruik `./start.sh`.

**Windows-firewall:** bij de eerste start kan Windows vragen of Python toegang tot het netwerk mag hebben. Sta alleen toegang op **privénetwerken** toe. Gebruik geen openbaar wifi-netwerk en open geen poort op je router naar het internet.

## Zo werkt de avond

- Het digitale rad kiest een van **elf minigames**. Elke ronde duurt ongeveer 3–7 minuten. De spelleider kan tussen rondes ook rechtstreeks een spel kiezen.
- De spelleider start de opdracht, onthult eventueel het antwoord en kiest bij een fysiek duel de winnaar.
- De app telt de meeste digitale uitslagen zelf. Bij een gelijke eindstand wordt met een **echte dobbelsteen** beslist.
- **De winnaar mag een cadeautje kiezen voor zichzelf of iemand anders**, maar alleen uit de spelers met de **laagste huidige cadeaustand**. Daardoor krijgt iedereen eerst één, dan twee, dan drie cadeaus, enzovoort.
- Als er per persoon een verschillend aantal cadeaus is ingevoerd, stopt de app met iemand kiezen zodra diens cadeaus allemaal op zijn.
- Klik pas op een naam als het cadeau echt gepakt is. Verkeerd geklikt? Kies **Laatste cadeau terugdraaien**.
- De volgende ronde begint na de cadeau-uitdeling. Met **Zak leeg · afsluiten** sluit je handmatig af (of automatisch wanneer alle ingestelde cadeaus zijn uitgedeeld).

## Elf minigames

| Spelrad-vak | Wat doe je? | Benodigd | Richttijd |
|---|---|---|---|
| 🎵 Hitster | 3 muziekfragmenten: iedereen raadt jaartal en eventueel artiest via de telefoon | Hitster + officiële app; óf eigen audio | 5–7 min |
| 🎯 Schat & gok | 3 schattingsvragen; dichtstbijzijnde krijgt 3 punten, tweede 1 | Alleen telefoons | 3–5 min |
| 💬 Party & Co | 2 grappige vragen, antwoorden op telefoon, anoniem stemmen op de leukste | Alleen telefoons | 4–6 min |
| 👀 Wie van ons? | 3 uitspraken: ieder stemt op een familielid; stemmen op de populairste keuze levert punten op | Alleen telefoons | 3–5 min |
| 🎨 Pictionary | Iedereen tekent één geheim woord; anderen raden op hun telefoon | Papier en stiften | 5–7 min |
| 🎭 Uitbeelden | Iedereen beeldt één geheim woord uit; anderen raden via hun telefoon | Geen | 5–7 min |
| 🤫 Verboden woord | Iedereen omschrijft een woord zonder drie verboden woorden te noemen | Geen | 5–7 min |
| 🎲 Yahtzee-sprint | Korte dobbelsteenuitdaging, hoogste score wint | Yahtzee / vijf dobbelstenen | 3–5 min |
| 🧩 Rummikub-race | Iedereen puzzelt met dezelfde open stenen; meeste geldige combinaties wint | Rummikub | 3–5 min |
| 🃏 Kaartenduel | Kort kaartspel zoals eenentwintigen, hoogste kaart of hoger/lager | Kaartspel | 3–5 min |
| 🚗 Levensweg | Originele, absurdistische levensdilemma's met stemmen op de telefoon | Alleen telefoons | 4–6 min |

De volgorde is **verrassend maar gevarieerd**: het rad kiest iedere soort eerst één keer voordat het dezelfde mogelijkheden opnieuw gebruikt. Het probeert bovendien lange reeksen van dezelfde soort uitdaging te vermijden. Creatieve opdrachten zijn **nieuw geschreven** en geen digitale kopieën van de Party & Co-kaarten.

### 🎵 Belangrijk over Hitster en automatische muziek

Met een gewone fysieke Hitster-kaart kan deze eigen app **niet** de QR-code van Hitster uitlezen en direct het bijbehorende nummer op Spotify afspelen. De officiële Hitster-app is daarvoor de praktische, ondersteunde route: een van jullie scant de kaart en speelt de muziek af via een speaker. Iedereen voert zijn of haar gok in op de eigen telefoon, waarna de spelleider het goede jaar en eventueel de artiest invoert.

Je kunt ook **je eigen audiobestanden** voorbereiden: bij de hostinstellingen upload je MP3, WAV, OGG of M4A (max. 20 MB per bestand), met titel, artiest en jaar. In dat geval kiest de app de tracks automatisch uit de lokale muziekbank en kan het TV-scherm het fragment afspelen zonder de metadata te tonen. Browsers kunnen automatisch afspelen blokkeren; gebruik dan de knop **Speel muziek**. Upload alleen audio die je mag gebruiken en verspreid deze lokale server niet op internet.

Een Spotify Web Playback-integratie zou meer vereisen, waaronder OAuth, een geschikte account en extra ontwikkelwerk. Deze versie doet dat niet en belooft dus geen automatische Spotify-weergave van jullie Hitster-deck.

### 👩‍👦 Geschikt voor verschillende leeftijden

- Geen afvalrondes: iedereen doet steeds mee.
- Ruime tijd voor tekenen, uitbeelden en omschrijven; géén snelle reactietoets of reflexspel.
- Muziek, grappige antwoorden, kennis, tactiek en geluk wisselen af.
- Bij Pictionary/uitbeelden krijgt alleen de uitvoerende speler het geheime woord op diens telefoon. Het TV-scherm verklapt niets.
- Je kunt het rad gewoon een avond lang blijven draaien of stoppen wanneer de zak leeg is.

## Problemen oplossen

**Telefoons kunnen de link niet openen:** controleer of alle apparaten op hetzelfde wifi-netwerk zitten. Bezoek op de computer `ipconfig` (Windows) of je netwerkconfiguratie en gebruik het **IPv4-adres van de computer**, gevolgd door `:8765/play`; bijvoorbeeld `http://192.168.1.20:8765/play`. Het werkelijke adres kan anders zijn. Schakel zo nodig VPN uit en controleer de privéfirewall.

**Het verkeerde IP-adres verschijnt op de startpagina (bijvoorbeeld door een VPN):** start de server met de omgevingsvariabele `PARTY_IP` ingesteld op het lokale IPv4-adres. Op Windows in Opdrachtprompt: `set PARTY_IP=192.168.1.20` en daarna `py -3 server.py`. Op macOS/Linux: `PARTY_IP=192.168.1.20 python3 server.py`. Vervang het voorbeeldadres door je eigen LAN-adres.

**Smart TV heeft geen geschikte browser:** open de `/screen`-pagina op de laptop en cast die tab of gebruik een videokabel. De laptop kan de `/host`-pagina in een ander browservenster houden.

**Iemand zit vast op 'plek bezet':** klik als host bij de betreffende speler op **Ontkoppel telefoon** in de pakjesstand. Diegene kan zich daarna op een ander toestel of in dezelfde browser opnieuw aanmelden. De cadeaustand blijft bewaard. (Bij normaal verversen onthoudt de telefoon de toegang automatisch.)

**QR-code ontbreekt:** gebruik de uitgeschreven link. De QR-codegenerator is al meegeleverd, dus er hoeft niets te worden geïnstalleerd.

**Muziek begint niet vanzelf:** klik op **Speel muziek** op de TV of host. Dat is een browserbeveiliging, geen defect.

**Game loopt vast op een antwoord:** de host kan onthullen en naar de volgende vraag gaan zonder op alle vier telefoons te wachten. Er hoeft niemand af te vallen.

## Privacy en opslag

De server draait op **jouw eigen computer**, niet in de cloud. De namen, scores, cadeaustanden en muziekbibliotheek staan lokaal in `party-state.json`, `.host-key` en `audio/`. De bestanden worden automatisch gemaakt bij de eerste start. Je kunt ze na de avond verwijderen. Bewaar de volledige hostlink privé en zet geen poort 8765 open op je router. De app is bedoeld voor een vertrouwd thuisnetwerk, niet voor publiek internet.

## Technisch

Alleen Python-standaardbibliotheek voor de server, gewone HTML/CSS/JS voor de interface, JSON-polling voor de synchronisatie. Geen npm-installatie, database of internetserver nodig. Starten met `python3 server.py`. Voor ontwikkeltests: `python tests/test_http.py` terwijl de server draait (dit reset de speldata!).

## Hitster-kaarten importeren en op de TV testen

Vanaf deze versie kun je een **CSV met originele Hitster QR-URL's** importeren. Dat werkt volledig lokaal zonder de QR-kaarten te fotograferen of Spotify/Apple Music te integreren.

1. Maak met Apple **Opdrachten** een scanner die per Hitster-kaart de QR-URL, artiest, titel en het jaartal vastlegt. Zet iedere kaart op één CSV-regel in de volgorde **URL, artiest, titel, jaar**. Een kopregel is niet verplicht.
2. Kopieer of mail het CSV-bestand naar de laptop. Voorbeeld met *fictieve* URL's:

   ```csv
   "https://voorbeeld.invalid/kaart001","ABBA","Dancing Queen",1976
   "https://voorbeeld.invalid/kaart002","Queen","Bohemian Rhapsody",1975
   ```

3. Start de server en open de **beveiligde hostlink**. Ga vóór de eerste spelronde naar **Hitster QR-bibliotheek**, kies het CSV-bestand en klik op **Importeer Hitster-kaarten**.
4. Je ziet per kaart de artiest, titel, het jaar en de opgeslagen QR-inhoud. Bestaande URL's worden niet dubbel geïmporteerd. Ongeldige regels worden gerapporteerd en overgeslagen.
5. Klik bij één kaart op **📺 Test QR**. Een apart scherm toont de opnieuw gegenereerde QR-code, zonder het antwoord. Toon dit scherm groot op je TV en scan het met de **officiële Hitster-app**. Controleer met de originele kaart of het juiste nummer wordt geopend.
6. Tijdens een Hitster-minigame toont het TV-scherm daarna automatisch QR-codes van opgeslagen kaarten. Titel, artiest en jaar verschijnen pas na het beantwoorden. De app probeert decennia binnen de ronde af te wisselen en voorkomt herhaling zolang ongebruikte kaarten beschikbaar zijn.

**Belangrijk:** de software bewaart exact de ingescande URL (zonder verkorten, redirects volgen of aanpassen), maar de nieuwe QR-afbeelding kan een ander pixelpatroon hebben. Of de officiële Hitster-app opnieuw gegenereerde codes accepteert, moet je met de eerste echte kaart controleren. De app kan dit niet zelf bevestigen.

**Privacy:** de bibliotheek blijft in `party-state.json` op de laptop, die door `.gitignore` uit de openbare GitHub-repository wordt gehouden. Deel de geheime hostlink niet. Er is geen koppeling met Hitster of een streaming-API.

**Formaat:** UTF-8 CSV met (optioneel) kolommen `URL,Artiest,Titel,Jaar` en komma's of puntkomma's. Vul aanhalingstekens binnen titels in CSV in als dubbele `""`; de scanner kan dat automatisch afhandelen. Maximaal 300 KB per import en 2000 kaarten in de bibliotheek. De import werkt vóór het starten van de spelavond. Een reset van de scores bewaart de Hitster-bibliotheek.
