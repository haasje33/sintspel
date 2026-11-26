#!/usr/bin/env python3
"""De Grote Sinterklaas Spellenavond — LAN-only party server without third-party dependencies.

Run: python server.py. Everything stays on the computer running the server.
The game rules live in show_v2.py; this module handles HTTP, phone seats,
the music library import and safe persistence in party-state.json.
"""
import json
import os
import random
import secrets
import socket
import threading
import time
import uuid
from copy import deepcopy
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from hitster_library import MAX_CARDS, parse_cards_csv, qr_png
import show_v2

BASE = Path(__file__).resolve().parent
STATIC = BASE / 'static'
DATA = BASE / 'party-state.json'
ADMIN = BASE / '.host-key'
PORT = int(os.environ.get('PARTY_PORT', '8765'))
RNG = random.SystemRandom()
LOCK = threading.RLock()

# Fixed types: on Windows, mimetypes reads the registry, which on some PCs
# maps .js to text/plain. With nosniff the browser would refuse the script.
CONTENT_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.svg': 'image/svg+xml',
}
STATIC_FILES = {'/': 'index.html', '/host': 'index.html', '/screen': 'index.html',
                '/play': 'index.html', '/v2.js': 'v2.js', '/v2.css': 'v2.css',
                '/cards.svg': 'cards.svg', '/card-back.svg': 'card-back.svg'}


def init_state():
    return {
        'room': str(RNG.randrange(1000, 10000)), 'version': 0,
        'players': [{'id': f'p{i+1}', 'name': name, 'token': None}
                    for i, name in enumerate(['Speler 1', 'Speler 2', 'Speler 3', 'Speler 4'])],
        'history': [], 'hitster_cards': [],
    }


def load_state():
    if not DATA.exists():
        return init_state()
    try:
        # utf-8-sig: tolerate a BOM added when the file was saved in Notepad.
        s = json.loads(DATA.read_text(encoding='utf-8-sig'))
        if not isinstance(s, dict) or len(s.get('players', [])) != 4:
            raise ValueError('onverwachte inhoud')
        s.setdefault('hitster_cards', [])
        s.setdefault('history', [])
        s.setdefault('version', 0)
        s.setdefault('room', str(RNG.randrange(1000, 10000)))
        return s
    except (OSError, ValueError, TypeError) as exc:
        # Never silently overwrite a damaged save: keep it for recovery.
        backup = DATA.with_name('party-state.beschadigd-%s.json' % time.strftime('%Y%m%d-%H%M%S'))
        try:
            DATA.replace(backup)
            print('!! party-state.json kon niet worden gelezen (%s).' % exc)
            print('!! Het bestand is bewaard als %s; er start een nieuwe spelstand.' % backup.name)
        except OSError:
            print('!! party-state.json kon niet worden gelezen of verplaatst (%s).' % exc)
        return init_state()


S = load_state()
# Drop keys from the retired first version of the game engine.
for legacy in ('mode', 'bag', 'recent', 'spin', 'game', 'gift', 'music', 'hitster_used', 'used', 'started_at'):
    S.pop(legacy, None)
for p in S['players']:  # gift counts and wins are no longer tracked
    for legacy in ('received', 'target', 'wins'):
        p.pop(legacy, None)
show_v2.ensure(S)
show_v2.load_packaged_library(S, BASE / 'data' / 'music-library.json')
if ADMIN.exists():
    ADMIN_KEY = ADMIN.read_text(encoding='utf-8-sig').strip()
else:
    ADMIN_KEY = secrets.token_urlsafe(24)
    ADMIN.write_text(ADMIN_KEY, encoding='utf-8')
    try:
        ADMIN.chmod(0o600)
    except OSError:
        pass


def save():
    S['version'] += 1
    raw = json.dumps(S, ensure_ascii=False, indent=2)
    path = DATA.with_suffix('.tmp')
    path.write_text(raw, encoding='utf-8')
    # On Windows a virus scanner, OneDrive or backup tool can briefly lock the
    # file. Retry instead of failing the host's action.
    for attempt in range(8):
        try:
            path.replace(DATA)
            return
        except PermissionError:
            if attempt == 7:
                raise OSError('De spelstand kon niet worden opgeslagen: party-state.json is vergrendeld '
                              '(virusscanner of OneDrive?). Probeer het opnieuw.')
            time.sleep(0.15)


def player(token):
    return next((p for p in S['players'] if token and p['token'] == token), None)


def by_id(pid):
    return next((p for p in S['players'] if p['id'] == pid), None)


def sanitized(is_admin, token=''):
    me = player(token)
    return {
        'version': S['version'], 'room': S['room'], 'host_authorized': is_admin,
        'players': [{k: v for k, v in p.items() if k != 'token'} | {'joined': bool(p['token'])}
                    for p in S['players']],
        'me': me['id'] if me else None,
        'join_url': f'http://{lan_ip()}:{PORT}/play',
        'screen_url': f'http://{lan_ip()}:{PORT}/screen',
        'show': show_v2.view(S, is_admin, me['id'] if me else None),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = 'Sintspel/2.1'

    def log_message(self, fmt, *args):
        if not self.path.startswith('/api/state'):
            print('%s %s' % (self.address_string(), fmt % args))

    def send_bytes(self, data, content_type, status=200, cache='no-store', extra=()):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', cache)
        self.send_header('X-Content-Type-Options', 'nosniff')
        for name, value in extra:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def jsonout(self, value, status=200):
        self.send_bytes(json.dumps(value, ensure_ascii=False).encode('utf-8'),
                        'application/json; charset=utf-8', status)

    def serve_static(self, filename):
        path = STATIC / filename
        if not path.is_file():
            self.send_error(404)
            return
        # Code always fresh; the large card artwork may be cached by the TV.
        cache = 'private, max-age=86400' if path.suffix == '.svg' else 'no-store'
        self.send_bytes(path.read_bytes(), CONTENT_TYPES.get(path.suffix, 'application/octet-stream'), cache=cache)

    def do_GET(self):
        parsed = urlparse(self.path)
        q = parse_qs(parsed.query)
        path = parsed.path
        # Opening /host on the server laptop is safe and convenient.
        # Only loopback requests with a literal localhost Host header can
        # receive the secret host URL; never redirect remote players to it.
        if path == '/host' and q.get('key', [''])[0] != ADMIN_KEY:
            local_peer = self.client_address[0] in ('127.0.0.1', '::1')
            local_host = self.headers.get('Host', '').lower() in (f'127.0.0.1:{PORT}', f'localhost:{PORT}')
            if local_peer and local_host:
                self.send_bytes(b'', 'text/plain', 302, extra=(('Location', '/host?key=' + ADMIN_KEY),
                                                               ('Referrer-Policy', 'no-referrer')))
                return
        if path == '/api/state':
            is_admin = q.get('key', [''])[0] == ADMIN_KEY
            with LOCK:
                state = sanitized(is_admin, q.get('token', [''])[0])
            self.jsonout(state)
            return
        if path == '/api/health':
            self.jsonout({'ok': True, 'room': S['room']})
            return
        if path in ('/hitster/qr.png', '/hitster/test'):
            self.hitster(path, q)
            return
        if path == '/favicon.ico':
            self.send_bytes(b'', 'image/x-icon', 204)
            return
        if path in STATIC_FILES:
            self.serve_static(STATIC_FILES[path])
            return
        if path == '/qr.png':
            target = q.get('url', [''])[0]
            if not target.startswith('http://') or len(target) > 250:
                self.send_error(404)
                return
            try:
                data = qr_png(target, scale=4)
            except Exception as e:  # QR rendering must never take the server down.
                print('QR render error', repr(e))
                self.send_error(404)
                return
            self.send_bytes(data, 'image/png', cache='private, max-age=600')
            return
        self.send_error(404)

    def hitster(self, path, q):
        card_id = q.get('id', [''])[0]
        with LOCK:
            card = next((c for c in S.get('hitster_cards', []) if c['id'] == card_id), None)
            show = S.get('show2') or {}
            current = show.get('game') or {}
            active = False
            if show.get('mode') == 'game' and current.get('category') in ('classic', 'quiz'):
                r = current['rounds'][current['round_index']]
                active = (r.get('hidden_id') == card_id
                          and current.get('phase') in ('answer', 'reveal', 'review'))
        admin_access = q.get('key', [''])[0] == ADMIN_KEY
        if not card or not (admin_access or (active and path == '/hitster/qr.png')):
            self.send_error(404)
            return
        if path == '/hitster/qr.png':
            try:
                data = qr_png(card['url'])
            except (ValueError, OverflowError) as exc:
                print('Hitster QR error', repr(exc))
                self.send_error(400)
                return
            self.send_bytes(data, 'image/png')
            return
        src = '/hitster/qr.png?id=' + card_id + '&key=' + ADMIN_KEY
        page = ("<!doctype html><html lang='nl'><head><meta charset='utf-8'>"
                "<meta name='viewport' content='width=device-width, initial-scale=1'>"
                "<title>Hitster — testcode</title><style>body{background:#101d25;color:white;"
                "font-family:system-ui;text-align:center;margin:0;display:grid;place-content:center;"
                "min-height:100vh}img{width:min(84vw,68vh,620px);image-rendering:pixelated;"
                "background:white;padding:12px;border-radius:12px}p{margin:18px auto}"
                "</style></head><body><h1>🎵 Hitster — testcode</h1><p>Scan met de officiële Hitster-app</p>"
                f"<img alt='Hitster QR-testcode' src='{escape(src, quote=True)}'>"
                "<p>Controleer of hetzelfde nummer wordt afgespeeld.</p></body></html>")
        self.send_bytes(page.encode('utf-8'), 'text/html; charset=utf-8', extra=(('Referrer-Policy', 'no-referrer'),))

    def do_POST(self):
        status, body = 200, None
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length > 1024 * 1024:
                raise ValueError('Verzoek te groot.')
            path = urlparse(self.path).path
            payload = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
            if not isinstance(payload, dict):
                raise ValueError('Ongeldig verzoek.')
            with LOCK:
                # Transaction: a failing action (or a failed save) must never
                # leave a half-applied change behind in memory.
                snapshot = deepcopy(S)
                try:
                    result = self.dispatch(path, payload)
                except BaseException:
                    S.clear()
                    S.update(snapshot)
                    raise
                body = {'ok': True, 'data': result, 'version': S['version']}
        except PermissionError as e:
            status, body = 403, {'error': str(e)}
        except (ValueError, KeyError, TypeError, IndexError) as e:
            status, body = 400, {'error': str(e)}
        except OSError as e:
            print('Opslagfout', repr(e))
            status, body = 503, {'error': str(e) or 'De spelstand kon niet worden opgeslagen.'}
        except Exception as e:
            print('Unexpected error', repr(e))
            status, body = 500, {'error': 'Er ging iets mis op de server.'}
        # Write the response outside the lock: a slow phone must not block others.
        self.jsonout(body, status)

    def dispatch(self, path, payload):
        action = str(payload.get('action', ''))
        if path == '/api/claim':
            return self.claim(payload)
        if path == '/api/submit':
            p = player(payload.get('token', ''))
            if not p:
                raise PermissionError('Meld je eerst aan.')
            return show_v2.submit(S, payload, p['id'], save)
        if path == '/api/admin':
            if self.headers.get('X-Admin-Key') != ADMIN_KEY:
                raise PermissionError('Alleen de host kan dit doen.')
            if action == 'import_hitster':
                return self.import_hitster(payload)
            return show_v2.admin(S, payload, save)
        raise ValueError('Onbekende actie.')

    def claim(self, a):
        if str(a.get('room', '')).strip() != S['room']:
            raise ValueError('Onjuiste spelcode.')
        p = by_id(a.get('player', ''))
        if not p:
            raise ValueError('Onbekende speler.')
        token = str(a.get('token', '') or '')
        if p['token'] and p['token'] != token:
            raise ValueError('Deze plek is al bezet. Vraag de spelleider om de telefoon te ontkoppelen.')
        # A phone holds at most one seat: switching seats frees the old one.
        for other in S['players']:
            if other is not p and token and other['token'] == token:
                other['token'] = None
        if not p['token']:
            p['token'] = secrets.token_urlsafe(24)
        save()
        return {'token': p['token'], 'player': p['id']}

    def import_hitster(self, a):
        if show_v2.ensure(S)['mode'] != 'setup':
            raise ValueError('Importeer kaarten vóór het starten van de spelavond.')
        existing = S.setdefault('hitster_cards', [])
        available = MAX_CARDS - len(existing)
        if available <= 0:
            raise ValueError('De muziekbibliotheek is vol (maximaal %d kaarten).' % MAX_CARDS)
        cards, duplicates, errors = parse_cards_csv(a.get('csv', ''), (c['url'] for c in existing), available)
        for card in cards:
            card['id'] = uuid.uuid4().hex
        existing.extend(cards)
        save()
        return {'added': len(cards), 'duplicates': duplicates,
                'skipped': len(errors), 'errors': errors[:15], 'total': len(existing)}


def lan_ip():
    override = os.environ.get('PARTY_IP', '').strip()
    if override:
        return override
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        return s.getsockname()[0]
    except OSError:
        return '127.0.0.1'
    finally:
        s.close()


def main():
    host = lan_ip()
    print('\n' + '=' * 62)
    print('  🎁  DE GROTE SINTERKLAAS SPELLENAVOND')
    print('=' * 62)
    print('  Host / laptop : http://127.0.0.1:%s/host?key=%s' % (PORT, ADMIN_KEY))
    print('  TV-scherm     : http://%s:%s/screen' % (host, PORT))
    print('  Telefoons     : http://%s:%s/play' % (host, PORT))
    print('  Spelcode      : %s' % S['room'])
    print('\n  Alle apparaten op dezelfde wifi. Stop met Ctrl+C.')
    print('  De spelstand staat lokaal in party-state.json.')
    print('=' * 62 + '\n')
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()


if __name__ == '__main__':
    main()
