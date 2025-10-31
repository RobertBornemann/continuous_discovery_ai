# api.py
import os, json, time, hashlib, asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from discovery import InterviewAnalyzer

DEMO_PATH = Path("data/interviews/mock_interview.txt")
CACHE_PATH = Path("data/interviews/demo_cache.json")

app = FastAPI(title="Discovery AI Demo API")
analyzer = InterviewAnalyzer()


@app.get("/healthz")
def healthz():
    return {"ok": True, "has_openai_key": bool(os.getenv("OPENAI_API_KEY"))}

class DemoResponse(BaseModel):
    run_id: str
    steps: list[str]
    insights: dict | None

def _load_demo_text() -> str:
    if not DEMO_PATH.exists():
        raise HTTPException(500, "Demo transcript missing.")
    return DEMO_PATH.read_text(encoding="utf-8")

def _cache_key(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

@app.post("/demo/run", response_model=DemoResponse)
async def run_demo(mode: str = "auto"):
    """
    mode:
      - 'cached' -> return cached insights (fast)
      - 'live'   -> force a real OpenAI run (expensive)
      - 'auto'   -> use cache if present, otherwise run once then cache
    """
    text = _load_demo_text()
    key = _cache_key(text)
    run_id = f"demo-{key}"

    # Try cache
    if mode in ("auto", "cached") and CACHE_PATH.exists():
        data = json.loads(CACHE_PATH.read_text())
        if data.get("key") == key:
            return DemoResponse(
                run_id=run_id,
                steps=["Loading cached insights", "Rendering…", "Done"],
                insights=data["insights"],
            )

    # Basic guardrails
    if mode == "live":
        # super-simple IP budget/lock can go here if you like
        pass

    # Real run (first time) with visible steps
    steps = ["Reading transcript", "Extracting insights", "Validating schema", "Preparing export"]
    # (Optional) small sleeps so UI can animate steps without SSE
    await asyncio.sleep(0.2)

    insights = await analyzer.analyze(text, audit=True, validate=True)

    # Cache to disk
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps({
        "key": key,
        "insights": insights.model_dump(),
        "cached_at": time.time(),
    }), encoding="utf-8")

    return DemoResponse(run_id=run_id, steps=steps + ["Done"], insights=insights.model_dump())
