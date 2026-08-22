# Video Quality Improvement Plan

## Purpose

This document defines the phased plan for improving the generated educational videos in `youtub-agent`.

The target is not only technically valid MP4 output, but a coherent educational video in which narration, visuals, captions, diagrams, code, animation, and sound effects are synchronized to one timeline.

## Current Problems

The current pipeline already has useful building blocks: Remotion scenes, diagrams, cartoon characters, captions, TTS, animation events, and technical render checks. The main problem is that these systems are not driven by one authoritative semantic timeline.

Key gaps identified on `main`:

1. **Audio/video/caption synchronization is not authoritative.** TTS duration, scene duration, caption timestamps, and visual animation timing can originate from different timing assumptions.
2. **Code is not a first-class visual asset.** The planner/schema supports stock video, images, diagrams, and screen captures, but not a dedicated code block with language, highlighted lines, or reveal behavior.
3. **Diagrams are implemented but not strongly required by content semantics.** A technical explanation can still be planned with a generic image or stock asset instead of a diagram.
4. **Cartoon characters are mostly decorative.** They are rendered in scenes, but their actions are not sufficiently coupled to narration or semantic events.
5. **Captions and visual events have separate timelines.** Caption timestamps can be correct for speech while diagram/code/cartoon events occur at unrelated points.
6. **Quality checks are mostly technical.** Current checks verify dimensions, FPS, duration, audio presence, captions, and asset resolution, but do not verify semantic visual quality or synchronization.
7. **The renderer has conflicting caption ownership assumptions.** Captions are treated as a global overlay while scene-level code comments indicate captions were removed from that phase. Ownership should be explicit and singular.

## Target Architecture

Use a **Master Video Timeline** as the source of truth.

```text
                    CONTENT / SCRIPT
                          |
                          v
                 MASTER VIDEO PLAN
                          |
          +---------------+----------------+
          |               |                |
          v               v                v
        AUDIO           VISUALS         CAPTIONS
          |               |                |
          +---------------+----------------+
                          |
                          v
                 MASTER TIMELINE
                          |
                          v
                      REMOTION
                          |
                          v
                   FINAL MP4 + QA
```

Every important event should be expressed relative to the same timeline:

- narration/word timing
- caption timing
- diagram animation
- code highlighting/reveal
- cartoon action
- visual transitions
- sound effects

## Phase 0 — Baseline and Contracts

**Goal:** establish the contracts before changing rendering behavior.

### Tasks

- [ ] Document the current scene, audio, caption, diagram, and event flow.
- [ ] Define a canonical time unit: milliseconds in the planning layer, converted to Remotion frames only at render time.
- [ ] Define one source of truth for scene start/end times.
- [ ] Define the ownership of captions as a global timeline-driven layer.
- [ ] Add explicit video-quality acceptance criteria to the project documentation.
- [ ] Add regression fixtures containing a short technical explanation with speech, diagram, code, and captions.

### Exit Criteria

A test plan exists that can detect timing drift and missing visual requirements before upload.

---

## Phase 1 — Fix Audio, Caption, and Visual Synchronization

**Priority: P0**

**Goal:** make the actual narration timing authoritative.

### Tasks

- [ ] Generate TTS per scene rather than relying only on planned scene duration.
- [ ] Measure the actual generated audio duration.
- [ ] Preserve word-boundary timestamps from the TTS provider.
- [ ] Build a canonical scene timeline from measured narration durations plus intentional pauses.
- [ ] Generate captions directly from the same word timestamps used by the audio.
- [ ] Attach visual events to narration-relative timestamps.
- [ ] Convert milliseconds to Remotion frames in exactly one place.
- [ ] Validate that scene boundaries, audio, captions, and event timelines cannot silently drift.
- [ ] Define explicit behavior for pauses, silence, and scene padding.
- [ ] Add synchronization tests with tolerance thresholds.

### Required Timeline Model

```text
Scene
  |
  +-- audioStartMs / audioEndMs
  +-- words[]
  |     +-- startMs / endMs
  |
  +-- visualEvents[]
  |     +-- atMs / durationMs
  |
  +-- captionEvents[]
  |     +-- startMs / endMs
  |
  +-- soundEvents[]
```

### Exit Criteria

For a fixed regression script:

- captions follow spoken words within the defined tolerance;
- diagrams/code/cartoon events occur at the intended spoken point;
- scene transitions do not cut speech prematurely;
- no independent timing system can move captions or visual events away from the master timeline.

---

## Phase 2 — Add First-Class Code Blocks

**Priority: P1**

**Goal:** make code a native educational visual instead of forcing it through screenshots or generic text.

### Tasks

- [ ] Add `code` to the visual asset kinds in the Python video-plan contract.
- [ ] Add `code` to the Remotion/Zod scene schema.
- [ ] Define code fields: language, source, highlighted lines, title, and optional focus range.
- [ ] Implement `CodeBlock.tsx` in the renderer.
- [ ] Add syntax highlighting for supported languages.
- [ ] Add line-number rendering.
- [ ] Add line/region highlight animation.
- [ ] Add optional type/reveal animation where appropriate.
- [ ] Keep code inside mobile-safe areas and preserve readability at 1080x1920.
- [ ] Make the planner select code when narration explains implementation or source code.
- [ ] Add tests for long code, wrapped lines, and unsupported languages.

### Exit Criteria

A technical explanation can show readable, animated code without requiring a screen capture.

---

## Phase 3 — Make Diagram Selection Semantic

**Priority: P1**

**Goal:** ensure technical relationships are visually explained with diagrams.

### Tasks

- [ ] Define planner rules for when a diagram is required.
- [ ] Prefer diagrams for architecture, request/response flow, sequences, comparisons, pipelines, dependencies, and timelines.
- [ ] Map narration concepts to diagram templates.
- [ ] Validate diagram data before rendering.
- [ ] Improve diagram layout for vertical video.
- [ ] Synchronize diagram animation events with narration timestamps.
- [ ] Highlight the exact node/edge/step being discussed.
- [ ] Add a fallback when diagram generation fails, without silently replacing it with an irrelevant stock image.

### Exit Criteria

When the narration explains a process or relationship, the corresponding visual makes that relationship explicit and synchronized.

---

## Phase 4 — Make Cartoon Animation Content-Driven

**Priority: P2**

**Goal:** turn cartoon characters from decoration into explanatory actors.

### Tasks

- [ ] Define semantic cartoon actions: talk, point, think, surprised, send, receive, walk, celebrate, error, and idle.
- [ ] Add an action timeline to scene events.
- [ ] Allow the planner to request an action based on the narration.
- [ ] Synchronize character actions with diagram/code events.
- [ ] Avoid covering captions, code, or important diagram content.
- [ ] Use different character poses/actions instead of only an idle bounce.
- [ ] Add deterministic seeds so renders remain reproducible.

### Example

```text
Narration: "The client sends a request to the server."

0ms       Client character points
300ms     Request packet starts moving
900ms     Server reacts
1200ms    Response animation starts
```

### Exit Criteria

Cartoon animation communicates the concept and is synchronized with the spoken explanation rather than being a permanently visible decorative layer.

---

## Phase 5 — Improve Visual Composition and Motion Quality

**Priority: P2**

**Goal:** make every scene visually purposeful and readable.

### Tasks

- [ ] Establish scene composition rules for captions, code, diagrams, characters, and backgrounds.
- [ ] Prevent important content from being hidden by captions or characters.
- [ ] Add controlled camera movement where it improves comprehension.
- [ ] Use transitions only when they support the story; avoid transition noise for its own sake.
- [ ] Improve typography hierarchy and code/diagram readability.
- [ ] Ensure every scene has meaningful visual progression.
- [ ] Avoid static stock footage when an explanatory graphic would communicate better.

### Exit Criteria

The video remains visually engaging without sacrificing technical readability.

---

## Phase 6 — Semantic Video Quality Gates

**Priority: P2**

**Goal:** prevent technically valid but educationally poor videos from reaching upload.

### Extend QA Beyond ffprobe

Add checks for:

- [ ] required visual type present when required by the plan;
- [ ] code block rendered when the plan requires code;
- [ ] diagram rendered when the plan requires a diagram;
- [ ] cartoon action events rendered when requested;
- [ ] captions present and within duration;
- [ ] audio duration matches the master timeline;
- [ ] caption/audio timing error is within tolerance;
- [ ] visual event timing is within tolerance of its target narration event;
- [ ] no scene is accidentally empty or visually static;
- [ ] safe-area violations are detected;
- [ ] final output still passes 1080x1920, 30fps, duration, and audio-stream checks.

### Exit Criteria

A render cannot be marked `ready_to_upload` merely because the MP4 is technically valid. It must also satisfy the semantic video-quality contract.

---

## Phase 7 — Regression and Evaluation Suite

**Priority: P3**

**Goal:** continuously measure video quality as the renderer evolves.

### Test Cases

Create representative scripts for:

1. API request/response flow — diagram + cartoon + captions.
2. Python implementation — code block + highlighted lines + narration.
3. System architecture — architecture diagram + character explanation.
4. Algorithm explanation — diagram + code + step-by-step animation.
5. Concept comparison — comparison diagram + captions.

### Automated Evaluation

For each fixture, record:

- render success/failure;
- duration drift;
- caption timing drift;
- missing visual assets;
- required visual type compliance;
- safe-area violations;
- audio stream validity;
- output dimensions/FPS;
- deterministic render behavior.

### Exit Criteria

Every major renderer change runs against the regression suite before being considered production-ready.

---

## Recommended Implementation Order

```text
Phase 0  Contracts / baseline
   |
   v
Phase 1  Master timeline + sync             <-- FIRST
   |
   +------> Phase 2  Code blocks
   |
   +------> Phase 3  Semantic diagrams
   |
   +------> Phase 4  Content-driven cartoons
              |
              v
Phase 5  Composition / motion quality
              |
              v
Phase 6  Semantic quality gates
              |
              v
Phase 7  Regression / evaluation suite
```

## Definition of Done

A generated educational video is considered high quality only when all of the following are true:

- [ ] narration is natural and complete;
- [ ] audio is the timing source for spoken content;
- [ ] captions are synchronized with spoken words;
- [ ] diagrams are used when they improve explanation of relationships/processes;
- [ ] code is shown when implementation/source code is part of the explanation;
- [ ] cartoon animation is used meaningfully where appropriate;
- [ ] visual events occur at the point they are discussed;
- [ ] captions do not hide important visual content;
- [ ] output is 1080x1920 at 30fps;
- [ ] final MP4 contains valid audio and video streams;
- [ ] semantic quality checks pass before upload.

## Non-Goals

This plan does **not** require replacing Remotion, replacing the existing diagram renderer, or replacing the complete TTS stack. Existing components should be reused where they satisfy the new contracts.

The primary architectural change is to make the **master timeline and semantic video plan authoritative** and make all renderers consume that plan consistently.
