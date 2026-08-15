"""Tiny round-robin load balancer for 4 vLLM replicas.
Listens on 0.0.0.0:8210 and routes any POST /v1/chat/completions to ports
8200..8203 in round-robin. No state, no auth — for local benchmarking only.
"""
import asyncio
import itertools
import os
import sys

import httpx
from fastapi import FastAPI, Request, Response

UPSTREAMS = [
    f"http://127.0.0.1:{int(os.environ.get('LB_BASE_PORT', 8200)) + i}"
    for i in range(int(os.environ.get('LB_N_REPLICAS', 4)))
]
print(f"[lb] upstreams: {UPSTREAMS}", flush=True)

_rr = itertools.cycle(UPSTREAMS)
_lock = asyncio.Lock()
app = FastAPI()
client = httpx.AsyncClient(timeout=httpx.Timeout(180.0, read=180.0, connect=10.0))


async def _proxy(request: Request, path: str):
    async with _lock:
        upstream = next(_rr)
    url = f"{upstream}{path}"
    body = await request.body()
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in {"host", "content-length"}}
    try:
        resp = await client.request(
            method=request.method,
            url=url,
            content=body,
            headers=headers,
            params=request.query_params,
        )
        return Response(content=resp.content, status_code=resp.status_code,
                        headers={"content-type": resp.headers.get("content-type", "application/json")})
    except Exception as e:
        return Response(content=str(e).encode(), status_code=502)


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def catch_all(request: Request, full_path: str):
    return await _proxy(request, "/" + full_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("LB_PORT", 8210)),
                log_level="warning")
