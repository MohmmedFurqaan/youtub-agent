# Remotion Integration Test Plan

This document outlines the testing strategy for the integration of Remotion into the `yt-agent` video generation pipeline. The integration is divided into 5 phases. As each phase is completed, its detailed test cases and status will be documented here.

## Phase 1: AI Prompt and JSON Output (COMPLETED)

**Objective**: Ensure the LLM generates a strictly formatted JSON video script and the `VideoAgent` parses it correctly into a Python dictionary.

### Test Cases

| Test ID | Component | Description | Steps | Expected Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **P1.1** | Prompt File | Verify strict JSON instructions in prompt file. | 1. Open `prompts/script_video_prompt.md`.<br>2. Check for the JSON schema and rules preventing markdown. | File contains exact JSON schema for `title`, `characters`, and `scenes`. | ✅ Passed |
| **P1.2** | JSON Parsing | Verify successful parsing of raw JSON. | 1. Mock the LLM response to return a raw valid JSON string.<br>2. Call `video_script_generator()`. | Returns a Python `dict` with the parsed JSON data. | ⬜ Pending |
| **P1.3** | Markdown Stripping | Verify stripping of ` ```json ` blocks. | 1. Mock the LLM response to return JSON wrapped in ` ```json ... ``` `.<br>2. Call `video_script_generator()`. | Returns a Python `dict`. Strips backticks successfully. | ⬜ Pending |
| **P1.4** | Markdown Stripping | Verify stripping of generic ` ``` ` blocks. | 1. Mock the LLM response to return JSON wrapped in ` ``` ... ``` `.<br>2. Call `video_script_generator()`. | Returns a Python `dict`. Strips backticks successfully. | ⬜ Pending |
| **P1.5** | Invalid JSON Handling | Verify graceful failure on invalid JSON. | 1. Mock the LLM response to return invalid JSON.<br>2. Call `video_script_generator()`. | Returns dict: `{"error": "Failed to parse JSON", "raw_content": ...}`. | ⬜ Pending |
| **P1.6** | Title Generation Types | Verify `ai_title_prompt` accepts dict inputs. | 1. Pass a valid `dict` to `ai_title_prompt()`. | `json.dumps()` is called and title is generated successfully. | ⬜ Pending |
| **P1.7** | E2E Generation | Verify live LLM call returns expected schema. | 1. Run `main.py`.<br>2. Observe terminal output. | Prints valid Python dict with `title`, `characters`, and `scenes`. | ✅ Passed |

---

## Phase 2: Python Asset Generation (TTS & Images) (PENDING)

*Test cases will be defined once this phase is shipped.*

---

## Phase 3: Setup the Remotion Project (PENDING)

*Test cases will be defined once this phase is shipped.*

---

## Phase 4: Orchestrate the Render from Python (PENDING)

*Test cases will be defined once this phase is shipped.*

---

## Phase 5: Bring it all together in `main.py` (PENDING)

*Test cases will be defined once this phase is shipped.*
