# Complete Remotion Migration Guide

## Purpose

Replace every text-to-video provider in `yt-agent` (Seedance, Veo, and Grok)
with a deterministic Remotion renderer. NVIDIA Nemotron remains the creative
planner: it produces a validated video plan, narration, and asset instructions.
Remotion then assembles licensed/static visual assets, narration, captions,
music, and overlays into a 30-second vertical MP4.

This is an execution plan for a coding agent. Follow phases in order and do not
start the destructive cleanup phase until the acceptance checks in Phase 6 pass.

## Current repository facts

- `main.py` currently imports and runs `SeedanceVideoGenerator`.
- `src/model/service/video_generator.py`, `veo_video_generator.py`, and
  `grok_video_generator.py` are text-to-video paths to remove.
- `src/model/service/asset_generator.py` already generates per-scene TTS and
  Remotion-like props, but it needs a stable run directory and a stronger
  schema.
- Git currently shows the old `video-renderer/` directory as deleted. Do not
  restore it with `git checkout`; create the new Remotion project described
  below. Preserve unrelated uncommitted work.
- `prompts/script_video_prompt.md` currently requests Veo prompts and therefore
  must be migrated with the Python code.

## Target architecture

```text
topic
  -> Prompt agent (NVIDIA Nemotron through OpenRouter)
  -> VideoPlan JSON validation
  -> Asset resolver + TTS
  -> Remotion props JSON
  -> Remotion renderer
  -> local data/runs/<run-id>/final.mp4
  -> explicit approval gate
  -> YouTube upload
```

### Hard boundaries

| Component | May do | Must not do |
| --- | --- | --- |
| NVIDIA prompt agent | Write script, metadata, scene timing, visual instructions | Generate video or provider-specific Veo/Grok/Seedance prompts |
| Asset resolver | Select/download licensed stock assets, create diagrams, optionally fetch still images | Invoke any text-to-video API |
| TTS | Produce one narration MP3 and caption timings | Guess a 30-second duration |
| Remotion | Compose assets/audio/captions and render MP4 | Call APIs, read the database, or decide content |
| YouTube uploader | Upload an approved MP4 and save its video ID | Publish without explicit `--publish` / approval |

## Target directory layout

```text
yt-agent/
  main.py
  prompts/
    script_video_prompt.md
  src/
    contracts/
      video_plan.py
    pipeline/
      run_pipeline.py
      quality_checks.py
    model/service/
      prompt_agent.py
    media/
      asset_resolver.py
      tts_generator.py
      captions.py
    remotion/
      renderer.py
    youtube/
      video_uploader.py
  video-renderer/
    package.json
    tsconfig.json
    remotion.config.ts
    src/
      index.ts
      Root.tsx
      compositions/ShortVideo.tsx
      components/Scene.tsx
      components/Captions.tsx
      schemas.ts
  data/
    runs/<run-id>/
      plan.json
      props.json
      assets/
      audio/narration.mp3
      captions.json
      final.mp4
```

`data/` remains ignored by Git. All runtime paths must be derived from a
`run_id`; do not use the shared mutable paths `data/video.mp4` or
`data/metadata/scene/`.

---

## Phase 1 — Define the source-of-truth contract

Create `src/contracts/video_plan.py` with Pydantic v2 models. Add
`pydantic>=2` to `pyproject.toml`.

Required model shape:

```python
class VisualAsset(BaseModel):
    kind: Literal["stock_video", "image", "diagram", "screen_capture"]
    query: str
    required: bool = True

class Scene(BaseModel):
    id: str                      # "scene-01", stable within a run
    start_ms: int
    end_ms: int
    narration: str
    on_screen_text: str
    visual: VisualAsset
    transition: Literal["cut", "fade", "slide"] = "cut"

class YouTubeMetadata(BaseModel):
    title: str
    description: str
    tags: list[str]
    category_id: str = "22"

class VideoPlan(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    topic: str
    aspect_ratio: Literal["9:16"] = "9:16"
    width: int = 1080
    height: int = 1920
    fps: int = 30
    target_duration_ms: int = 30000
    voice: str = "en-US-ChristopherNeural"
    youtube: YouTubeMetadata
    scenes: list[Scene]
```

Add `validate_video_plan(plan)` with these enforced checks:

1. Exactly 4–5 scenes.
2. First scene starts at `0`; each following scene starts at the preceding
   scene's `end_ms`; no gaps or overlaps.
3. Last scene ends at exactly `30000` ms.
4. Every scene is 4–10 seconds.
5. `on_screen_text` is 2–5 words.
6. No legacy fields are accepted: `veo_prompt`, `extension_prompt`,
   `video_prompt`, `reference_image_urls`, `shots`, `production`.

Write unit tests for valid input, gap, overlap, non-30-second total, and a
legacy field. The pipeline must stop before TTS or rendering if validation
fails.

## Phase 2 — Replace the LLM prompt and parser

Rewrite `prompts/script_video_prompt.md`. It must request only the `VideoPlan`
JSON contract from Phase 1. Remove all mentions of Veo, Seedance, Grok,
extensions, `taskId`, camera continuation, and `background_prompt` intended
for image/video generation.

The visual instruction for each scene should be provider-neutral:

```json
{
  "id": "scene-02",
  "start_ms": 7000,
  "end_ms": 14000,
  "narration": "Your phone sends a request to the API, like placing an order at a restaurant.",
  "on_screen_text": "REQUEST SENT",
  "visual": {
    "kind": "diagram",
    "query": "Animated phone-to-API-to-server request flow, dark blue technical style"
  },
  "transition": "slide"
}
```

Update `VideoScriptGeneratorAgent`:

1. Return `VideoPlan.model_validate_json(content)`, not an untyped `dict`.
2. Delete the inverted/confusing `DEVMODE` cache branching. Replace it with an
   explicit `--use-cached-plan <path>` CLI option in Phase 5.
3. Save the validated result as `data/runs/<run-id>/plan.json`.
4. Keep OpenRouter/NVIDIA configuration, but do not include `KIE_API_KEY` in
   this flow.

## Phase 3 — Build the media preparation layer

Do not use a text-to-video model. Implement one `AssetResolver` interface in
`src/media/asset_resolver.py`:

```python
class AssetResolver(Protocol):
    def resolve(self, scene: Scene, output_dir: Path) -> ResolvedAsset: ...
```

Implement adapters in this order:

1. `DiagramResolver`: renders topic diagrams using SVG/HTML assets. This is the
   default for technical explanations and needs no external visual AI service.
2. `LocalAssetResolver`: chooses assets from a user-managed library by query.
3. `StockAssetResolver` (optional): downloads only assets with stored source,
   license, and attribution metadata.
4. `StillImageResolver` (optional): may reuse the existing Pollinations image
   approach for a *still background only*. It must never generate video and
   must be behind an explicit configuration flag.

Store the result of each resolver under
`data/runs/<run-id>/assets/<scene-id>/` with an `asset.json` manifest:

```json
{
  "source": "local|stock|generated-still",
  "original_url": "...",
  "license": "...",
  "local_path": "assets/scene-02/request-flow.svg"
}
```

### TTS and captions

Replace per-scene independent MP3 files with one file:

```text
all scene narration concatenated in plan order
  -> data/runs/<run-id>/audio/narration.mp3
  -> data/runs/<run-id>/captions.json
```

`edge-tts` can remain the initial provider. Capture word boundaries if the
provider exposes them; otherwise transcribe the generated MP3 and create
timestamped captions. Do not create captions from word-count estimates.

Persist Remotion-compatible caption records:

```json
{ "text": "request", "startMs": 7020, "endMs": 7420,
  "timestampMs": 7020, "confidence": 1.0 }
```

Adjust scene start/end times only when required to fit real audio. If the
final narration cannot fit 30 seconds, fail the run and regenerate the plan;
never silently speed audio past an agreed limit.

## Phase 4 — Create the new Remotion project

Create a fresh project at `video-renderer/`:

```bash
npx create-video@latest --yes --blank --no-tailwind video-renderer
cd video-renderer
npx remotion add @remotion/media zod @remotion/captions
```

Use `npx remotion add` for every `@remotion/*` dependency so versions remain
compatible. Do not copy back the deleted legacy renderer or its generated
assets.

Implement a single composition:

```tsx
<Composition
  id="ShortVideo"
  component={ShortVideo}
  width={1080}
  height={1920}
  fps={30}
  durationInFrames={900}
  schema={shortVideoSchema}
/>
```

`ShortVideo` must receive all data through props:

```ts
type ShortVideoProps = {
  audioSrc: string;
  scenes: Array<{
    id: string;
    fromFrame: number;
    durationInFrames: number;
    assetSrc: string;
    assetKind: "stock_video" | "image" | "diagram" | "screen_capture";
    onScreenText: string;
    transition: "cut" | "fade" | "slide";
  }>;
  captions: Caption[];
};
```

Rendering rules:

- Use `<Audio>` and `<Video>` from `@remotion/media`.
- Use `staticFile()` only for files copied into `video-renderer/public/runs/`.
- Use `<Sequence>` per scene; do not calculate timing from component-local
  state.
- Animate only with `useCurrentFrame()`, `interpolate()`, and spring/easing;
  CSS animation or transition is prohibited because it will not render
  deterministically.
- Add a safe-area-aware caption layer, scene label, and high-contrast
  background overlay.
- Use a Zod schema for composition props. `calculateMetadata()` must validate
  the 30-second duration before rendering.

The Python render adapter will copy/link only the current run's assets to
`video-renderer/public/runs/<run-id>/`; it must clean this target after a
successful render or after a failed render retry.

## Phase 5 — Replace `main.py` with an explicit pipeline CLI

Create `src/pipeline/run_pipeline.py`, then make `main.py` a thin CLI wrapper.
Required command shape:

```bash
uv run python main.py create --topic "How an API request works"
uv run python main.py create --topic "..." --use-cached-plan data/runs/<id>/plan.json
uv run python main.py upload --run-id <id> --privacy private
uv run python main.py upload --run-id <id> --privacy public --publish
```

`create` executes, in this exact order:

1. create `run_id` and run directory;
2. generate or load and validate `VideoPlan`;
3. resolve every visual asset;
4. generate narration and captions;
5. create `props.json` from plan + resolved assets + caption timestamps;
6. invoke Remotion renderer;
7. run quality checks;
8. write `run.json` with paths, status, versions, and errors.

The `create` command must **not** upload. Upload is a separate command so a
render cannot become public because of a coding or asset failure.

Render from Python using `subprocess.run([...], check=True)`, with arguments
as a list. Do not use shell interpolation. The renderer contract is:

```bash
cd video-renderer
npx remotion render ShortVideo ../data/runs/<run-id>/final.mp4 \
  --props=../data/runs/<run-id>/props.json
```

## Phase 6 — Quality gate and tests

Implement `src/pipeline/quality_checks.py` using `ffprobe`/FFmpeg metadata.
A run is uploadable only if all checks pass:

| Check | Required value |
| --- | --- |
| File exists and is nonempty | yes |
| Container | MP4 |
| Video dimensions | 1080 × 1920 |
| Frame rate | 30 fps |
| Duration | 29.5–30.5 seconds |
| Audio stream | present |
| Captions | nonempty and within duration |
| Every required asset | resolved |
| No legacy generator dependency | true |

Add tests for contract validation, props construction, renderer command
construction, and quality-check parsing. Add one smoke test that renders a
small fixture plan with local SVG/image assets and no external API key.

Manual verification before cleanup:

```bash
cd video-renderer && npm run start
# preview the ShortVideo composition with fixture props

uv run python main.py create --topic "How an API request works"
ffprobe data/runs/<run-id>/final.mp4
```

## Phase 7 — Complete removal of video-generation code

Only after Phase 6 passes, remove these tracked implementation paths and their
imports/references:

```text
src/model/client/seedance_client.py
src/model/client/veo_client.py
src/model/client/grok_client.py
src/model/service/video_generator.py
src/model/service/veo_video_generator.py
src/model/service/grok_video_generator.py
```

Also remove `KIE_API_KEY` from `.env.example`, `load_all_env()`, README,
documentation, and dependency notes. Keep the user's actual `.env` untouched.
Update `README.md` to reflect the new command flow and explicitly state:

> This project does not use text-to-video generation. Remotion composes
> licensed/static visual assets, programmatic diagrams, narration, captions,
> and overlays.

Retain the old docs only when clearly marked **historical**. Otherwise delete
or replace their obsolete Veo/Seedance instructions.

## Phase 8 — YouTube uploader hardening

Fix the configuration mismatch before enabling uploads: README and
`load_envs.py` say OAuth comes from environment variables, but
`video_uploader.py` currently requires `credentials.json`.

Choose environment-based OAuth and pass the existing config dictionary to
`InstalledAppFlow.from_client_config()`. Store refreshed credentials securely
outside Git. Add upload scopes only as needed, default every upload to
`private`, and require `--publish` to select `public`.

Extend `upload_video()` to accept only a successful `run_id`, read metadata
from that run's `plan.json`, and write `youtube.json` containing the returned
video ID and uploaded timestamp.

Performance monitoring is a separate future command (`metrics --run-id ...`)
using the YouTube Analytics API. Do not mix it into the rendering migration.

## Definition of done

The migration is complete only when all of the following are true:

- A topic produces a validated 30-second `VideoPlan`.
- The project renders a 1080×1920 MP4 using Remotion without Seedance, Veo,
  Grok, or any other text-to-video API.
- Narration, captions, and visual assets are tied to one immutable run folder.
- Invalid plans and failed quality checks prevent upload.
- Upload is a separate, private-by-default command.
- The legacy generator clients/services and `KIE_API_KEY` are removed.
- README and docs match the code that actually runs.
