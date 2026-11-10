"""Demo-only clinic PIN gate. Never send the configured PIN to the browser."""
import hashlib
import hmac
import os
from pathlib import Path
import secrets
from fastapi import Header, HTTPException

SECRET=Path(__file__).resolve().parents[2]/'cache/clinic_device_secret'


def clinic_pin():
    value=os.getenv('CLINIC_PIN','1234')
    if len(value)!=4 or not value.isascii() or not value.isdigit():
        raise HTTPException(503,'CLINIC_PIN must contain exactly four digits.')
    return value


def device_token():
    SECRET.parent.mkdir(parents=True,exist_ok=True)
    try:
        with SECRET.open('x') as stream:stream.write(secrets.token_hex(32))
        SECRET.chmod(0o600)
    except FileExistsError:
        pass
    return hmac.new(SECRET.read_bytes(),clinic_pin().encode(),hashlib.sha256).hexdigest()


def require_clinic(authorization:str|None=Header(default=None)):
    if not authorization or not hmac.compare_digest(authorization.encode(),('Bearer '+device_token()).encode()):
        raise HTTPException(401,'Unlock Doctor view with the clinic PIN.')
