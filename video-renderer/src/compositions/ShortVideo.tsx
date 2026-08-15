/**
 * compositions/ShortVideo.tsx
 *
 * The root composition component for a 30-second vertical YouTube Short.
 *
 * Structure:
 *   - <Audio> — single narration.mp3 playing for the full 30 s
 *   - Per-scene <Sequence> — renders SceneRenderer in its time window
 *   - <CaptionsOverlay> — rendered above all scenes for the full duration
 *
 * Props come from props.json (written by run_pipeline.py) and are validated
 * by the Zod shortVideoSchema before the composition renders.
 */

import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  staticFile,
  useVideoConfig,
} from "remotion";
import type { ShortVideoProps } from "../schemas";
import { SceneRenderer } from "../components/SceneRenderer";
import { CaptionsOverlay } from "../components/CaptionsOverlay";

export const ShortVideo: React.FC<ShortVideoProps> = ({
  audioSrc,
  scenes,
  captions,
}) => {
  const { width, height } = useVideoConfig();
  const { fps, durationInFrames } = useVideoConfig();

  // Validation: fail loudly if basic invariants are violated
  React.useMemo(() => {
    const totalMs = (durationInFrames / fps) * 1000;
    if (durationInFrames !== 30 * fps) {
      throw new Error(
        `Composition durationInFrames must be ${30 * fps} (30s × ${fps}fps).`,
      );
    }

    // Scenes contiguous check
    const sorted = [...scenes].sort((a, b) => a.fromFrame - b.fromFrame);
    if (sorted.length > 0 && sorted[0].fromFrame !== 0) {
      throw new Error(`First scene must start at frame 0.`);
    }
    for (let i = 1; i < sorted.length; i++) {
      const prev = sorted[i - 1];
      const cur = sorted[i];
      if (cur.fromFrame !== prev.fromFrame + prev.durationInFrames) {
        throw new Error(
          `Scenes must be contiguous: scene ${cur.id} does not follow ${prev.id}.`,
        );
      }
    }

    // Captions within total duration
    for (const c of captions) {
      if (c.endMs > totalMs) {
        throw new Error(`Caption ends after total video duration: ${c.text}`);
      }
    }

    // Scene-level animation validation
    for (const s of scenes) {
      const sceneMs = (s.durationInFrames / fps) * 1000;
      const diag = (s as any).diagram;
      if (diag && diag.data && Array.isArray(diag.data.animationTimeline)) {
        for (const ev of diag.data.animationTimeline) {
          if (ev.durationMs <= 0)
            throw new Error(
              `Animation event duration must be > 0 in scene ${s.id}`,
            );
          if (ev.atMs < 0 || ev.atMs + ev.durationMs > sceneMs) {
            throw new Error(
              `Animation event outside scene bounds in scene ${s.id}`,
            );
          }
          // reference checks
          if (ev.from) {
            const exists = diag.data.nodes.find((n: any) => n.id === ev.from);
            if (!exists)
              throw new Error(
                `Animation event references unknown node '${ev.from}' in scene ${s.id}`,
              );
          }
          if (ev.to) {
            const exists = diag.data.nodes.find((n: any) => n.id === ev.to);
            if (!exists)
              throw new Error(
                `Animation event references unknown node '${ev.to}' in scene ${s.id}`,
              );
          }
          if (ev.target) {
            const exists = diag.data.nodes.find((n: any) => n.id === ev.target);
            if (!exists)
              throw new Error(
                `Animation event targets unknown node '${ev.target}' in scene ${s.id}`,
              );
          }
        }
      }
    }
  }, [scenes, captions, fps, durationInFrames]);

  return (
    <AbsoluteFill style={{ background: "#0a0e27", width, height }} from={74}>
      {/* Single narration audio track for the full video */}
      <Audio src={staticFile(audioSrc)} />
      {/* Scene layers — each occupies its exact frame window */}
      {scenes.map((scene) => (
        <Sequence
          key={scene.id}
          from={scene.fromFrame}
          durationInFrames={scene.durationInFrames}
          name={scene.id}
        >
          <AbsoluteFill>
            <SceneRenderer scene={scene} />
          </AbsoluteFill>
        </Sequence>
      ))}
      {/* Caption overlay — spans the full composition duration */}
      <CaptionsOverlay captions={captions} />
    </AbsoluteFill>
  );
};
