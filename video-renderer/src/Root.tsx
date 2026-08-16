/**
 * Root.tsx
 *
 * Registers all Remotion compositions for yt-agent.
 * The ShortVideo composition renders a 30-second 1080×1920 vertical MP4.
 *
 * SoundProvider wraps each composition so that `react-sounds` is available
 * for interactive playback in Remotion Studio.
 */

import React from "react";
import { Composition } from "remotion";
import { SoundProvider } from "react-sounds";
import { ShortVideo } from "./compositions/ShortVideo";
import { shortVideoSchema } from "./schemas";
import { SoundName } from "./config/SoundConfig";

const preloadSounds: SoundName[] = [
  "ui/pop_open",
  "ui/pop_close",
  "ui/buzz",
  "ui/button_squishy",
  "ui/toggle_on",
  "ui/item_select",
  "ui/success_chime",
  "arcade/coin",
];

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ShortVideo"
        component={ShortVideo}
        schema={shortVideoSchema}
        width={1080}
        height={1920}
        fps={30}
        durationInFrames={900} /* 30 s × 30 fps */
        defaultProps={{
          audioSrc: "",
          scenes: [],
          captions: [],
          title: "Preview",
        }}
      />
    </>
  );
};

/**
 * Wrapper that adds SoundProvider for interactive preview.
 * Used by the Player / Studio to enable react-sounds playback.
 */
export const RemotionRootWithSounds: React.FC = () => (
  <SoundProvider preload={preloadSounds} initialEnabled>
    <RemotionRoot />
  </SoundProvider>
);
