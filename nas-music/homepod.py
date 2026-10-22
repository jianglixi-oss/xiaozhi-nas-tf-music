"""Restricted HA playback bridge. Credentials and signed URLs never enter results."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HomePod:
    def __init__(self, env=None):
        env = os.environ if env is None else env
        self.base = env.get('HOME_ASSISTANT_URL', '').rstrip('/')
        self.token = env.get('HOME_ASSISTANT_TOKEN', '')
        self.players = json.loads(env.get('HOME_ASSISTANT_PLAYERS', '{}'))
        if not isinstance(self.players, dict) or any(
                not isinstance(k, str) or not isinstance(v, str) or
                not v.startswith('media_player.') or not v.replace('_', '').replace('.', '').isalnum()
                for k, v in self.players.items()):
            raise ValueError('HOME_ASSISTANT_PLAYERS must map names to media_player entities')
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def target(self, player):
        if not self.base or not self.token or not self.players:
            raise ValueError('HomePod is not configured')
        u = urlsplit(self.base)
        if u.scheme not in ('http', 'https') or not u.hostname or u.username or u.password or u.query or u.fragment:
            raise ValueError('Invalid HOME_ASSISTANT_URL')
        if not player:
            player = next(iter(self.players))
        if player not in self.players:
            raise ValueError('Choose a player returned by nas_homepod_players')
        return player, self.players[player]

    def request(self, path, body=None):
        data = None if body is None else json.dumps(body).encode()
        request = Request(self.base + path, data=data, headers={
            'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'})
        with self.opener.open(request, timeout=12) as response:
            return json.load(response)

    def status(self, player=''):
        try:
            name, entity = self.target(player)
            state = self.request('/api/states/' + entity)
            a = state.get('attributes', {})
            return {'player': name, 'state': state['state'],
                    'title': a.get('media_title'), 'volume': a.get('volume_level')}
        except ValueError as ex:
            return {'status': 'configuration_error', 'message': str(ex)}
        except (OSError, HTTPError, URLError):
            return {'status': 'unavailable'}

    def command(self, action, player='', url=None):
        if action not in ('play_media', 'media_stop'):
            raise ValueError('Unsupported action')
        try:
            name, entity = self.target(player)
            body = {'entity_id': entity}
            if action == 'play_media':
                body.update(media_content_id=url, media_content_type='music')
            self.request('/api/services/media_player/' + action, body)
            return {'status': 'accepted', 'player': name,
                    'message': 'HA accepted the request; audible playback is not confirmed.'}
        except ValueError as ex:
            return {'status': 'configuration_error', 'message': str(ex)}
        except HTTPError as ex:
            return {'status': 'failed', 'http_status': ex.code}
        except (OSError, URLError):
            return {'status': 'unknown', 'message':
                    'HA did not confirm the request. It may still play. Do not automatically retry.'}
