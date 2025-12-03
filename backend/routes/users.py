from datetime import datetime, timedelta
from fastapi import APIRouter, Body, HTTPException, Depends, Request, Header
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
import secrets
import random
import os
import smtplib
from email.mime.text import MIMEText

# Models & Config
from backend.models.user import (
    UserSchema,
    ForgotPasswordSchema,
    ResetPasswordSchema
)
from backend.config.database import user_collection, otp_collection
from backend.auth.jwt_handler import signJWT, decodeJWT
from backend.middleware.security import JWTBearer, JWTAdmin
from bson import ObjectId
from datetime import datetime

# Helpers
from backend.auth.recaptcha import verify_recaptcha

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------- EMAIL HELPER FOR OTP ----------
def send_otp_email(recipient_email: str, otp: str) -> None:
    """
    Sends the OTP to the user's email using SMTP.
    Uses env vars:
      - MAIL_USER
      - MAIL_PASS
      - MAIL_SERVER
      - MAIL_PORT
    """
    sender_email = os.getenv("MAIL_USER")
    sender_password = os.getenv("MAIL_PASS")
    smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("MAIL_PORT", "587"))

    subject = "Your SCMXpertLite Password Reset OTP"
    body = (
        f"Hello,\n\n"
        f"Your OTP for resetting your SCMXpertLite password is: {otp}\n\n"
        f"This code is valid for 5 minutes.\n"
        f"If you did not request this, you can ignore this email.\n\n"
        f"Regards,\nSCMXpertLite"
    )

    # If email config is missing, fall back to printing so app still works
    if not sender_email or not sender_password:
        print("\n" + "=" * 40)
        print(" EMAIL CONFIG NOT SET - FALLBACK TO CONSOLE ")
        print(f" To: {recipient_email}")
        print(f" OTP: {otp}")
        print("=" * 40 + "\n")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print(f"OTP email sent to {recipient_email}")
    except smtplib.SMTPAuthenticationError as e:
        # Bad credentials: log and fallback to console, do NOT crash the API
        print("\n" + "=" * 40)
        print(" SMTP AUTHENTICATION ERROR ")
        print(e)
        print(f" Fallback OTP for {recipient_email}: {otp}")
        print("=" * 40 + "\n")
    except Exception as e:
        # Any other SMTP error
        print("\n" + "=" * 40)
        print(" SMTP ERROR WHILE SENDING OTP ")
        print(e)
        print(f" Fallback OTP for {recipient_email}: {otp}")
        print("=" * 40 + "\n")


def send_admin_request_email(user_email: str, username: str) -> None:
    """
    Notify configured admin email address that a user requested admin access.
    Uses env var `ADMIN_EMAIL`; falls back to console if not configured.
    """
    admin_email = os.getenv("ADMIN_EMAIL")
    sender_email = os.getenv("MAIL_USER")
    sender_password = os.getenv("MAIL_PASS")
    smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("MAIL_PORT", "587"))

    subject = "SCMXpertLite Admin Access Request"
    body = f"""Admin,

User '{username}' with email {user_email} has requested admin access.

Please review the requests in the admin panel.

Regards,
SCMXpertLite
"""

    if not admin_email:
        print("ADMIN_EMAIL not set - admin request from:", user_email)
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email or "no-reply@scmxpertlite.local"
    msg["To"] = admin_email

    # If email config is missing, print to console
    if not sender_email or not sender_password:
        print("\n" + "=" * 40)
        print("ADMIN REQUEST (email fallback)")
        print(f" To: {admin_email}")
        print(f" From: {user_email} ({username})")
        print(msg.as_string())
        print("=" * 40 + "\n")
        return

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print(f"Admin request email sent to {admin_email}")
    except Exception as e:
        print("Failed to send admin request email:", e)
    


# --- 1. SIGNUP ROUTE ---
@router.post("/signup")
async def create_user(request: Request, users: UserSchema = Body(...)):
    # Check if user exists
    if await user_collection.find_one({"email": users.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = pwd_context.hash(users.password)
    
    # Create User Dictionary
    user_dict = {
        "username": users.username, # Saves the username provided at signup
        "email": users.email,
        "password": hashed_password,
        "auth_provider": "local",
        "last_login": datetime.now().isoformat(), # FIX: Set initial login time
        "is_admin": False,
        "admin_request_status": "none",
        "admin_requested_at": None
    }
    
    # Save to DB
    new_user = await user_collection.insert_one(user_dict)
    return signJWT(str(new_user.inserted_id), users.email)

# --- 2. LOGIN ROUTE ---
@router.post("/token")
async def login(
    request: Request, 
    form_data: OAuth2PasswordRequestForm = Depends(),
    x_recaptcha_token: str = Header(None) 
):
    # A. Verify ReCAPTCHA
    if not x_recaptcha_token:
         raise HTTPException(status_code=400, detail="ReCAPTCHA is missing.")
    
    is_valid_captcha = verify_recaptcha(x_recaptcha_token)
    if not is_valid_captcha:
        raise HTTPException(status_code=400, detail="Invalid ReCAPTCHA. Are you a robot?")

    # B. Standard Login Logic
    user = await user_collection.find_one({"email": form_data.username})
    if user and pwd_context.verify(form_data.password, user["password"]):
        
        # FIX: Update Last Login Time
        await user_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.now().isoformat()}}
        )
        
        return signJWT(str(user["_id"]), user["email"])
    
    raise HTTPException(status_code=401, detail="Invalid login details")

# NOTE: Google SSO route removed (Google SSO disabled)

# --- 4. PASSWORD RESET LOGIC ---
def generate_otp():
    return str(random.randint(100000, 999999))

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordSchema):
    # 1. Check if user exists
    user = await user_collection.find_one({"email": payload.email})
    if not user:
        # Do not reveal whether email exists
        return {"message": "If email exists, OTP sent."}

    # 2. Generate OTP
    otp = generate_otp()

    # 3. Save to DB with expiration (5 minutes)
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    # 🔹 IMPORTANT: remove any old OTPs for this email
    await otp_collection.delete_many({"email": payload.email})

    await otp_collection.insert_one({
        "email": payload.email,
        "otp": otp,
        "expires_at": expires_at
    })

    # 4. Send email
    send_otp_email(payload.email, otp)

    return {"message": "OTP sent to email"}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordSchema):
    # 1. Find OTP record
    record = await otp_collection.find_one({"email": payload.email})
    
    if not record:
        raise HTTPException(status_code=400, detail="Invalid request or OTP expired")
    
    # 2. Verify OTP and Expiration
    if record["otp"] != payload.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
        
    if datetime.utcnow() > record["expires_at"]:
        raise HTTPException(status_code=400, detail="OTP Expired")

    # 3. Hash new password
    hashed_password = pwd_context.hash(payload.new_password)

    # 4. Update User Password
    await user_collection.update_one(
        {"email": payload.email},
        {"$set": {"password": hashed_password}}
    )

    # 5. Cleanup OTP
    await otp_collection.delete_one({"_id": record["_id"]})

    return {"message": "Password updated successfully"}

# --- 5. GET CURRENT USER ---
@router.get("/me", dependencies=[Depends(JWTBearer())])
async def get_current_user(token: str = Depends(JWTBearer())):
    decoded = decodeJWT(token)
    user = await user_collection.find_one({"email": decoded["email"]})
    if user:
        return {
            "id": str(user["_id"]),
            "username": user.get("username"), 
            "email": user["email"],
            "last_login": user.get("last_login"),
            "is_admin": user.get("is_admin", False),
            "admin_request_status": user.get("admin_request_status", "none")
        }
    raise HTTPException(status_code=404, detail="User not found")


# --- ADMIN PRIVILEGE REQUEST ---
@router.post("/admin/request", dependencies=[Depends(JWTBearer())])
async def request_admin(token: str = Depends(JWTBearer())):
    decoded = decodeJWT(token)
    if not decoded:
        raise HTTPException(status_code=403, detail="Invalid token")

    email = decoded.get("email")
    user = await user_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # If already admin or already pending, return appropriate message
    if user.get("is_admin"):
        return {"message": "User already has admin privileges"}
    if user.get("admin_request_status") == "pending":
        return {"message": "Admin request already pending"}

    await user_collection.update_one(
        {"email": email},
        {"$set": {"admin_request_status": "pending", "admin_requested_at": datetime.utcnow()}}
    )

    # Send notification to admins (best-effort)
    try:
        send_admin_request_email(email, user.get("username") or email)
    except Exception as e:
        print('Failed to send admin notification:', e)

    return {"message": "Admin request submitted"}


# --- ADMIN: List pending requests (admin only) ---
@router.get("/admin/requests", dependencies=[Depends(JWTAdmin())])
async def list_admin_requests(token: str = Depends(JWTAdmin())):
    pending = []
    async for u in user_collection.find({"admin_request_status": "pending"}):
        pending.append({
            "id": str(u.get("_id")),
            "username": u.get("username"),
            "email": u.get("email"),
            "requested_at": u.get("admin_requested_at")
        })
    return pending


# --- ADMIN: Approve request ---
@router.post("/admin/approve/{user_id}", dependencies=[Depends(JWTAdmin())])
async def approve_admin_request(user_id: str, token: str = Depends(JWTAdmin())):
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user id")

    user = await user_collection.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await user_collection.update_one({"_id": oid}, {"$set": {"is_admin": True, "admin_request_status": "approved"}})
    return {"message": "User approved as admin"}


# --- ADMIN: Reject request ---
@router.post("/admin/reject/{user_id}", dependencies=[Depends(JWTAdmin())])
async def reject_admin_request(user_id: str, token: str = Depends(JWTAdmin())):
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user id")

    user = await user_collection.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await user_collection.update_one({"_id": oid}, {"$set": {"admin_request_status": "rejected"}})
    return {"message": "Admin request rejected"}
