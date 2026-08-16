/**
 * compositions/ShortVideo.tsx
 *
 * Root composition for a 30-second vertical YouTube Short.
 *
 * Structure:
 *   - <Audio> narration.mp3 — full 30 s
 *   - Per-scene <Sequence> → SceneRenderer
 *
 * Captions removed for Phase 1.
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
  captions = [],
  musicSrc,
}) => {
  const { width, height, fps, durationInFrames } = useVideoConfig();

  // Validation
  React.useMemo(() => {
    if (durationInFrames !== 30 * fps) {
      throw new Error(`Composition must be ${30 * fps} frames (30s × ${fps}fps).`);
    }
    const sorted = [...scenes].sort((a, b) => a.fromFrame - b.fromFrame);
    if (sorted.length > 0 && sorted[0].fromFrame !== 0) {
      throw new Error("First scene must start at frame 0.");
    }
    for (let i = 1; i < sorted.length; i++) {
      const prev = sorted[i - 1];
      const cur = sorted[i];
      if (cur.fromFrame !== prev.fromFrame + prev.durationInFrames) {
        throw new Error(`Scenes not contiguous: ${cur.id} does not follow ${prev.id}.`);
      }
    }
  }, [scenes, fps, durationInFrames]);

  return (
    <AbsoluteFill style={{ background: "#030712", width, height }}>
      {/* Background music */}
      {musicSrc && (
        <Audio src={staticFile(musicSrc)} volume={0.12} loop />
      )}

      {/* Narration audio */}
      <Audio src={staticFile(audioSrc)} />

      {/* Scenes */}
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

      {/* Global captions overlay */}
      {captions.length > 0 && <CaptionsOverlay captions={captions} />}
    </AbsoluteFill>
  );
};
