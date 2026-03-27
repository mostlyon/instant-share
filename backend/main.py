import time
import string
import random
import base64
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

app = FastAPI()

# Enable CORS so your Cloudflare frontend can talk to your Render backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
data_store = {}
EXPIRY_TIME = 600  # 10 minutes (600 seconds)

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def cleanup_expired():
    """Removes data older than 10 minutes."""
    now = time.time()
    expired_keys = [k for k, v in data_store.items() if now > v["expiry"]]
    for k in expired_keys:
        del data_store[k]

@app.get("/")
def health_check():
    return {"status": "Instant Share API is running"}

@app.post("/send")
async def send_data(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    cleanup_expired()
    
    # Validation: Must have at least one
    if not text and not file:
        raise HTTPException(status_code=400, detail="No content provided")

    code = generate_code()
    
    file_b64 = None
    filename = None
    if file:
        content = await file.read()
        # Convert binary file to Base64 string for JSON safety
        file_b64 = base64.b64encode(content).decode('utf-8')
        filename = file.filename

    data_store[code] = {
        "text": text,
        "file": file_b64,
        "filename": filename,
        "expiry": time.time() + EXPIRY_TIME
    }
    
    return {"code": code, "expires_in": "10 minutes"}

@app.get("/retrieve/{code}")
async def retrieve_data(code: str):
    cleanup_expired()
    code = code.upper()
    
    if code not in data_store:
        raise HTTPException(status_code=404, detail="Code invalid or expired")
    
    return data_store[code]