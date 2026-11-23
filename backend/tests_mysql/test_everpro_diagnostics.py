import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest

from integrations.check_everpro import check_auth, environment_report


@pytest.mark.parametrize('status,body,reason', [
    (200, {'data': {'token': 'secret-token', 'token_type': 'Bearer'}}, 'token_received'),
    (404, {'message': 'user not found'}, 'client_not_found_in_environment'),
    (404, {'message': 'secret-key secret-value secret-token'}, 'authentication_rejected'),
    (401, {'message': 'secret-value'}, 'authentication_rejected'),
    (200, {'data': []}, 'authentication_rejected'),
    (404, '<html>secret-value</html>', 'non_json_or_invalid_response'),
])
def test_token_probe_reports_only_fixed_classifications(status, body, reason):
    calls = []
    def handler(request):
        calls.append(request)
        assert request.method == 'POST' and request.url.path == '/auth/v1/token'
        assert json.loads(request.content) == {'client_key':'secret-key', 'client_secret':'secret-value'}
        return httpx.Response(status, json=body) if isinstance(body, dict) else httpx.Response(status, text=body)
    settings = SimpleNamespace(base_url='https://client-api.everpro.id', client_key='secret-key', client_secret='secret-value')
    report = asyncio.run(check_auth(settings, transport=httpx.MockTransport(handler)))
    assert report['reason'] == reason
    assert report['ok'] == (reason == 'token_received')
    assert len(calls) == 1
    assert all(secret not in json.dumps(report) for secret in ('secret-key','secret-value','secret-token'))


def test_process_overrides_are_identified_without_disclosing_credentials():
    report = environment_report({'EVERPRO_CLIENT_KEY':'file-key', 'EVERPRO_CLIENT_SECRET':'same'},
                                {'EVERPRO_CLIENT_KEY':'old-key', 'EVERPRO_CLIENT_SECRET':'same'})
    assert report['EVERPRO_CLIENT_KEY']['source'] == 'process'
    assert report['EVERPRO_CLIENT_KEY']['matches_file'] is False
    assert report['EVERPRO_CLIENT_SECRET']['matches_file'] is True
    assert all(value not in json.dumps(report) for value in ('file-key', 'old-key', 'same'))


def test_network_exceptions_do_not_print_connection_details():
    def handler(request):
        raise httpx.ConnectError('secret-key secret-value', request=request)
    settings = SimpleNamespace(base_url='https://client-api.everpro.id', client_key='secret-key', client_secret='secret-value')
    assert asyncio.run(check_auth(settings, transport=httpx.MockTransport(handler))) == {'ok':False, 'reason':'network_or_tls_error'}
