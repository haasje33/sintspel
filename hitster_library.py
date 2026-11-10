"""Import a local Hitster QR collection and render original QR payloads as PNG.

No lookup or redirect is performed: the scanned URL is stored unchanged and
encoded directly into the generated QR code.
"""
import csv
import io
import re
import struct
import sys
import zlib
from pathlib import Path
from urllib.parse import urlsplit

MAX_IMPORT_BYTES = 300_000
MAX_CARDS = 2000


def parse_cards_csv(content, known_urls=(), available_slots=MAX_CARDS):
    """Return (new rows, duplicate count, errors) for headerless/headered CSV.

    Accepts the Shortcuts order URL, Artist, Title, Year, with optional header.
    A full row with malformed content is skipped and reported, not imported.
    """
    if not isinstance(content, str) or not content.strip():
        raise ValueError('Selecteer een CSV-bestand met kaartgegevens.')
    if len(content.encode('utf-8')) > MAX_IMPORT_BYTES:
        raise ValueError('CSV is te groot (maximaal 300 KB).')
    content = content.lstrip('\ufeff')
    try:
        dialect = csv.Sniffer().sniff(content[:4096], delimiters=',;')
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ','
    reader = csv.reader(io.StringIO(content, newline=''), delimiter=delimiter, strict=True)
    headers = None
    new, errors, duplicate_count = [], [], 0
    seen = set(known_urls)
    aliases = (
        {'url', 'qrurl', 'qrcode', 'qrcodeurl', 'qrinhoud', 'qr'},
        {'artist', 'artiest'},
        {'title', 'titel', 'nummer', 'song'},
        {'year', 'jaar', 'releasejaar'},
    )
    try:
        for row in reader:
            line = reader.line_num
            if not row or not any(x.strip() for x in row):
                continue
            if headers is None:
                normalized = [re.sub(r'[^a-z0-9]', '', s.strip().lower()) for s in row]
                if len(row) == 4 and all(any(v in names for v in normalized) for names in aliases):
                    headers = [next(i for i, v in enumerate(normalized) if v in names) for names in aliases]
                    continue
                headers = [0, 1, 2, 3]
            if len(row) != 4:
                errors.append(f'Regel {line}: verwacht 4 velden (URL, artiest, titel, jaar).')
                continue
            url, artist, title, raw_year = (row[i].strip() for i in headers)
            try:
                parsed = urlsplit(url)
                if (parsed.scheme.lower() not in ('http', 'https') or not parsed.hostname
                    or any(ch.isspace() or ord(ch) < 32 for ch in url)
                    or len(url.encode('utf-8')) > 1500):
                    raise ValueError('ongeldige QR-URL')
                if not artist or not title or len(artist) > 120 or len(title) > 120:
                    raise ValueError('artiest of titel ontbreekt of is te lang')
                year = int(raw_year)
                if not 1900 <= year <= 2100:
                    raise ValueError('jaar moet tussen 1900 en 2100 liggen')
                if url in seen:
                    duplicate_count += 1
                    continue
                if len(new) >= available_slots:
                    raise ValueError('maximum van 2000 kaarten bereikt')
                new.append({'url': url, 'artist': artist, 'title': title, 'year': year})
                seen.add(url)
            except (ValueError, OverflowError) as exc:
                errors.append(f'Regel {line}: {exc}.')
    except csv.Error as exc:
        raise ValueError(f'CSV kon niet worden gelezen: {exc}') from exc
    return new, duplicate_count, errors


def qr_png(payload, scale=8):
    """Encode payload into a sharp black/white PNG using the bundled library."""
    vendor = str(Path(__file__).resolve().parent / 'vendor')
    if vendor not in sys.path:
        sys.path.insert(0, vendor)
    import qrcode
    code = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
    code.add_data(payload)
    code.make(fit=True)
    matrix = code.get_matrix()
    size = len(matrix) * scale
    rows = []
    for row in matrix:
        pixels = bytes([0]) + b''.join(bytes([0 if bit else 255]) * scale for bit in row)
        rows.extend([pixels] * scale)

    def chunk(name, content):
        return (struct.pack('>I', len(content)) + name + content +
                struct.pack('>I', zlib.crc32(name + content) & 0xffffffff))

    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 0, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(b''.join(rows), 9)) +
            chunk(b'IEND', b''))
