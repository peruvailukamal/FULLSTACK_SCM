from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import datetime

# Rate Limit Imports
# Rate limiter removed

# IP-based access control removed

# Import Routes
from backend.routes import users, shipments, stream
# Recaptcha ConfigS
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY") # Load from .env
load_dotenv()

app = FastAPI()

# Rate limiter and IP access middleware removed per configuration

# --- 3. CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Path Setup ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
TEMPLATE_DIR = os.path.join(FRONTEND_DIR, "templates")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATE_DIR)
templates.env.globals["now"] = datetime.datetime.now

# --- API Routes ---
app.include_router(users.router, prefix="/api/v1", tags=["Users"])
app.include_router(shipments.router, prefix="/api/v1", tags=["Shipments"])
app.include_router(stream.router, tags=["Stream"])

# --- Frontend Page Routes ---
@app.get("/")
async def serve_index(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "RECAPTCHA_SITE_KEY": RECAPTCHA_SITE_KEY})

@app.get("/signup")
async def serve_signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/dashboard")
async def serve_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/create-shipment")
async def serve_create_shipment(request: Request):
    return templates.TemplateResponse("create_shipment.html", {"request": request})

@app.get("/my-shipments")
async def serve_my_shipments(request: Request):
    return templates.TemplateResponse("my_shipments.html", {"request": request})

@app.get("/data-stream")
async def serve_data_stream(request: Request):
    return templates.TemplateResponse("data_stream.html", {"request": request})

@app.get("/account")
async def serve_account(request: Request):
    return templates.TemplateResponse("account.html", {"request": request})

@app.get("/forgot-password")
async def serve_forgot_password(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return templates.TemplateResponse("error.html", {"request": request, "error_code": "404", "error_message": "Page Not Found"})