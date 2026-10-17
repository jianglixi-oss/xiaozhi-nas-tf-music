"""stdio MCP plus LAN-only HTTP MP3 streaming. Run via the official MCP pipe."""
import os
import shutil
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from mcp.server.fastmcp import FastMCP
from library import Library

secret = os.environ.get('MUSIC_SIGNING_KEY', '')
if len(secret) < 32 or secret.startswith('REPLACE'):
    raise RuntimeError('Set MUSIC_SIGNING_KEY to a random secret of at least 32 characters')
base_url = os.environ['MUSIC_BASE_URL']
if urlsplit(base_url).scheme not in ('http', 'https'):
    raise RuntimeError('MUSIC_BASE_URL must be the HTTP(S) address reachable by the device')
library = Library(os.environ.get('MUSIC_DIR', '/music'), secret, base_url)
mcp = FastMCP('NAS MP3 Library')


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        request = urlsplit(self.path)
        parts = request.path.split('/')
        if len(parts) != 3 or parts[1] != 'audio':
            self.send_error(404)
            return
        try:
            args = parse_qs(request.query)
            path = library.authorized_path(parts[2], int(args['expires'][0]), args['signature'][0])
            with path.open('rb') as source:
                self.send_response(200)
                self.send_header('Content-Type', 'audio/mpeg')
                self.send_header('Content-Length', str(os.fstat(source.fileno()).st_size))
                self.send_header('Cache-Control', 'private, no-store')
                self.end_headers()
                shutil.copyfileobj(source, self.wfile, length=65536)
        except (KeyError, ValueError, PermissionError):
            self.send_error(403)
        except FileNotFoundError:
            self.send_error(404)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, fmt, *args):
        # Do not log signed URLs; stdio stdout belongs exclusively to MCP.
        pass


@mcp.tool()
def nas_music_search(query: str, limit: int = 10) -> dict:
    """Search the user's NAS MP3 filenames by song/artist. Then call the returned
    device_tool with device_arguments to play on XiaoZhi. A URL alone does not start playback.
    If several songs match, choose the requested artist/version or ask the user.
    """
    return {'matches': library.search(query[:200], limit)}


@mcp.tool()
def nas_music_refresh() -> dict:
    """Rescan the read-only music folder after files have been added or removed."""
    return {'indexed_mp3_files': library.refresh()}


if __name__ == '__main__':
    http = ThreadingHTTPServer((os.environ.get('MUSIC_BIND', '0.0.0.0'),
                               int(os.environ.get('MUSIC_PORT', '8765'))), Handler)
    http.daemon_threads = True
    threading.Thread(target=http.serve_forever, daemon=True).start()
    try:
        mcp.run(transport='stdio')
    finally:
        http.shutdown()
