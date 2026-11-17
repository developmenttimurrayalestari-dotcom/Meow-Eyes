"""Verify Facebook user tokens with Meta; credentials never come from browser profile fields."""
import hashlib
import hmac
import os
import re
import time
import requests
from fastapi import HTTPException
from pydantic import EmailStr, TypeAdapter, ValidationError


def facebook_config():
    app_id = os.environ.get('FACEBOOK_APP_ID', '').strip()
    secret = os.environ.get('FACEBOOK_APP_SECRET', '').strip()
    version = os.environ.get('FACEBOOK_GRAPH_VERSION', 'v27.0').strip()
    enabled = bool(re.fullmatch(r'[0-9]+', app_id) and secret and re.fullmatch(r'v[0-9]+\.0', version))
    return {'enabled': enabled, 'app_id': app_id if enabled else None, 'version': version if enabled else None}


def verify_facebook_token(token):
    config = facebook_config()
    if not config['enabled']:
        raise HTTPException(503, 'Login Facebook belum dikonfigurasi')
    secret = os.environ['FACEBOOK_APP_SECRET'].strip()
    base = 'https://graph.facebook.com/' + config['version']
    try:
        with requests.Session() as session:
            reply = session.get(base + '/debug_token', params={'input_token': token},
                headers={'Authorization': 'Bearer ' + config['app_id'] + '|' + secret}, timeout=10, allow_redirects=False)
            if reply.status_code >= 500: raise HTTPException(503, 'Facebook sementara tidak dapat dihubungi')
            if reply.status_code != 200: raise HTTPException(401, 'Sesi Facebook tidak valid. Silakan masuk ulang.')
            data = reply.json().get('data', {})
            now = time.time()
            expires, access_expires = data.get('expires_at'), data.get('data_access_expires_at', 0)
            subject = data.get('user_id')
            if (data.get('is_valid') is not True or data.get('app_id') != config['app_id']
                    or not isinstance(subject, str) or not re.fullmatch(r'[0-9]{1,128}', subject)
                    or type(expires) is not int or expires <= now
                    or type(access_expires) is not int or (access_expires != 0 and access_expires <= now)
                    or data.get('type', 'USER') != 'USER'):
                raise HTTPException(401, 'Sesi Facebook tidak valid. Silakan masuk ulang.')
            proof = hmac.new(secret.encode(), token.encode(), hashlib.sha256).hexdigest()
            reply = session.get(base + '/me', params={'fields': 'id,name,email,picture', 'appsecret_proof': proof},
                headers={'Authorization': 'Bearer ' + token}, timeout=10, allow_redirects=False)
            if reply.status_code >= 500: raise HTTPException(503, 'Facebook sementara tidak dapat dihubungi')
            if reply.status_code != 200: raise HTTPException(401, 'Identitas Facebook gagal diverifikasi')
            profile = reply.json()
    except requests.RequestException:
        raise HTTPException(503, 'Facebook sementara tidak dapat dihubungi') from None
    except (ValueError, AttributeError, TypeError):
        raise HTTPException(401, 'Respons Facebook tidak valid') from None
    if not isinstance(profile, dict) or profile.get('id') != subject:
        raise HTTPException(401, 'Identitas Facebook tidak sesuai')
    email = None
    if profile.get('email'):
        try: email = str(TypeAdapter(EmailStr).validate_python(profile['email'])).lower()
        except ValidationError: raise HTTPException(401, 'Email Facebook tidak valid') from None
    name = profile.get('name')
    if not isinstance(name, str) or not name.strip(): raise HTTPException(401, 'Nama Facebook tidak tersedia')
    picture = profile.get('picture', {})
    picture = picture.get('data') if isinstance(picture, dict) else None
    picture = picture.get('url') if isinstance(picture, dict) else None
    return {'subject': subject, 'email': email, 'name': name.strip()[:255],
            'picture': picture if isinstance(picture, str) and picture.startswith('https://') and len(picture) <= 2048 else None}
