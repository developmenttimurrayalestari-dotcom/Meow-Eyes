"""Safe Everpro configuration/token probe; never creates orders or prints tokens.

Run from backend using its venv:
    python -m integrations.check_everpro --check-auth
On Linux, --pid accepts the backend PID to include its startup environment.
"""
import argparse
import asyncio
import hashlib
import hmac
import json
import os
from pathlib import Path

import httpx
from dotenv import dotenv_values
from fastapi import HTTPException

from integrations.config import EverproSettings
from integrations.common import ProviderError
from mysql.config import DEFAULT_ENV_FILE

KEYS = ('EVERPRO_ENVIRONMENT', 'EVERPRO_BASE_URL', 'EVERPRO_CLIENT_KEY', 'EVERPRO_CLIENT_SECRET', 'EVERPRO_API_VERSION', 'EVERPRO_AUTH_VERSION', 'EVERPRO_DATA_SOURCE', 'EVERPRO_REFERENCE_DATABASE')


def credential_fingerprint(settings):
    # An opt-in comparison tag, never the key, secret or token itself. Keep the
    # exact input bytes: whitespace and case differences must remain visible.
    return hmac.new(settings.client_secret.encode('utf-8'),
                    b'meow-eyes-everpro-v1\0' + settings.client_key.encode('utf-8'), hashlib.sha256).hexdigest()[:16]


def environment_report(file_values, process_values):
    report = {}
    for key in KEYS:
        value = process_values.get(key, file_values.get(key))
        item = {'source': 'process' if key in process_values else 'file', 'present': bool(value)}
        if key in process_values:
            item['matches_file'] = process_values[key] == file_values.get(key)
        if key in ('EVERPRO_CLIENT_KEY', 'EVERPRO_CLIENT_SECRET'):
            item['surrounding_whitespace'] = bool(value and value != value.strip())
        report[key] = item
    return report


async def check_auth(settings, *, transport=None, reference_store=None):
    if getattr(settings, 'data_source', 'api') == 'database':
        from integrations.everpro import EverproClient
        client = EverproClient(settings, transport=transport, reference_store=reference_store)
        try:
            await client.request('GET', '/shipment/v1/logistics')
            return {'ok':True, 'http_status':200, 'reason':'shared_token_valid', 'token_source':client.token_source}
        except ProviderError as error:
            return {'ok':False, 'reason':error.code}
    try:
        async with httpx.AsyncClient(transport=transport, timeout=httpx.Timeout(20, connect=5), follow_redirects=False) as client:
            response = await client.post(settings.base_url + getattr(settings, 'auth_path', '/auth/v1/token'), headers={'Accept': 'application/json'},
                json={'client_key': settings.client_key, 'client_secret': settings.client_secret})
        report = {'http_status': response.status_code, 'ok': False}
        try:
            body = response.json() if len(response.content) <= 2_000_000 else None
        except (ValueError, UnicodeError):
            body = None
        if not isinstance(body, dict):
            report['reason'] = 'non_json_or_invalid_response'
            return report
        data = body.get('data')
        report['ok'] = (response.status_code == 200 and isinstance(data, dict)
                        and isinstance(data.get('token'), str) and bool(data['token'])
                        and data.get('token_type', 'Bearer') == 'Bearer')
        if report['ok']:
            report['reason'] = 'token_received'
        elif response.status_code == 404 and str(body.get('message', '')).strip().lower() == 'user not found':
            report['reason'] = 'client_not_found_in_environment'
        else:
            report['reason'] = 'authentication_rejected'
        # Provider bodies can echo credentials: only fixed classifications leave
        # this function. Never return the raw body, headers, token or exception.
        return report
    except httpx.HTTPError:
        return {'ok': False, 'reason': 'network_or_tls_error'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-auth', action='store_true', help='Request a token only; never create an order')
    parser.add_argument('--pid', type=int, help='Linux backend PID; inspect its startup environment instead of this shell')
    parser.add_argument('--fingerprint', action='store_true', help='Include an opaque comparison tag for the credential pair')
    args = parser.parse_args()
    file_values = dotenv_values(DEFAULT_ENV_FILE, interpolate=False)
    process_values = dict(os.environ)
    if args.pid is not None:
        if args.pid < 1: parser.error('PID must be positive')
        try:
            raw = Path('/proc', str(args.pid), 'environ').read_bytes()
            process_values = dict(entry.decode().split('=', 1) for entry in raw.split(b'\0') if b'=' in entry)
        except (OSError, UnicodeError):
            print(json.dumps({'ok': False, 'reason': 'cannot_read_process_environment'}))
            return 1
    report = {'env_file': str(DEFAULT_ENV_FILE), 'configuration': environment_report(file_values, process_values)}
    if args.pid is not None:
        report['note'] = 'Reconstructed from process startup environment and CURRENT file; restart is still required after file changes.'
    # Match load_runtime_environment: explicit process values override the file.
    effective = {key: value for key, value in file_values.items() if value is not None}
    effective.update(process_values)
    os.environ.clear()
    os.environ.update(effective)
    try:
        settings = EverproSettings.from_env(require_origin=False)
    except HTTPException:
        report.update(ok=False, reason='invalid_everpro_configuration')
        print(json.dumps(report, indent=2))
        return 1
    report.update(environment=settings.environment, base_url=settings.base_url, api_version=settings.api_version,
                  data_source=settings.data_source, auth_path=settings.auth_path if settings.data_source == 'api' else None, ok=True)
    if settings.data_source == 'database': report['reference_database'] = settings.reference_database
    if args.fingerprint:
        report['credential_fingerprint'] = credential_fingerprint(settings) if settings.data_source == 'api' else 'not_used_database_mode'
    if args.check_auth:
        report['authentication'] = asyncio.run(check_auth(settings))
        report['ok'] = report['authentication']['ok']
    print(json.dumps(report, indent=2))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
