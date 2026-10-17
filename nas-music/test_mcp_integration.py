"""Actual MCP handshake -> search -> signed HTTP download, without cloud/NAS."""
import asyncio
import json
import os
import socket
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class IntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_and_authenticated_download(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / 'Artist - Song.mp3').write_bytes(b'test-mp3-content')
            with socket.socket() as listener:
                listener.bind(('127.0.0.1', 0))
                port = listener.getsockname()[1]
            env = dict(os.environ, MUSIC_DIR=folder, MUSIC_SIGNING_KEY='integration-secret-' * 3,
                       MUSIC_BASE_URL=f'http://127.0.0.1:{port}', MUSIC_PORT=str(port),
                       MUSIC_BIND='127.0.0.1')
            params = StdioServerParameters(command=sys.executable,
                        args=[str(Path(__file__).with_name('server.py'))], env=env)
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as client:
                    await client.initialize()
                    listing = await client.list_tools()
                    self.assertEqual({t.name for t in listing.tools},
                                     {'nas_music_search', 'nas_music_refresh'})
                    result = await client.call_tool('nas_music_search', {'query': 'Artist Song'})
                    self.assertFalse(result.isError)
                    payload = json.loads(next(c.text for c in result.content if c.type == 'text'))
                    match = payload['matches'][0]
                    self.assertEqual(match['device_tool'], 'self.music.play_url')
                    def download():
                        with urlopen(match['url'], timeout=5) as response:
                            return response.read()
                    self.assertEqual(await asyncio.to_thread(download), b'test-mp3-content')
                    with self.assertRaises(HTTPError) as rejected:
                        await asyncio.to_thread(urlopen, match['url'] + 'tampered', timeout=5)
                    self.assertEqual(rejected.exception.code, 403)


if __name__ == '__main__':
    unittest.main()
