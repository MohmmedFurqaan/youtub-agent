"""
src/model/service/prompt_agent.py

Calls NVIDIA Nemotron (via OpenRouter) and returns a validated VideoPlan.

Changes from previous version:
  - Returns typed VideoPlan, not an untyped dict.
  - Inverted / confusing DEVMODE cache logic removed.
  - Supports --use-cached-plan <path> via load_plan_from_file().
  - Saves validated plan to data/runs/<run-id>/plan.json (caller supplies run_dir).
  - No reference to KIE_API_KEY or any text-to-video service.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage

from src.contracts.video_plan import VideoPlan, validate_video_plan
from src.utility.load_envs import load_all_env
from src.utility.logging_config import setup_logging


class VideoScriptGeneratorAgent:
    """Generates and validates a VideoPlan from a user topic via NVIDIA Nemotron."""

    def __init__(
        self,
        topic: str,
        open_router_model_name: str | None = None,
    ) -> None:
        """
        Args:
            topic:                   The video topic / user request.
            open_router_model_name:  OpenRouter model identifier.
        """
        self.topic = topic
        self.model_name = open_router_model_name
        self.logger = setup_logging()

        prompts_dir = Path(__file__).resolve().parents[3] / "prompts"
        self.system_prompt = self._load_prompt(prompts_dir / "script_video_prompt.md")

    # ── Public API ────────────────────────────────────────────────────────────

    def generate(self, run_dir: Path) -> VideoPlan:
        """Call the LLM, validate the result, save plan.json, and return it.

        Args:
            run_dir: The run's data directory (data/runs/<run-id>/).

        Returns:
            Validated VideoPlan instance.

        Raises:
            ValueError:  If the LLM response cannot be parsed or fails validation.
            RuntimeError: If the model name is not configured.
        """
        if not self.model_name:
            raise RuntimeError(
                "open_router_model_name is required. Set OPENROUTER_MODEL_NAME in .env."
            )

        self.logger.info("[prompt_agent] Calling %s for topic: %s", self.model_name, self.topic)

        raw = self._invoke_llm()
        plan = self._parse_and_validate(raw)

        plan_path = run_dir / "plan.json"
        plan_path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        self.logger.info("[prompt_agent] plan.json saved → %s", plan_path)

        return plan

    @staticmethod
    def load_plan_from_file(path: Path | str) -> VideoPlan:
        """Load and validate an existing plan.json (--use-cached-plan support).

        Args:
            path: Path to a previously saved plan.json.

        Returns:
            Validated VideoPlan.
        """
        text = Path(path).read_text(encoding="utf-8")
        plan = VideoPlan.model_validate_json(text)
        validate_video_plan(plan)
        return plan

    # ── Private helpers ───────────────────────────────────────────────────────

    def _invoke_llm(self) -> str:
        """Call the OpenRouter model and return the raw content string."""
        model = init_chat_model(
            model=self.model_name,
            model_provider="openrouter",
        )
        messages = [
            SystemMessage(self.system_prompt),
            HumanMessage(self.topic),
        ]
        response = model.invoke(messages)
        return str(response.content).strip()

    def _parse_and_validate(self, raw: str) -> VideoPlan:
        """Strip optional markdown fences, parse JSON, validate against contract.

        Args:
            raw: Raw LLM response string.

        Returns:
            Validated VideoPlan.

        Raises:
            ValueError: On JSON parse failure or contract validation failure.
        """
        # Strip ```json ... ``` or ``` ... ``` fences if present.
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()

        try:
            payload = json.loads(cleaned)
            payload = self._repair_invalid_visual_schema(payload)
            plan = VideoPlan.model_validate(payload)
        except Exception as exc:
            self.logger.error(
                "[prompt_agent] JSON parse / validation failed:\n%s\n\nRaw content:\n%s",
                exc,
                raw[:800],
            )
            raise ValueError(f"LLM output did not match VideoPlan schema: {exc}") from exc

        try:
            validate_video_plan(plan)
        except ValueError as exc:
            self.logger.error("[prompt_agent] Structural validation failed: %s", exc)
            raise

        self.logger.info(
            "[prompt_agent] VideoPlan validated — %d scenes, topic: %s",
            len(plan.scenes),
            plan.topic,
        )
        return plan

    @staticmethod
    def _repair_invalid_visual_schema(plan: dict) -> dict:
        """Normalize mistaken diagram template names that the model emitted as kind values."""
        valid_kinds = {"diagram", "image", "stock_video", "screen_capture"}
        diagram_templates = {
            "request-flow",
            "architecture-layers",
            "sequence",
            "comparison",
            "timeline",
            "concept-card",
            "metric-chart",
        }

        for scene in plan.get("scenes", []):
            visual = scene.get("visual")
            if not isinstance(visual, dict):
                continue

            kind = visual.get("kind")
            template = visual.get("template")
            if kind in valid_kinds:
                continue

            if kind in diagram_templates:
                visual["kind"] = "diagram"
                visual.setdefault("template", kind)
                continue

            if isinstance(template, str) and template in diagram_templates:
                visual["kind"] = "diagram"
                continue

        return plan

    @staticmethod
    def _load_prompt(path: Path) -> str:
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")
        return path.read_text(encoding="utf-8")