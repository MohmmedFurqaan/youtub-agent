import { AbsoluteFill, Series } from "remotion";
import { SceneRenderer } from "./SceneRenderer";
import type { VideoProps } from "./types";

/**
 * MainComposition — root Remotion composition for the faceless video format.
 *
 * Uses <Series> to chain scenes sequentially based on each scene's
 * duration_in_frames. No characters, no host images — purely narration
 * + background + captions.
 */
export const MainComposition: React.FC<VideoProps> = ({ scenes }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#000000" }}>
      <Series>
        {scenes.map((scene) => (
          <Series.Sequence
            key={scene.scene_number}
            durationInFrames={scene.duration_in_frames}
            layout="none"
          >
            <SceneRenderer scene={scene} />
          </Series.Sequence>
        ))}
      </Series>
    </AbsoluteFill>
  );
};
