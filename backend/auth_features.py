import os


def phone_auth_enabled():
    return os.environ.get('AUTH_PHONE_ENABLED', 'false').strip().lower() in ('true', '1')
