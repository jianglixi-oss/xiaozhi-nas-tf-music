import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from urllib.error import HTTPError
from homepod import HomePod


class HomePodTests(unittest.TestCase):
    def make(self):
        return HomePod({'HOME_ASSISTANT_URL': 'http://127.0.0.1:8123',
                        'HOME_ASSISTANT_TOKEN': 'private-test-token',
                        'HOME_ASSISTANT_PLAYERS': '{"primary":"media_player.test"}'})

    def test_reject_unconfigured_and_unknown_target(self):
        self.assertEqual(HomePod({}).command('play_media')['status'], 'configuration_error')
        h = self.make()
        with patch.object(h, 'request') as request:
            self.assertEqual(h.command('play_media', 'unknown')['status'], 'configuration_error')
            request.assert_not_called()

    def test_timeout_is_unknown_no_retry_no_credential_leak(self):
        h = self.make()
        with patch.object(h, 'request', side_effect=TimeoutError('private-test-token')) as request:
            result = h.command('play_media', url='http://nas/audio?signature=secret')
            self.assertEqual(result['status'], 'unknown')
            self.assertNotIn('private-test-token', json.dumps(result))
            self.assertNotIn('signature', json.dumps(result))
            self.assertEqual(request.call_count, 1)

    def test_http_error_is_failure(self):
        h = self.make()
        with patch.object(h, 'request', side_effect=HTTPError('http://ha',500,'failed',{},None)):
            self.assertEqual(h.command('play_media')['http_status'], 500)

    def test_actual_http_command_and_state(self):
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                calls.append((self.path, self.headers.get('Authorization'),
                              json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
                self.send_response(200); self.end_headers(); self.wfile.write(b'[]')
            def do_GET(self):
                self.send_response(200); self.end_headers()
                self.wfile.write(b'{"state":"off","attributes":{}}')
            def log_message(self, *args): pass
        server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True);thread.start()
        try:
            h = self.make();h.base = 'http://127.0.0.1:' + str(server.server_port)
            result = h.command('play_media', url='http://nas/audio')
            self.assertEqual(result['status'], 'accepted')
            self.assertEqual(calls[0], ('/api/services/media_player/play_media',
                'Bearer private-test-token', {'entity_id':'media_player.test',
                    'media_content_id':'http://nas/audio','media_content_type':'music'}))
            self.assertEqual(h.status()['state'], 'off')
            self.assertEqual(h.command('media_stop')['status'], 'accepted')
        finally:
            server.shutdown();server.server_close();thread.join()
