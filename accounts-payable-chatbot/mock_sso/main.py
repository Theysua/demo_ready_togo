import os
import httpx
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError
from dotenv import load_dotenv

# Load Dify URL and API key from parent's parent directory .env if not set
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
DIFY_API_KEY = os.getenv("CHATFLOW_ACCOUNT_PAYABLE_API")
if not DIFY_API_KEY:
    print("Warning: CHATFLOW_ACCOUNT_PAYABLE_API not found in .env")

app = FastAPI(title="Goodyear AP Chatbot Backend")

# Secret key for JWT signing (mock)
SECRET_KEY = "goodyear-mock-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock user database
USERS_DB = {
    "admin@demo.com": {"password": "password123", "role": "internal", "vendor_id": None},
    "vendor@demo.com": {"password": "password123", "role": "vendor", "vendor_id": "VEND001"}
}

class LoginRequest(BaseModel):
    email: str
    password: str

class ChatMessage(BaseModel):
    query: str
    user: str
    conversation_id: Optional[str] = None

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/api/auth/login")
async def login(req: LoginRequest):
    user = USERS_DB.get(req.email)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    token_data = {"sub": req.email, "role": user["role"], "vendor_id": user["vendor_id"]}
    access_token = create_access_token(data=token_data)
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_info": {"email": req.email, "role": user["role"], "vendor_id": user["vendor_id"]}
    }

async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/chat")
async def chat(message: ChatMessage, current_user: dict = Depends(get_current_user)):
    user_email = current_user.get("sub")
    user_role = current_user.get("role")
    
    # 1. Prepare inputs with identity injected stealthily
    dify_payload = {
        "inputs": {
            "user_email": user_email,
            "user_role": user_role
        },
        "query": message.query,
        "response_mode": "streaming", # Stream and aggregate instead of blocking due to workflow API behaviors
        "user": message.user
    }

    if message.conversation_id:
        dify_payload["conversation_id"] = message.conversation_id
        
    # 2. Forward request to Dify API
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async def stream_generator():
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                "http://localhost/v1/chat-messages",
                json=dify_payload,
                headers=headers
            ) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes():
                    yield chunk

    try:
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files at the end to not catch API routes
import os as _os
static_dir = _os.path.join(_os.path.dirname(__file__), "static")
if not _os.path.exists(static_dir):
    _os.makedirs(static_dir)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
