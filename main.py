from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import logging

# Database helpers are pre-configured in the environment
# They expose: db, create_document, get_documents
try:
    from database import create_document, get_documents
except Exception as e:
    create_document = None
    get_documents = None
    logging.warning("Database helper import failed: %s", e)

app = FastAPI(title="Font Madrid API", version="1.0.0")

# CORS - allow frontend dev server and generic usage
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class ContactPayload(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    phone: str = Field(..., min_length=6, max_length=40)
    email: Optional[EmailStr] = None
    message: str = Field(..., min_length=5, max_length=4000)
    honeypot: Optional[str] = ""  # simple spam trap (hidden field)


@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.get("/test")
async def test_db():
    if get_documents is None:
        return {"ok": False, "message": "Database helpers not available in this environment"}
    try:
        docs = await get_documents("contactmessage", {}, limit=1)
        return {"ok": True, "connected": True, "sample": docs}
    except Exception as e:
        logging.exception("DB test failed")
        return {"ok": False, "connected": False, "error": str(e)}


@app.post("/contact")
async def contact(payload: ContactPayload, request: Request):
    # Basic spam check
    if payload.honeypot:
        # silently accept but do nothing
        return {"ok": True}

    data = {
        "name": payload.name.strip(),
        "phone": payload.phone.strip(),
        "email": (payload.email or "").strip(),
        "message": payload.message.strip(),
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "created_at": datetime.utcnow(),
        "source": "website",
    }

    if create_document is None:
        logging.warning("create_document not available; skipping persistence")
        return {"ok": True, "stored": False}

    try:
        inserted = await create_document("contactmessage", data)
        return {"ok": True, "stored": True, "id": str(inserted.get("_id", ""))}
    except Exception as e:
        logging.exception("Failed to store contact message")
        raise HTTPException(status_code=500, detail="Failed to submit your request. Please try again later.")


# Basic sitemap and robots to help SEO during preview
@app.get("/robots.txt", response_class=None)
async def robots_txt():
    content = """User-agent: *\nAllow: /\nSitemap: /sitemap.txt\n"""
    return app.response_class(content=content, media_type="text/plain")


@app.get("/sitemap.txt", response_class=None)
async def sitemap_txt():
    urls = [
        "/",
        "/es",
        "/en",
        "/ca",
        "/servicios",
        "/nosotros",
        "/contacto",
        "/trabajos-verticales-madrid",
        "/fontaneria-madrid",
        "/impermeabilizacion-cubiertas-madrid",
    ]
    content = "\n".join(urls)
    return app.response_class(content=content, media_type="text/plain")
