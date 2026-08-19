"""
src/media/asset_resolver.py

Resolves a visual asset for each scene in the VideoPlan.
No text-to-video API is ever invoked.

Resolver strategy per scene visual.kind:
  "diagram"        → DiagramResolver  (default; generates SVG inline; no API)
  "image"          → StillImageResolver (only when USE_POLLINATIONS_STILL=true)
                    or LocalAssetResolver fallback
  "stock_video"    → LocalAssetResolver  (picks from data/library/)
  "screen_capture" → LocalAssetResolver

Resolver outputs:
  data/runs/<run-id>/assets/<scene-id>/asset.<ext>
  data/runs/<run-id>/assets/<scene-id>/asset.json   (manifest)
"""

from __future__ import annotations

import json
import os
import urllib.parse
from abc import ABC, abstractmethod
from pathlib import Path
from typing import NamedTuple

import requests

# pyrefly: ignore [missing-import]
from src.contracts.video_plan import Scene
# pyrefly: ignore [missing-import]
from src.utility.logging_config import setup_logging

logger = setup_logging()


# ── Result type ───────────────────────────────────────────────────────────────


class ResolvedAsset(NamedTuple):
    """Describes a successfully resolved asset."""

    scene_id: str
    local_path: Path          # absolute path on disk
    kind: str                 # mirrors scene.visual.kind
    source: str               # "diagram" | "local" | "stock" | "generated-still"
    original_url: str = ""
    license: str = "unknown"
    attribution: str = ""


# ── Protocol / base ───────────────────────────────────────────────────────────


class BaseResolver(ABC):
    """Base class for all asset resolvers."""

    def __init__(self, run_assets_dir: Path) -> None:
        self.run_assets_dir = run_assets_dir

    @abstractmethod
    def resolve(self, scene: Scene) -> ResolvedAsset | None:
        """Resolve the asset for a scene.

        Returns:
            ResolvedAsset on success, or None if this resolver cannot handle
            the scene.  The pipeline will try the next resolver in the chain.
        """

    def _scene_dir(self, scene: Scene) -> Path:
        d = self.run_assets_dir / scene.id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _write_manifest(self, resolved: ResolvedAsset) -> None:
        manifest = {
            "source": resolved.source,
            "original_url": resolved.original_url,
            "license": resolved.license,
            "attribution": resolved.attribution,
            "local_path": str(resolved.local_path.relative_to(self.run_assets_dir.parent.parent)),
        }
        manifest_path = self._scene_dir_for_id(resolved.scene_id) / "asset.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def _scene_dir_for_id(self, scene_id: str) -> Path:
        d = self.run_assets_dir / scene_id
        d.mkdir(parents=True, exist_ok=True)
        return d


# ── DiagramResolver ───────────────────────────────────────────────────────────


# Simple icon map: keywords → Unicode icon
_ICON_MAP: dict[str, str] = {
    "phone": "📱",
    "mobile": "📱",
    "api": "⚡",
    "server": "🖥️",
    "database": "🗄️",
    "db": "🗄️",
    "network": "🌐",
    "internet": "🌐",
    "cloud": "☁️",
    "request": "➡️",
    "response": "⬅️",
    "flow": "🔄",
    "data": "📊",
    "code": "💻",
    "computer": "💻",
    "laptop": "💻",
    "lock": "🔒",
    "security": "🛡️",
    "cache": "⚡",
    "load": "⚖️",
    "queue": "📋",
    "message": "💬",
    "chat": "💬",
    "user": "👤",
    "client": "👤",
    "auth": "🔑",
    "token": "🎟️",
    "dns": "🔍",
    "http": "🌐",
    "rest": "🔗",
    "json": "📄",
    "websocket": "🔌",
    "microservice": "🧩",
    "docker": "🐳",
    "kubernetes": "☸️",
    "deploy": "🚀",
    "cpu": "⚙️",
    "memory": "💾",
    "storage": "💾",
}


def _pick_icon(query: str) -> str:
    """Pick the first matching icon from the query string."""
    lower = query.lower()
    for keyword, icon in _ICON_MAP.items():
        if keyword in lower:
            return icon
    return "📌"  # default


def _generate_diagram_svg(scene: Scene) -> str:
    """Generate a simple text + icon SVG diagram for a scene.

    Design: dark blue background, centred icon, two lines of text.
    Dimensions: 1080 × 1920 (portrait).
    """
    icon = _pick_icon(scene.visual.query)
    # Title: first 6 words of query, uppercase
    words = scene.visual.query.split()
    title = " ".join(words[:6]).upper()
    subtitle = " ".join(words[6:12]) if len(words) > 6 else scene.on_screen_text

    # Wrap long subtitle into two lines (max 30 chars per line)
    if len(subtitle) > 30:
        mid = len(subtitle) // 2
        # find nearest space to mid
        left = subtitle.rfind(" ", 0, mid)
        right = subtitle.find(" ", mid)
        split_at = left if left != -1 else right
        if split_at != -1:
            line1 = subtitle[:split_at].strip()
            line2 = subtitle[split_at:].strip()
        else:
            line1 = subtitle
            line2 = ""
    else:
        line1 = subtitle
        line2 = ""

    second_text = (
        f'<text x="540" y="1120" class="sub">{line1}</text>\n'
        f'    <text x="540" y="1180" class="sub">{line2}</text>'
        if line2
        else f'<text x="540" y="1120" class="sub">{line1}</text>'
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1920" width="1080" height="1920">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0a0e27"/>
      <stop offset="100%" stop-color="#0d1b4b"/>
    </linearGradient>
    <style>
      .icon {{ font: 280px serif; dominant-baseline: middle; text-anchor: middle; }}
      .title {{ font: bold 68px 'Arial', sans-serif; fill: #e8f0ff;
                text-anchor: middle; letter-spacing: 4px; }}
      .sub   {{ font: 46px 'Arial', sans-serif; fill: #8ab4f8;
                text-anchor: middle; }}
      .tag   {{ font: bold 38px 'Arial', sans-serif; fill: #4285f4;
                text-anchor: middle; letter-spacing: 2px; }}
      .line  {{ stroke: #2a4aaa; stroke-width: 3; opacity: 0.6; }}
    </style>
  </defs>
  <!-- Background -->
  <rect width="1080" height="1920" fill="url(#bg)"/>
  <!-- Decorative lines -->
  <line x1="0" y1="600" x2="1080" y2="600" class="line"/>
  <line x1="0" y1="1400" x2="1080" y2="1400" class="line"/>
  <!-- Icon -->
  <text x="540" y="860" class="icon">{icon}</text>
  <!-- Title -->
  <text x="540" y="1040" class="title">{title}</text>
  <!-- Subtitle -->
  {second_text}
  <!-- Scene tag -->
  <text x="540" y="1340" class="tag">{scene.on_screen_text}</text>
</svg>"""


class DiagramResolver(BaseResolver):
    """Renders a text + icon SVG diagram directly — no external API call."""

    def resolve(self, scene: Scene) -> ResolvedAsset | None:
        if scene.visual.kind != "diagram":
            return None
        scene_dir = self._scene_dir(scene)
        dest = scene_dir / "asset.svg"

        # If the VideoPlan provided a typed diagram payload (template + data),
        # prefer rendering it natively in Remotion and keep a small placeholder
        # manifest so the quality gate can still verify the scene asset directory.
        if getattr(scene.visual, "data", None) is not None or getattr(scene.visual, "template", None) is not None:
            logger.info("[diagram] native diagram payload present; keeping placeholder asset manifest for %s", scene.id)
            if not dest.exists():
                dest.write_text("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1080 1920'/>", encoding="utf-8")
            resolved = ResolvedAsset(
                scene_id=scene.id,
                local_path=dest,
                kind="diagram",
                source="diagram",
                license="generated",
            )
            self._write_manifest(resolved)
            return None

        if not dest.exists():
            svg = _generate_diagram_svg(scene)
            dest.write_text(svg, encoding="utf-8")
            logger.info("[diagram] SVG written → %s", dest)
        else:
            logger.info("[diagram] SVG already exists, skipping: %s", dest)

        resolved = ResolvedAsset(
            scene_id=scene.id,
            local_path=dest,
            kind="diagram",
            source="diagram",
            license="generated",
        )
        self._write_manifest(resolved)
        return resolved


# ── LocalAssetResolver ────────────────────────────────────────────────────────


class LocalAssetResolver(BaseResolver):
    """Picks a matching asset from data/library/ by simple keyword match.

    Library layout:
        data/library/
            stock_video/  *.mp4
            image/        *.png, *.jpg
            screen_capture/ *.mp4
    """

    EXTENSIONS: dict[str, list[str]] = {
        "stock_video": [".mp4", ".mov"],
        "image": [".png", ".jpg", ".jpeg", ".webp"],
        "screen_capture": [".mp4", ".mov"],
    }

    def __init__(self, run_assets_dir: Path, library_dir: Path) -> None:
        super().__init__(run_assets_dir)
        self.library_dir = library_dir

    def resolve(self, scene: Scene) -> ResolvedAsset | None:
        kind = scene.visual.kind
        if kind == "diagram":
            return None  # handled by DiagramResolver

        search_dir = self.library_dir / kind
        if not search_dir.exists():
            logger.warning("[local] Library folder not found: %s", search_dir)
            return None

        extensions = self.EXTENSIONS.get(kind, [])
        candidates = [
            f for f in search_dir.iterdir()
            if f.suffix.lower() in extensions
        ]
        if not candidates:
            logger.warning("[local] No assets in %s", search_dir)
            return None

        # Simple keyword match: pick first file whose name contains any query word.
        query_words = scene.visual.query.lower().split()
        for candidate in candidates:
            name_lower = candidate.stem.lower()
            if any(w in name_lower for w in query_words):
                return self._copy_and_resolve(scene, candidate)

        # Fallback: first file in folder
        logger.info("[local] No keyword match; using first available asset.")
        return self._copy_and_resolve(scene, candidates[0])

    def _copy_and_resolve(self, scene: Scene, src: Path) -> ResolvedAsset:
        import shutil
        scene_dir = self._scene_dir(scene)
        dest = scene_dir / f"asset{src.suffix}"
        if not dest.exists():
            shutil.copy2(src, dest)
            logger.info("[local] Copied %s → %s", src.name, dest)
        resolved = ResolvedAsset(
            scene_id=scene.id,
            local_path=dest,
            kind=scene.visual.kind,
            source="local",
            license="user-managed",
        )
        self._write_manifest(resolved)
        return resolved


# ── StillImageResolver (Pollinations) ─────────────────────────────────────────


class StillImageResolver(BaseResolver):
    """Downloads a still background image from Pollinations.ai.

    ONLY active when the env var USE_POLLINATIONS_STILL=true is set.
    Generates still images only — never video.
    """

    POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"

    def resolve(self, scene: Scene) -> ResolvedAsset | None:
        if not _pollinations_enabled():
            return None
        if scene.visual.kind not in ("image",):
            return None

        scene_dir = self._scene_dir(scene)
        dest = scene_dir / "asset.png"

        if dest.exists():
            logger.info("[pollinations] Image already exists, skipping: %s", dest)
        else:
            image_bytes = self._download(scene.visual.query)
            if image_bytes is None:
                logger.warning("[pollinations] Failed to download image for %s", scene.id)
                return None
            dest.write_bytes(image_bytes)
            logger.info("[pollinations] Image saved → %s", dest)

        resolved = ResolvedAsset(
            scene_id=scene.id,
            local_path=dest,
            kind="image",
            source="generated-still",
            original_url=self._build_url(scene.visual.query),
            license="Pollinations.ai (free tier)",
        )
        self._write_manifest(resolved)
        return resolved

    def _build_url(self, query: str) -> str:
        encoded = urllib.parse.quote(query)
        return f"{self.POLLINATIONS_BASE}/{encoded}?width=1080&height=1920&nologo=true"

    def _download(self, query: str, retries: int = 3) -> bytes | None:
        url = self._build_url(query)
        for attempt in range(1, retries + 1):
            try:
                resp = requests.get(url, timeout=60)
                if resp.status_code == 200:
                    return resp.content
                logger.warning("[pollinations] HTTP %d (attempt %d/%d)", resp.status_code, attempt, retries)
            except requests.RequestException as exc:
                logger.warning("[pollinations] Request failed (attempt %d/%d): %s", attempt, retries, exc)
            import time
            time.sleep(2)
        return None


# ── CodeResolver ─────────────────────────────────────────────────────────────


class CodeResolver(BaseResolver):
    """Generates a placeholder manifest for kind=code so Remotion can render CodeBlock natively."""

    def resolve(self, scene: Scene) -> ResolvedAsset | None:
        if scene.visual.kind != "code":
            return None
        scene_dir = self._scene_dir(scene)
        dest = scene_dir / "asset.txt"
        dest.write_text(scene.visual.code or "", encoding="utf-8")
        resolved = ResolvedAsset(
            scene_id=scene.id,
            local_path=dest,
            kind="code",
            source="code",
            license="generated",
        )
        self._write_manifest(resolved)
        return resolved


# ── Env helper ────────────────────────────────────────────────────────────────


def _pollinations_enabled() -> bool:
    val = os.getenv("USE_POLLINATIONS_STILL", "false").strip().lower()
    return val in {"1", "true", "yes", "on"}


# ── Orchestrator ──────────────────────────────────────────────────────────────


class AssetOrchestrator:
    """Runs all resolvers in priority order for every scene.

    Priority:
      1. DiagramResolver  (for kind=diagram, always first)
      2. CodeResolver     (for kind=code)
      3. StillImageResolver (for kind=image, only if USE_POLLINATIONS_STILL=true)
      4. LocalAssetResolver (fallback)

    If scene.visual.required is True and no resolver succeeds, raises RuntimeError.
    """

    def __init__(self, run_dir: Path) -> None:
        self.run_assets_dir = run_dir / "assets"
        library_dir = Path(__file__).resolve().parents[3] / "data" / "library"

        self.resolvers: list[BaseResolver] = [
            DiagramResolver(self.run_assets_dir),
            CodeResolver(self.run_assets_dir),
            StillImageResolver(self.run_assets_dir),
            LocalAssetResolver(self.run_assets_dir, library_dir),
        ]

    def resolve_all(self, scenes: list[Scene]) -> dict[str, ResolvedAsset]:
        """Resolve assets for all scenes.

        Returns:
            Mapping of scene.id → ResolvedAsset.

        Raises:
            RuntimeError: If a required asset cannot be resolved.
        """
        results: dict[str, ResolvedAsset] = {}

        for scene in scenes:
            logger.info("[assets] Resolving %s (kind=%s) …", scene.id, scene.visual.kind)
            resolved = self._resolve_one(scene)
            if resolved is None:
                # If this is a typed/native diagram payload, no external asset
                # is required — Remotion will render it from the `diagram`
                # prop. Treat as satisfied.
                if scene.visual.kind == "diagram" and (
                    getattr(scene.visual, "data", None) or getattr(scene.visual, "template", None)
                ):
                    logger.info("[assets] Native diagram present; no asset required for %s", scene.id)
                    continue

                if scene.visual.required:
                    raise RuntimeError(
                        f"Required asset could not be resolved for {scene.id}: "
                        f"kind={scene.visual.kind}, query={scene.visual.query!r}"
                    )
                logger.warning("[assets] No asset for %s (not required, continuing)", scene.id)
            else:
                results[scene.id] = resolved
                logger.info("[assets] ✓ %s → %s", scene.id, resolved.local_path.name)

        return results

    def _resolve_one(self, scene: Scene) -> ResolvedAsset | None:
        for resolver in self.resolvers:
            result = resolver.resolve(scene)
            if result is not None:
                return result
        return None
