import { registerRoot, Composition } from "remotion";
import { MainComposition } from "./MainComposition";
import type { VideoProps } from "./types";
import videoProps from "../../data/metadata/video-props.json";

/**
 * Remotion Root — registers the MainComposition.
 *
 * Default props are loaded from video-props.json so Remotion Studio
 * shows a live preview without needing --props on every run.
 *
 * Headless render:
 *   npm run render:props
 *   → npx remotion render src/index.tsx MainComposition out/video.mp4 \
 *       --props=../data/metadata/video-props.json
 */
const RemotionRoot: React.FC = () => {
  const props = videoProps as VideoProps;

  return (
    // TypeScript infers the generic from `component` — no explicit annotation needed
    <Composition
      id="MainComposition"
      component={MainComposition}
      durationInFrames={props.total_duration_frames}
      fps={props.fps}
      width={1080}
      height={1920}
      defaultProps={props}
    />
  );
};

registerRoot(RemotionRoot);
