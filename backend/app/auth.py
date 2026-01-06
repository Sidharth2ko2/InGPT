from fastapi import HTTPException
from app.config import ADMIN_USERNAME, ADMIN_PASSWORD

def authenticate(username: str, password: str):
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return True