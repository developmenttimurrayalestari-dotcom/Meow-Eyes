import asyncio

import pytest
from fastapi import HTTPException

from integrations.config import DokuSettings
from mysql import integration_services as service
from mysql.commerce import create_checkout
from tests_mysql.sql_helpers import isolated_database
from tests_mysql.test_integrations import env, adapters, prepared  # noqa: F401


@pytest.mark.parametrize('host', ['localhost', '127.0.0.1', '192.168.44.50', '10.1.2.3', '172.16.4.5', '[::1]', '[fd00::1]'])
def test_sandbox_development_allows_private_lan_return_urls_without_private_webhook_override(env, monkeypatch, host):
    monkeypatch.setenv('APP_ENV', 'development')
    monkeypatch.setenv('PUBLIC_FRONTEND_URL', f'http://{host}:3000')
    monkeypatch.setenv('PUBLIC_API_URL', f'http://{host}:8001')
    settings = DokuSettings.from_env()
    assert settings.frontend_url == f'http://{host}:3000'
    assert settings.notification_override_url is None
    assert settings.base_url == 'https://api-sandbox.doku.com'
    assert service.integration_status()['payment']['ready'] is True
    assert service.integration_status(admin=True)['payment']['configuration_notes']


@pytest.mark.parametrize('app_env,doku_env,front,api', [
    ('production', 'sandbox', 'http://192.168.44.50:3000', 'https://api.example.test'),
    ('development', 'production', 'http://192.168.44.50:3000', 'https://api.example.test'),
    ('staging', 'sandbox', 'http://192.168.44.50:3000', 'https://api.example.test'),
    ('development', 'sandbox', 'http://shop.example.com', 'https://api.example.test'),
    ('development', 'sandbox', 'http://8.8.8.8', 'https://api.example.test'),
    ('development', 'sandbox', 'http://0.0.0.0:3000', 'https://api.example.test'),
    ('development', 'sandbox', 'http://169.254.169.254', 'https://api.example.test'),
    ('development', 'sandbox', 'http://user:secret@192.168.44.50:3000', 'https://api.example.test'),
    ('development', 'sandbox', 'http://192.168.44.50:3000?debug=1', 'https://api.example.test'),
    ('development', 'sandbox', 'https://shop.example.test', 'http://api.example.test'),
])
def test_http_exceptions_do_not_weaken_production_or_accept_public_insecure_urls(env, monkeypatch, app_env, doku_env, front, api):
    for name, value in {'APP_ENV': app_env, 'DOKU_ENVIRONMENT': doku_env, 'PUBLIC_FRONTEND_URL': front, 'PUBLIC_API_URL': api}.items():
        monkeypatch.setenv(name, value)
    with pytest.raises(HTTPException): DokuSettings.from_env()
    assert service.integration_status()['payment']['ready'] is False
    admin = service.integration_status(admin=True)['payment']
    assert 'configuration_error' in admin
    assert 'secret' not in admin['configuration_error']
    assert 'configuration_error' not in service.integration_status()['payment']


def test_public_https_notification_override_still_used_in_production(env, monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production'); monkeypatch.setenv('DOKU_ENVIRONMENT', 'production')
    settings = DokuSettings.from_env()
    assert settings.notification_override_url == 'https://api.example.test/api/webhooks/doku'
    assert settings.base_url == 'https://api.doku.com'


def test_local_payment_request_keeps_lan_return_url_but_does_not_send_unreachable_override(adapters, monkeypatch):
    monkeypatch.setenv('PUBLIC_FRONTEND_URL', 'http://192.168.44.50:3000')
    monkeypatch.setenv('PUBLIC_API_URL', 'http://192.168.44.50:8001')
    adapters[0].settings = DokuSettings.from_env()
    async def run():
        async with isolated_database():
            d = await prepared(adapters)
            await create_checkout(d['alice'], d['req'], 'lan-checkout-once')
            request = adapters[0].calls[0][1]
            assert request['order']['callback_url'].startswith('http://192.168.44.50:3000/payment/')
            assert 'additional_info' not in request
    asyncio.run(run())
