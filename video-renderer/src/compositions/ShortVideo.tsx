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
import { AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig } from "remotion";
import type { ShortVideoProps } from "../schemas";
import { SceneRenderer } from "../components/SceneRenderer";
import { CaptionsOverlay } from "../components/CaptionsOverlay";

export const ShortVideo: React.FC<ShortVideoProps> = ({
  audioSrc,
  scenes,
  captions,
}) => {
  const { width, height } = useVideoConfig();

  return (
    <AbsoluteFill style={{ background: "#0a0e27", width, height }}>
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
