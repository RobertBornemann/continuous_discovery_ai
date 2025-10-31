# api.py (top)
import os, json, time, asyncio, inspect, logging, traceback
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Header, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

from discovery import InterviewAnalyzer  # your class

# 1) Create the app first
app = FastAPI(title="Discovery AI Demo API")

# 2) CORS (adjust origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://<your-vercel-app>.vercel.app",
        "https://<your-prod-domain>",
    ],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

# 3) Globals & paths
HERE = Path(__file__).parent
VARIANT_MAP = {
    "sanitized": HERE / "data" / "interviews" / "sanitized.txt",
    "sensitive": HERE / "data" / "interviews" / "sensitive.txt",
}
CACHE_DIR = Path(os.getenv("CACHE_DIR", "/tmp/discovery_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def cache_path_for(variant: str) -> Path:
    return CACHE_DIR / f"{variant}_cache.json"

def cache_key_for(text: str, guidelines_key: str = "", variant: str = "") -> str:
    import hashlib
    raw = f"{variant}::{guidelines_key}::{text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

def load_demo_text(variant: str) -> str:
    if variant not in VARIANT_MAP:
        raise HTTPException(400, f"Unknown variant '{variant}'. Allowed: {list(VARIANT_MAP)}")
    p = VARIANT_MAP[variant]
    if not p.exists():
        raise HTTPException(500, f"Variant '{variant}' file missing at {p}. Commit & redeploy.")
    return p.read_text(encoding="utf-8")

# 4) Initialize analyzer AFTER app exists
analyzer: Optional[InterviewAnalyzer] = None

@app.on_event("startup")
async def _init_analyzer():
    global analyzer
    # If you need to load guidelines, do it here and pass them in
    analyzer = InterviewAnalyzer()

# --- health/debug endpoints (optional) ---
@app.get("/healthz")
def healthz():
    return {"ok": True, "has_openai_key": bool(os.getenv("OPENAI_API_KEY"))}

@app.get("/debug/variants")
def debug_variants():
    return {k: {"path": str(p), "exists": p.exists()} for k, p in VARIANT_MAP.items()}

@app.get("/debug/openai")
async def debug_openai():
    try:
        client = AsyncOpenAI()  # picks up OPENAI_API_KEY
        await client.models.list()
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

# 5) Helper to run analysis (works for sync or async analyze())
async def run_analysis(text: str):
    if analyzer is None:
        raise HTTPException(500, detail="analysis_error: analyzer not initialized")
    try:
        if inspect.iscoroutinefunction(analyzer.analyze):
            return await analyzer.analyze(text, audit=True, validate=True)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: analyzer.analyze(text, audit=True, validate=True))
    except Exception as e:
        logging.exception("Analysis failed")
        tb = "".join(traceback.format_exception_only(type(e), e)).strip()
        raise HTTPException(500, detail=f"analysis_error: {tb}")

# 6) The demo endpoint (unchanged from earlier logic)
@app.post("/demo/run")
async def run_demo(
    request: Request,
    mode: str = Query("auto", enum=["auto", "cached", "live"]),
    variant: str = Query("sanitized", enum=["sanitized", "sensitive"]),
    x_demo_session: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
):
    if not x_demo_session:
        raise HTTPException(400, "Missing session header 'x-demo-session'.")

    text = load_demo_text(variant)
    key = cache_key_for(text, "", variant)
    run_id = f"demo-{variant}-{key}"
    cache_file = cache_path_for(variant)

    # try cache
    if mode in ("auto", "cached") and cache_file.exists():
        try:
            data = json.loads(cache_file.read_text())
            if data.get("key") == key:
                return {
                    "run_id": run_id,
                    "variant": variant,
                    "cached": True,
                    "steps": ["Loading cached insights", "Rendering…", "Done"],
                    "insights": data["insights"],
                }
        except Exception:
            logging.exception("Cache read failed; running live.")

    # live
    steps = ["Reading transcript", "Extracting insights", "Validating schema", "Preparing export"]
    insights = await run_analysis(text)

    # cache (best effort)
    try:
        cache_file.write_text(json.dumps({
            "key": key,
            "variant": variant,
            "insights": insights.model_dump() if hasattr(insights, "model_dump") else insights,
            "cached_at": time.time(),
        }), encoding="utf-8")
    except Exception:
        logging.exception("Cache write failed (non-fatal).")

    return {
        "run_id": run_id,
        "variant": variant,
        "cached": False,
        "steps": steps + ["Done"],
        "insights": insights.model_dump() if hasattr(insights, "model_dump") else insights,
    }
