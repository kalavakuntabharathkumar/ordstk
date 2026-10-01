import os, time, hashlib, hmac, base64, json
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Demo-only compact HMAC token implementation; use a vetted JWT library in production.
SECRET = os.getenv("JWT_SECRET", "local-development-secret-change-me").encode()
bearer = HTTPBearer(auto_error=False)

def issue_token(username: str, role: str) -> str:
    payload = json.dumps({"sub": username, "role": role, "exp": int(time.time()) + 3600}).encode()
    body = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    sig = hmac.new(SECRET, body.encode(), hashlib.sha256).digest()
    return body + "." + base64.urlsafe_b64encode(sig).decode().rstrip("=")

def require_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Bearer token required")
    try:
        body, signature = credentials.credentials.split(".", 1)
        expected = base64.urlsafe_b64encode(hmac.new(SECRET, body.encode(), hashlib.sha256).digest()).decode().rstrip("=")
        if not hmac.compare_digest(signature, expected):
            raise ValueError("bad signature")
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if payload["exp"] < int(time.time()):
            raise ValueError("expired")
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def require_roles(*roles):
    def dependency(user=Depends(require_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return user
    return dependency
