"""Diagnose local configuration without printing merchant credentials."""
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import HTTPException
from mysql.config import load_runtime_environment
from integrations.config import DokuSettings, payment_provider
from mysql.integration_services import integration_status

load_runtime_environment()
report = {'payment': integration_status(admin=True)['payment'], 'app_env': os.environ.get('APP_ENV', 'development'),
          'missing': [name for name in ('DOKU_CLIENT_ID', 'DOKU_SECRET_KEY', 'PUBLIC_FRONTEND_URL') if not os.environ.get(name)]}
for name in ('PUBLIC_FRONTEND_URL', 'PUBLIC_API_URL'):
    try:
        parsed = urlsplit(os.environ.get(name, ''))
        report[name] = {'scheme': parsed.scheme, 'hostname': parsed.hostname, 'port': parsed.port}
    except ValueError:
        report[name] = {'invalid': True}
try:
    if payment_provider() == 'doku': DokuSettings.from_env()
except HTTPException as error:
    report['configuration_error'] = error.detail
print(json.dumps(report))
