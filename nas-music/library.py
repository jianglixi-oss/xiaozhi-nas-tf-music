"""Read-only local MP3 library and expiring URL signatures (no NAS login required)."""
import hashlib
import hmac
import time
import unicodedata
from pathlib import Path


class Library:
    def __init__(self, root, secret, base_url):
        self.root = Path(root).resolve(strict=True)
        self.secret = secret.encode()
        self.base_url = base_url.rstrip('/')
        self.files = {}
        self.refresh()

    def refresh(self):
        files = {}
        for path in self.root.rglob('*'):
            if path.suffix.lower() != '.mp3' or not path.is_file():
                continue
            resolved = path.resolve()
            if not resolved.is_relative_to(self.root):
                continue
            relative = path.relative_to(self.root).as_posix()
            key = hashlib.sha256(relative.encode()).hexdigest()[:32]
            files[key] = (relative, resolved)
        self.files = files
        return len(files)

    @staticmethod
    def normalize(text):
        return unicodedata.normalize('NFKC', text).casefold()

    def signature(self, key, expires):
        return hmac.new(self.secret, f'{key}:{expires}'.encode(), hashlib.sha256).hexdigest()

    def search(self, query, limit=10):
        terms = self.normalize(query).split()
        result = []
        expires = int(time.time()) + 900
        snapshot = self.files
        for key, (relative, _) in sorted(snapshot.items(), key=lambda item: item[1][0]):
            if all(term in self.normalize(relative) for term in terms):
                url = f'{self.base_url}/audio/{key}?expires={expires}&signature={self.signature(key, expires)}'
                result.append({'name': relative, 'url': url,
                               'device_tool': 'self.music.play_url', 'device_arguments': {'url': url}})
                if len(result) >= max(1, min(limit, 20)):
                    break
        return result

    def authorized_path(self, key, expires, signature):
        if expires < time.time() or expires > time.time() + 901:
            raise PermissionError('Expired URL')
        if not hmac.compare_digest(signature, self.signature(key, expires)):
            raise PermissionError('Invalid signature')
        path = self.files[key][1].resolve(strict=True)
        if not path.is_relative_to(self.root) or not path.is_file():
            raise PermissionError('Outside music directory')
        return path
