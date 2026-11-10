#!/usr/bin/env python3
"""Basic regression tests: CSV, duplicates and QR round trip."""
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hitster_library import parse_cards_csv, qr_png

class HitsterTests(unittest.TestCase):
    def test_shortcuts_csv(self):
        content = ('"https://example.invalid/song?x=1&y=2","A, B","Title ""Q""",1976\n'
                   '"https://example.invalid/song?x=1&y=2","A, B","Title",1976\n'
                   'bad,artist,title,year\n')
        cards, duplicates, errors = parse_cards_csv(content)
        self.assertEqual(1, len(cards))
        self.assertEqual(1, duplicates)
        self.assertEqual(1, len(errors))
        self.assertEqual('Title "Q"', cards[0]['title'])
    def test_original_scanned_qr_without_scheme(self):
        payload='www.hitstergame.com/nl/aaaa0006/00107'
        rows,duplicates,errors=parse_cards_csv(payload+',Eiffel 65,Blue (Da Ba Dee),1998\\n')
        self.assertEqual(errors,[])
        self.assertEqual(duplicates,0)
        self.assertEqual(rows[0]['url'],payload)

    def test_headers(self):
        cards, duplicates, errors = parse_cards_csv('\ufeffTitel;Jaar;URL;Artiest\nHey;1998;https://example.invalid/hey;B\n')
        self.assertEqual(1, len(cards))
        self.assertEqual('https://example.invalid/hey',cards[0]['url'])
    def test_qr_png(self):
        data = qr_png('https://example.invalid/a?x=%2F&y=1')
        self.assertTrue(data.startswith(b'\x89PNG\r\n\x1a\n'))

if __name__=='__main__':
    unittest.main()
