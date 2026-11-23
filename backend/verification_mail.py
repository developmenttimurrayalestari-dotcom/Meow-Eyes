"""SMTP verification messages. Never log links, credentials or token values."""
import os
import smtplib
import ssl
from email.message import EmailMessage
from fastapi import HTTPException
from integrations.config import public_frontend_url


def ready():
    auth = os.getenv('SMTP_AUTH_REQUIRED', 'true').lower() not in ('false', '0')
    return bool(os.getenv('SMTP_HOST') and os.getenv('SMTP_FROM_EMAIL') and os.getenv('PUBLIC_FRONTEND_URL')
        and (not auth or (os.getenv('SMTP_USERNAME') and os.getenv('SMTP_PASSWORD'))))


def send_verification(email, token):
    if not ready():
        raise HTTPException(503, 'Email verifikasi belum dikonfigurasi. Hubungi toko.')
    message = EmailMessage()
    message['Subject'] = 'Verifikasi email akun Meow Eyes'
    message['From'] = os.environ['SMTP_FROM_EMAIL']
    message['To'] = email
    url = public_frontend_url() + '/verify-email#token=' + token
    message.set_content('Verifikasi email akun Meow Eyes melalui tautan berikut:\n\n' + url +
        '\n\nTautan berlaku 30 menit dan hanya dapat digunakan sekali. Jika Anda tidak meminta verifikasi, abaikan email ini.')
    try:
        port = int(os.getenv('SMTP_PORT', '587'))
        mode = os.getenv('SMTP_SECURITY', 'starttls').lower()
        if mode not in ('starttls', 'ssl'):
            raise ValueError('SMTP requires TLS')
        client_type = smtplib.SMTP_SSL if mode == 'ssl' else smtplib.SMTP
        kwargs = {'timeout': 15}
        if mode == 'ssl': kwargs['context'] = ssl.create_default_context()
        with client_type(os.environ['SMTP_HOST'], port, **kwargs) as client:
            if mode == 'starttls': client.starttls(context=ssl.create_default_context())
            if os.getenv('SMTP_USERNAME'):
                client.login(os.environ['SMTP_USERNAME'], os.environ.get('SMTP_PASSWORD', ''))
            client.send_message(message)
    except (OSError, ValueError, smtplib.SMTPException):
        raise HTTPException(503, 'Email verifikasi belum berhasil dikirim. Silakan coba kembali.') from None
