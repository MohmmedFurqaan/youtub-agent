"""
src/web/server.py — FastAPI Web Application server entry point.
"""

from __future__ import annotations

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.web.api_router import router as api_router
from src.utility.logging_config import setup_logging

logger = setup_logging()

app = FastAPI(
    title="YouTube Agent Web Application",
    description="Full-stack AI Video Generation Studio & YouTube Publishing Suite",
    version="0.1.0",
)

# Configure CORS for local development (Vite frontend on port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)

# Mount frontend static distribution if built
frontend_dist = Path(__file__).parent.parent.parent / "web" / "dist"
if frontend_dist.exists() and frontend_dist.is_dir():
    logger.info("Mounting built frontend static distribution from %s", frontend_dist)
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        if full_path.startswith("api"):
            return None
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")


def start_web_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Launch Uvicorn ASGI server."""
    import uvicorn
    logger.info("Starting YouTube Agent Web App on http://%s:%d", host, port)
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_web_server()
