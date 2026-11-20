import os
import time
from collections import defaultdict, deque
from typing import Any

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

LLM_URL = os.getenv("NITRO_LLM_URL", "http://llama:8081").rstrip("/")
ALLOWED_ORIGINS = [x.strip() for x in os.getenv("NITRO_CORS_ORIGINS", "*").split(",") if x.strip()]
MAX_REQUEST_CHARS = int(os.getenv("NITRO_MAX_REQUEST_CHARS", "12000"))
MAX_OUTPUT_TOKENS = int(os.getenv("NITRO_MAX_OUTPUT_TOKENS", "512"))
RATE_PER_MINUTE = int(os.getenv("NITRO_RATE_PER_MINUTE", "12"))
RATE_PER_DAY = int(os.getenv("NITRO_RATE_PER_DAY", "200"))

app = FastAPI(title="NITRO Core", version="0.1.0", description="Self-hosted NITRO AI inference gateway")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Lightweight per-process abuse protection. Use a shared store (e.g. Redis) before
# running multiple gateway replicas or opening a large public launch.
requests_by_ip: dict[str, deque[float]] = defaultdict(deque)

def rate_limited(ip: str) -> bool:
    now = time.time()
    q = requests_by_ip[ip]
    while q and q[0] < now - 86400:
        q.popleft()
    recent_minute = sum(1 for stamp in q if stamp >= now - 60)
    if recent_minute >= RATE_PER_MINUTE or len(q) >= RATE_PER_DAY:
        return True
    q.append(now)
    return False

@app.get("/")
async def root():
    return {"name": "NITRO Core", "status": "online", "version": "0.1.0"}

@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{LLM_URL}/health")
        model_status = "ready" if response.is_success else "starting"
    except Exception:
        model_status = "unreachable"
    return {"ok": model_status == "ready", "service": "nitro-core", "model": model_status}

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    ip = request.client.host if request.client else "unknown"
    if rate_limited(ip):
        return JSONResponse({"error": {"message": "درخواست‌های زیادی ارسال شده؛ کمی بعد دوباره تلاش کن.", "type": "rate_limit"}}, status_code=429)

    try:
        payload: dict[str, Any] = await request.json()
    except Exception:
        return JSONResponse({"error": {"message": "بدنه درخواست باید JSON معتبر باشد."}}, status_code=400)

    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages or len(messages) > 24:
        return JSONResponse({"error": {"message": "تعداد یا قالب پیام‌ها معتبر نیست."}}, status_code=400)

    cleaned = []
    total_chars = 0
    for item in messages:
        if not isinstance(item, dict) or item.get("role") not in {"system", "user", "assistant"}:
            return JSONResponse({"error": {"message": "نقش پیام معتبر نیست."}}, status_code=400)
        content = item.get("content", "")
        if not isinstance(content, str):
            return JSONResponse({"error": {"message": "متن پیام باید رشته باشد."}}, status_code=400)
        total_chars += len(content)
        cleaned.append({"role": item["role"], "content": content[:MAX_REQUEST_CHARS]})
    if total_chars > MAX_REQUEST_CHARS:
        return JSONResponse({"error": {"message": "متن گفتگو بیش از حد طولانی است."}}, status_code=413)

    # The browser cannot select arbitrary models or change server resource limits.
    outgoing = {
        "model": "nitro-qwen-1.5b",
        "messages": cleaned,
        "temperature": min(max(float(payload.get("temperature", 0.7)), 0.1), 1.2),
        "top_p": 0.9,
        "max_tokens": min(max(int(payload.get("max_tokens", 384)), 32), MAX_OUTPUT_TOKENS),
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=10.0)) as client:
            upstream = await client.post(f"{LLM_URL}/v1/chat/completions", json=outgoing)
        if upstream.status_code >= 400:
            return JSONResponse({"error": {"message": "موتور زبانی هنوز آماده نیست؛ چند لحظه دیگر امتحان کن.", "upstream_status": upstream.status_code}}, status_code=503)
        data = upstream.json()
        # Keep only the standard chat completion response shape.
        return {
            "id": data.get("id", "nitro-local"),
            "object": "chat.completion",
            "created": data.get("created", int(time.time())),
            "model": "NITRO Core · Qwen 1.5B",
            "choices": data.get("choices", []),
            "usage": data.get("usage", {}),
        }
    except httpx.TimeoutException:
        return JSONResponse({"error": {"message": "پاسخ موتور طول کشید و زمان انتظار تمام شد."}}, status_code=504)
    except Exception:
        return JSONResponse({"error": {"message": "ارتباط با موتور زبانی برقرار نشد."}}, status_code=503)
