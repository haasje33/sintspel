"""Local Hitster QR library: CSV parsing, safe persistence and exact-payload QR output.

No Spotify/Hitster API calls or image scans. Input contains decoded QR strings,
not card photographs. Keep this module and its data on a trusted home network.
"""
import csv
import io
import json
import random
import re
import sys
import uuid
from pathlib import Path
from urllib.parse import urlsplit


MAX_URL_CHARS = 1000
MAX_CARDS = 5000
MAX_CSV_CHARS = 950_000
FIELD_ALIASES = {
    'url': {'qrurl', 'qr', 'url', 'qrcode', 'qrinhoud', 'code', 'link'},
    'artist': {'artiest', 'artist', 'uitvoerder'},
    'title': {'titel', 'title', 'nummer', 'song'},
    'year': {'jaar', 'year', 'releasejaar', 'jaartal'},
}


def _header_key(value):
    return re.sub(r'[^a-z0-9]', '', value.strip().lower())


def validate_card(url, artist, title, year):
    # Do not trim, shorten or follow the QR URL: its string must be reproduced.
    if not isinstance(url, str) or not url or url != url.strip() or len(url) > MAX_URL_CHARS:
        raise ValueError('QR-URL ontbreekt, bevat spaties aan de randen of is te lang.')
    parts = urlsplit(url)
    if parts.scheme not in ('http', 'https') or not parts.hostname or any(c.isspace() for c in url):
        raise ValueError('De QR-inhoud moet een volledige http(s)-URL zijn.')
    artist = str(artist).strip()
    title = str(title).strip()
    if not artist or not title or len(artist) > 120 or len(title) > 120:
        raise ValueError('Artiest en titel zijn verplicht (max. 120 tekens).')
    try:
        number = int(str(year).strip())
    except (ValueError, TypeError):
        raise ValueError('Gebruik een geldig jaartal, bijvoorbeeld 1987.') from None
    if str(year).strip() != str(number) or not 1800 <= number <= 2100:
        raise ValueError('Jaartal moet tussen 1800 en 2100 liggen.')
    return {'url': url, 'artist': artist, 'title': title, 'year': number}


def parse_csv(source):
    if not isinstance(source, str) or not source.strip() or len(source) > MAX_CSV_CHARS:
        raise ValueError('Kies een CSV-bestand (maximaal circa 950 kB).')
    source = source.lstrip('\ufeff')
    try:
        dialect = csv.Sniffer().sniff(source[:8192], delimiters=',;\t')
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ';' if source.count(';') > source.count(',') else ','
    reader = csv.reader(io.StringIO(source, newline=''), delimiter=delimiter, strict=True)
    try:
        rows = [(i, row) for i, row in enumerate(reader, start=1) if row and any(c.strip() for c in row)]
    except csv.Error as e:
        raise ValueError('CSV kon niet worden gelezen: ' + str(e)) from None
    if not rows:
        raise ValueError('Het CSV-bestand bevat geen kaarten.')
    if len(rows) > MAX_CARDS + 1:
        raise ValueError('Importeer maximaal 5.000 kaarten per bestand.')
    head = [_header_key(x) for x in rows[0][1]]
    mapping = {key: next((i for i, value in enumerate(head) if value in aliases), None)
               for key, aliases in FIELD_ALIASES.items()}
    if all(pos is not None for pos in mapping.values()):
        rows = rows[1:]
    elif any(pos is not None for pos in mapping.values()):
        raise ValueError('CSV-kopregel moet QR_URL, Artiest, Titel en Jaar bevatten.')
    else:
        mapping = {'url': 0, 'artist': 1, 'title': 2, 'year': 3}
    if not rows:
        raise ValueError('Er staan geen kaarten onder de CSV-kopregel.')
    parsed = []
    for line, row in rows:
        if len(row) != 4:
            raise ValueError(f'Rij {line}: verwacht vier kolommen, gevonden: {len(row)}.')
        try:
            parsed.append(validate_card(*(row[mapping[x]] for x in ('url','artist','title','year'))))
        except ValueError as e:
            raise ValueError(f'Rij {line}: {e}') from None
    return parsed


def era(year):
    return 'klassiek' if year < 1990 else 'millennium' if year < 2010 else 'recent'


class HitsterLibrary:
    def __init__(self, path, vendor_dir):
        self.path = Path(path)
        self.vendor_dir = Path(vendor_dir)
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            self.cards = data if isinstance(data, list) else []
        except (OSError, ValueError):
            self.cards = []

    def list_public(self):
        """Admin-only metadata; never exposes original QR URLs to the player state."""
        return [{k:c[k] for k in ('id','artist','title','year')} for c in self.cards]

    def get(self, card_id):
        if not re.fullmatch(r'[0-9a-f]{32}', str(card_id)):
            return None
        return next((c for c in self.cards if c['id'] == card_id), None)

    def save(self):
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.cards, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(self.path)

    def import_cards(self, entries):
        known = {c['url'] for c in self.cards}
        additions = []
        skipped = 0
        for entry in entries:
            if entry['url'] in known:
                skipped += 1
                continue
            additions.append({'id': uuid.uuid4().hex, **entry})
            known.add(entry['url'])
        if len(self.cards) + len(additions) > MAX_CARDS:
            raise ValueError('De bibliotheek kan maximaal 5.000 kaarten bevatten.')
        if additions:
            self.cards.extend(additions)
            self.save()
        return {'added': len(additions), 'duplicates': skipped, 'total': len(self.cards)}

    def add(self, url, artist, title, year):
        return self.import_cards([validate_card(url, artist, title, year)])

    def remove(self, card_id):
        card = self.get(card_id)
        if not card:
            raise ValueError('Kaart niet gevonden.')
        self.cards.remove(card)
        self.save()

    def edit(self, card_id, artist, title, year):
        card = self.get(card_id)
        if not card:
            raise ValueError('Kaart niet gevonden.')
        clean = validate_card(card['url'], artist, title, year)
        card.update(clean)
        self.save()

    def select(self, used, count=3):
        """No same-card repeats within a round; spread 3 songs across eras when possible."""
        if not self.cards:
            return [], list(used)
        chosen = []
        picked_ids = set()
        unplayed = [c for c in self.cards if c['id'] not in used]
        if not unplayed:
            used = []
            unplayed = list(self.cards)
        rng = random.SystemRandom()
        for era_name in rng.sample(['klassiek', 'millennium', 'recent'], 3):
            pool = [c for c in unplayed if era(c['year']) == era_name and c['id'] not in picked_ids]
            if pool and len(chosen) < count:
                pick = rng.choice(pool)
                chosen.append(pick)
                picked_ids.add(pick['id'])
        remaining = [c for c in unplayed if c['id'] not in picked_ids]
        rng.shuffle(remaining)
        chosen.extend(remaining[:max(0, count-len(chosen))])
        picked_ids = {c['id'] for c in chosen}
        if len(chosen) < min(count,len(self.cards)):
            fallback = [c for c in self.cards if c['id'] not in picked_ids]
            rng.shuffle(fallback)
            chosen.extend(fallback[:count-len(chosen)])
            used = []
        return chosen, list(set(used).union(c['id'] for c in chosen))

    def qr_svg(self, card_id):
        card = self.get(card_id)
        if not card:
            raise ValueError('Kaart niet gevonden.')
        if str(self.vendor_dir) not in sys.path:
            sys.path.insert(0,str(self.vendor_dir))
        import qrcode
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
        qr.add_data(card['url'])
        try:
            qr.make(fit=True)
        except Exception as e:
            raise ValueError('QR-code kon niet worden gegenereerd.') from e
        matrix = qr.get_matrix()
        size = len(matrix)
        # The SVG encodes only generated rectangles; original user text is never interpolated.
        path = ' '.join(f'M{x} {y}h1v1h-1z' for y,row in enumerate(matrix) for x,dark in enumerate(row) if dark)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
                f'width="800" height="800" shape-rendering="crispEdges">'
                f'<rect width="{size}" height="{size}" fill="white"/>'
                f'<path d="{path}" fill="black"/></svg>').encode('utf-8')
