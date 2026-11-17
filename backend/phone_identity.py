"""Canonical phone identifiers for password authentication (no OTP claim)."""
import re


def normalize_phone(value):
    if not isinstance(value, str) or len(value) > 40 or not re.fullmatch(r'[+0-9 ()-]+', value):
        raise ValueError('Nomor telepon tidak valid')
    number = re.sub(r'[ ()-]', '', value)
    if number.startswith('0'):
        number = '+62' + number[1:]
    elif number.startswith('62'):
        number = '+' + number
    if not re.fullmatch(r'\+[1-9][0-9]{7,14}', number):
        raise ValueError('Gunakan nomor 08…, 628…, atau format internasional +kode negara')
    return number
