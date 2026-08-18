/**
 * Root.tsx
 *
 * Registers all Remotion compositions for yt-agent.
 * The ShortVideo composition renders a 30-second 1080×1920 vertical MP4.
 */

import React from "react";
import { Composition } from "remotion";
import { ShortVideo } from "./compositions/ShortVideo";
import { shortVideoSchema } from "./schemas";

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

export const RemotionRootWithSounds = RemotionRoot;
