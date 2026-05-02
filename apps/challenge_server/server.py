"""Static challenge web server.

Serves each dimension as a realistic webpage that LLM agents can
interact with through browser DevTools — mimicking real RE scenarios.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

_PAGES_DIR = Path(__file__).parent / "pages"

app = FastAPI(title="JS-RE-Bench Challenge Server", version="0.1.0")


@app.get("/challenge/{dimension}", response_class=HTMLResponse)
async def serve_challenge(dimension: str) -> str:
    """Serve the challenge page for a given dimension (e.g. D05)."""
    page = _PAGES_DIR / f"{dimension}.html"
    if not page.exists():
        return HTMLResponse(f"<h1>404 — No challenge page for {dimension}</h1>", status_code=404)
    return page.read_text(encoding="utf-8")


@app.get("/")
async def index() -> HTMLResponse:
    """Landing page listing all available challenges."""
    pages = sorted(_PAGES_DIR.glob("D*.html"))
    links = "\n".join(f'<li><a href="/challenge/{p.stem}">{p.stem}</a></li>' for p in pages)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>JS-RE-Bench Challenges</title>
<style>body{{font-family:system-ui;max-width:640px;margin:2em auto;padding:0 1em}}
a{{color:#2563eb}} li{{margin:.3em 0}}</style></head>
<body><h1>JS-RE-Bench Challenge Server</h1>
<p>Click a dimension to load its challenge page:</p>
<ul>{links}</ul></body></html>"""
    return HTMLResponse(html)


# Mount static assets (if any) at /static/
_static = _PAGES_DIR / "static"
if _static.is_dir():
    app.mount("/static", StaticFiles(directory=str(_static)), name="static")


def main() -> None:
    """CLI entry point: ``python -m apps.challenge_server.server``."""
    import uvicorn

    uvicorn.run(
        "apps.challenge_server.server:app",
        host="0.0.0.0",
        port=3000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
