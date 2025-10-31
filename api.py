# --- imports you need at top (some you already have) ---
import os, json, time, asyncio, inspect, logging, traceback
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Header, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from discovery import InterviewAnalyzer

# Global analyzer instance
analyzer: InterviewAnalyzer | None = None

@app.on_event("startup")
async def _init_analyzer():
    """Initialize the InterviewAnalyzer once when the app boots."""
    global analyzer
    analyzer = InterviewAnalyzer()


app = FastAPI(title="Discovery AI Demo API")

# CORS – adjust to your origins
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

HERE = Path(__file__).parent

# == Fixed server-side inputs ==
VARIANT_MAP = {
    "sanitized": HERE / "data" / "interviews" / "sanitized.txt",
    "sensitive": HERE / "data" / "interviews" / "sensitive.txt",
}

def load_demo_text(variant: str) -> str:
    if variant not in VARIANT_MAP:
        raise HTTPException(400, f"Unknown variant '{variant}'. Allowed: {list(VARIANT_MAP)}")
    p = VARIANT_MAP[variant]
    if not p.exists():
        raise HTTPException(500, f"Variant '{variant}' file missing at {p}. Commit & redeploy.")
    return p.read_text(encoding="utf-8")

# == Writable cache location ==
CACHE_DIR = Path(os.getenv("CACHE_DIR", "/tmp/discovery_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def cache_path_for(variant: str) -> Path:
    return CACHE_DIR / f"{variant}_cache.json"

def cache_key_for(text: str, guidelines_key: str = "", variant: str = "") -> str:
    import hashlib
    raw = f"{variant}::{guidelines_key}::{text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

# tiny health + debug
@app.get("/healthz")
def healthz():
    return {"ok": True, "has_openai_key": bool(os.getenv("OPENAI_API_KEY"))}

@app.get("/debug/variants")
def debug_variants():
    return {k: {"path": str(p), "exists": p.exists()} for k, p in VARIANT_MAP.items()}

@app.get("/debug/openai")
async def debug_openai():
    try:
        client = AsyncOpenAI()  # reads OPENAI_API_KEY from env
        await client.models.list()  # auth-only; no token spend
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"ok": False, "err": str(e)}, status_code=500)

# === your analyzer init above this line ===
# analyzer = InterviewAnalyzer(...)

async def run_analysis(text: str):
    """Run analyzer whether it's async or sync, and surface errors cleanly."""
    try:
        if inspect.iscoroutinefunction(analyzer.analyze):
            return await analyzer.analyze(text, audit=True, validate=True)
        # sync -> run in threadpool so we don't block the event loop
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: analyzer.analyze(text, audit=True, validate=True))
    except Exception as e:
        logging.exception("Analysis failed")
        tb = "".join(traceback.format_exception_only(type(e), e)).strip()
        raise HTTPException(status_code=500, detail=f"analysis_error: {tb}")

@app.post("/demo/run")
async def run_demo(
    request: Request,
    mode: str = Query("auto", enum=["auto", "cached", "live"]),
    variant: str = Query("sanitized", enum=["sanitized", "sensitive"]),
    x_demo_session: str | None = Header(None),
    authorization: str | None = Header(None),
):
    if not x_demo_session:
        raise HTTPException(400, "Missing session header 'x-demo-session'.")

    text = load_demo_text(variant)
    guidelines_key = ""  # fill with your hash if you compute one
    key = cache_key_for(text, guidelines_key, variant)
    run_id = f"demo-{variant}-{key}"
    cache_file = cache_path_for(variant)

    # cached
    if mode in ("auto", "cached") and cache_file.exists():
        try:
            data = json.loads(cache_file.read_text())
            if data.get("key") == key:
                resp = JSONResponse({
                    "run_id": run_id,
                    "variant": variant,
                    "cached": True,
                    "steps": ["Loading cached insights", "Rendering…", "Done"],
                    "insights": data["insights"],
                })
                return resp
        except Exception:
            logging.exception("Failed to read cache; will run live.")

    # live
    steps = ["Reading transcript", "Extracting insights", "Validating schema", "Preparing export"]
    insights = await run_analysis(text)

    # write cache (writable dir)
    try:
        cache_file.write_text(json.dumps({
            "key": key,
            "variant": variant,
            "insights": insights.model_dump() if hasattr(insights, "model_dump") else insights,
            "cached_at": time.time(),
        }), encoding="utf-8")
    except Exception:
        logging.exception("Failed writing cache (non-fatal).")

    return {
        "run_id": run_id,
        "variant": variant,
        "cached": False,
        "steps": steps + ["Done"],
        "insights": insights.model_dump() if hasattr(insights, "model_dump") else insights,
    }
