from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from backend.auth.jwt_handler import decodeJWT
import os
from dotenv import load_dotenv

load_dotenv()

# Import DB collection for admin checks
from backend.config.database import user_collection

# --- JWT Security ---
class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            if not decodeJWT(credentials.credentials):
                raise HTTPException(status_code=403, detail="Invalid or expired token.")
            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")
# Admin-only bearer that verifies token + user is admin
class JWTAdmin(HTTPBearer):
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTAdmin, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403, detail="Invalid authentication scheme.")
            decoded = decodeJWT(credentials.credentials)
            if not decoded:
                raise HTTPException(status_code=403, detail="Invalid or expired token.")

            # Lookup user in DB and ensure is_admin
            user = await user_collection.find_one({"email": decoded.get("email")})
            if not user or not user.get("is_admin"):
                raise HTTPException(status_code=403, detail="Admin privileges required.")

            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")
# IP Access control removed