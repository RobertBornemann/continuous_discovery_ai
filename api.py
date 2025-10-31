# api.py
import os, json, time, hashlib, asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from discovery import InterviewAnalyzer
from fastapi import FastAPI, HTTPException, Request, Header, Query

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

HERE = Path(__file__).parent
VARIANT_MAP = {
    "sanitized": HERE / "data" / "interviews" / "sanitized.txt",
    "sensitive": HERE / "data" / "interviews" / "sensitive.txt",
}

CACHE_DIR = Path(os.getenv("CACHE_DIR", "/tmp/discovery_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def cache_path_for(variant: str) -> Path:
    return CACHE_DIR / f"{variant}_cache.json"

def load_demo_text(variant: str) -> str:
    # distinguish bad variant vs missing file
    if variant not in VARIANT_MAP:
        raise HTTPException(400, f"Unknown variant '{variant}'. Allowed: {list(VARIANT_MAP)}")
    p = VARIANT_MAP[variant]
    if not p.exists():
        raise HTTPException(500, f"Variant '{variant}' file missing at {p}. "
                                 "Check that it's committed to Git and deployed.")
    return p.read_text(encoding="utf-8")

@app.get("/debug/variants")
def debug_variants():
    return {k: {"path": str(p), "exists": p.exists()} for k, p in VARIANT_MAP.items()}

def cache_key_for(text: str, variant: str, guidelines_key: str = "") -> str:
    raw = f"{variant}::{guidelines_key}::{text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

@app.post("/demo/run")
async def run_demo(
    request: Request,
    mode: str = Query("auto", enum=["auto", "cached", "live"]),
    variant: str = Query("sanitized", enum=["sensitive", "sanitized"]),
    x_demo_session: str = Header(None),
    authorization: str | None = Header(None),
):
    # ... rate limits / owner checks as you already have ...

    text = load_demo_text(variant)
    key = cache_key_for(text, variant, _guideline_key)  # include your guideline hash if you use one
    run_id = f"demo-{variant}-{key}"

    # try cache
    if mode in ("auto", "cached") and CACHE_PATH.exists():
        data = json.loads(CACHE_PATH.read_text())
        if data.get("key") == key:
            resp = JSONResponse({
                "run_id": run_id,
                "variant": variant,
                "cached": True,
                "steps": ["Loading cached insights", "Rendering…", "Done"],
                "insights": data["insights"],
            })
            resp.headers["x-runs-remaining"] = str(max(0, SESSION_MAX - session_counts.get(x_demo_session, 0)))
            return resp

    # live run
    steps = ["Reading transcript", "Extracting insights", "Validating schema", "Preparing export"]
    await asyncio.sleep(0.2)
    insights = await analyzer.analyze(text, audit=True, validate=True)

    CACHE_PATH.write_text(json.dumps({
        "key": key,
        "variant": variant,
        "insights": insights.model_dump(),
        "cached_at": time.time(),
    }), encoding="utf-8")

    resp = JSONResponse({
        "run_id": run_id,
        "variant": variant,
        "cached": False,
        "steps": steps + ["Done"],
        "insights": insights.model_dump(),
    })
    resp.headers["x-runs-remaining"] = str(max(0, SESSION_MAX - session_counts.get(x_demo_session, 0)))
    return resp
