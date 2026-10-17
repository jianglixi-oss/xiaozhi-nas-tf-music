import tempfile
import time
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from library import Library


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        (root / '歌手 - 歌曲.MP3').write_bytes(b'mp3')
        (root / 'other.flac').write_bytes(b'flac')
        self.library = Library(root, 's' * 32, 'http://nas:8765')

    def test_search_signature_and_path(self):
        matches = self.library.search('歌手 歌曲')
        self.assertEqual(len(matches), 1)
        url = urlsplit(matches[0]['url'])
        query = parse_qs(url.query)
        key = url.path.split('/')[-1]
        path = self.library.authorized_path(key, int(query['expires'][0]), query['signature'][0])
        self.assertEqual(path.read_bytes(), b'mp3')
        with self.assertRaises(PermissionError):
            self.library.authorized_path(key, int(query['expires'][0]), 'tampered')

    def test_expired_and_future_urls(self):
        key = next(iter(self.library.files))
        for expires in (int(time.time()) - 10, int(time.time()) + 10000):
            with self.assertRaises(PermissionError):
                self.library.authorized_path(key, expires, self.library.signature(key, expires))

    def test_removed_file_and_refresh(self):
        path = next(iter(self.library.files.values()))[1]
        path.unlink()
        self.assertEqual(self.library.refresh(), 0)
        self.assertEqual(self.library.search(''), [])

    def test_limit_and_non_mp3(self):
        self.assertEqual(len(self.library.search('', 1000)), 1)
        self.assertEqual(self.library.search('flac'), [])


if __name__ == '__main__':
    unittest.main()
