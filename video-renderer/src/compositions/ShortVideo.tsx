/**
 * compositions/ShortVideo.tsx
 *
 * Root composition for a 30-second vertical YouTube Short.
 *
 * Structure:
 *   - <Audio> narration.mp3 — full 30 s
 *   - <Audio> music track — looped ambient background
 *   - Per-scene <Sequence> → SceneRenderer (visuals)
 *   - Per-scene <Sequence> → <Audio> transition sound effects
 *   - Global captions overlay
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
import { SOUND_LIBRARY, TRANSITION_SOUND, STORY_ROLE_SOUND, EVENT_SOUND } from "../config/SoundConfig";
import type { SceneProp } from "../schemas";

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

  /** Build the list of sound-effect Sequences for the current scene set. */
  const renderSceneSounds = (sortedScenes: SceneProp[]): React.ReactElement[] => {
    const elements: React.ReactElement[] = [];

    sortedScenes.forEach((scene) => {
      const transitionSound = TRANSITION_SOUND[scene.transition] || "ui/toggle_on";
      const roleSound = STORY_ROLE_SOUND[scene.storyRole || ""] || "ui/item_select";
      const eventSound = scene.diagram ? EVENT_SOUND[scene.diagram.template] || "ui/item_select" : null;

      // Transition sound — plays at scene start
      const tSound = SOUND_LIBRARY[transitionSound];
      elements.push(
        <Sequence
          key={`sfx-trans-${scene.id}`}
          from={scene.fromFrame}
          durationInFrames={fps} // 1s window is enough for short SFX
          name={`sfx-transition-${scene.id}`}
        >
          <Audio src={tSound.src} volume={tSound.volume} />
        </Sequence>,
      );

      // Story-role sound — plays 6 frames after scene start (after transition)
      const rSound = SOUND_LIBRARY[roleSound];
      elements.push(
        <Sequence
          key={`sfx-role-${scene.id}`}
          from={scene.fromFrame + 6}
          durationInFrames={fps}
          name={`sfx-role-${scene.id}`}
        >
          <Audio src={rSound.src} volume={rSound.volume} />
        </Sequence>,
      );

      // Diagram event sound — plays 12 frames after scene start
      if (eventSound) {
        const eSound = SOUND_LIBRARY[eventSound];
        elements.push(
          <Sequence
            key={`sfx-event-${scene.id}`}
            from={scene.fromFrame + 12}
            durationInFrames={fps}
            name={`sfx-event-${scene.id}`}
          >
            <Audio src={eSound.src} volume={eSound.volume} />
          </Sequence>,
        );
      }
    });

    return elements;
  };

  const sortedScenes = [...scenes].sort((a, b) => a.fromFrame - b.fromFrame);

  return (
    <AbsoluteFill style={{ background: "#030712", width, height }}>
      {/* Background music */}
      {musicSrc && (
        <Audio src={staticFile(musicSrc)} volume={0.12} loop />
      )}

      {/* Narration audio */}
      <Audio src={staticFile(audioSrc)} />

      {/* Scene visual layers */}
      {sortedScenes.map((scene) => (
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

      {/* Animation sound effects (rendered into final MP4) */}
      {renderSceneSounds(sortedScenes)}

      {/* Global captions overlay */}
      {captions.length > 0 && <CaptionsOverlay captions={captions} />}
    </AbsoluteFill>
  );
};
