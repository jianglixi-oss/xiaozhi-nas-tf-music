"""Read-only internet radio station list from a JSON file.

The station file mirrors the music library management style: it lives in the
same read-only NAS folder the user already mounts, so stations are edited on
the NAS without rebuilding the container. Playback itself reuses the device's
existing ``self.music.play_url`` MCP tool (a radio stream is just a continuous
HTTP MP3 stream).
"""
import json
from pathlib import Path


class Radio:
    def __init__(self, path):
        self.path = Path(path)
        self.stations = []
        self.refresh()

    def refresh(self):
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            self.stations = []
            return 0
        if not isinstance(data, list):
            self.stations = []
            return 0
        stations = []
        for item in data:
            if not isinstance(item, dict):
                continue
            name = str(item.get('name', '')).strip()
            url = str(item.get('url', '')).strip()
            if name and url.startswith(('http://', 'https://')):
                stations.append({'name': name, 'url': url})
        self.stations = stations
        return len(stations)

    def list(self):
        self.refresh()  # re-read the file so web-page edits apply immediately
        return [{
            'name': station['name'],
            'url': station['url'],
            'device_tool': 'self.music.play_url',
            'device_arguments': {'url': station['url']},
        } for station in self.stations]
