/**
 * components/SceneRenderer.tsx
 *
 * Renders a single scene inside a <Sequence>:
 *   - SVG diagram OR still image OR video background
 *   - Ken Burns slow zoom for still assets
 *   - On-screen text overlay
 *
 * All animation uses useCurrentFrame() + interpolate() / spring() — no CSS
 * transitions (which are non-deterministic in Remotion's renderer).
 */

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Img,
  Video,
  Sequence,
  OffthreadVideo,
  staticFile,
} from "remotion";
import type { SceneProp } from "../schemas";
import DiagramRenderer from "./diagrams/DiagramRenderer";

interface Props {
  scene: SceneProp;
}

// ── Background ────────────────────────────────────────────────────────────────

const DiagramBackground: React.FC<{ assetSrc: string; diagram?: any }> = ({ assetSrc, diagram }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // Slow Ken Burns zoom: 1.0 → 1.06 over the scene duration
  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.06], {
    extrapolateRight: "clamp",
  });

  // If a native diagram payload is present, render it centered; otherwise
  // fall back to the static image asset.
  if (diagram) {
    return (
      <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden" }}>
        <div style={{ transform: `scale(${scale})`, width: "100%", height: "100%" }}>
          <DiagramRenderer spec={diagram} />
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        overflow: "hidden",
        background: "linear-gradient(180deg, #0a0e27 0%, #0d1b4b 100%)",
      }}
    >
      <div style={{ transform: `scale(${scale})`, width: "100%", height: "100%" }}>
        <Img
          src={staticFile(assetSrc)}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </div>
    </div>
  );
};

const StillBackground: React.FC<{ assetSrc: string }> = ({ assetSrc }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.08], {
    extrapolateRight: "clamp",
  });

  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
      <div style={{ transform: `scale(${scale})`, width: "100%", height: "100%" }}>
        <Img
          src={staticFile(assetSrc)}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </div>
    </div>
  );
};

const VideoBackground: React.FC<{ assetSrc: string }> = ({ assetSrc }) => (
  <div style={{ position: "absolute", inset: 0 }}>
    <OffthreadVideo
      src={staticFile(assetSrc)}
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
    />
  </div>
);

// ── On-screen text ────────────────────────────────────────────────────────────

const OnScreenText: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Slide up + fade in from frame 0 → 12
  const opacity = interpolate(frame, [0, 12], [0, 1], {
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(frame, [0, 12], [30, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        bottom: 220,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        opacity,
        transform: `translateY(${translateY}px)`,
        padding: "0 60px",
      }}
    >
      <div
        style={{
          background: "rgba(66, 133, 244, 0.18)",
          backdropFilter: "blur(8px)",
          border: "2px solid rgba(66, 133, 244, 0.6)",
          borderRadius: 16,
          padding: "20px 48px",
        }}
      >
        <span
          style={{
            fontFamily: "'Arial Black', 'Arial', sans-serif",
            fontSize: 72,
            fontWeight: 900,
            color: "#ffffff",
            letterSpacing: 6,
            textTransform: "uppercase",
            textShadow: "0 0 40px rgba(66,133,244,0.8)",
          }}
        >
          {text}
        </span>
      </div>
    </div>
  );
};

// ── Transition overlay ────────────────────────────────────────────────────────

const FadeTransitionIn: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 10], [1, 0], {
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: "#000",
        opacity,
        pointerEvents: "none",
      }}
    />
  );
};

const SlideTransitionIn: React.FC = () => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const x = interpolate(frame, [0, 15], [width, 0], {
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        background: "#0a0e27",
        transform: `translateX(${x}px)`,
        pointerEvents: "none",
      }}
    />
  );
};

// ── Scene component ───────────────────────────────────────────────────────────

export const SceneRenderer: React.FC<Props> = ({ scene }) => {
  const renderBackground = () => {
    if (scene.assetKind === "diagram" || scene.assetKind === "screen_capture") {
      return <DiagramBackground assetSrc={scene.assetSrc} diagram={(scene as any).diagram} />;
    }
    if (scene.assetKind === "image") {
      return <StillBackground assetSrc={scene.assetSrc} />;
    }
    // stock_video
    return <VideoBackground assetSrc={scene.assetSrc} />;
  };

  const renderTransition = () => {
    if (scene.transition === "fade") return <FadeTransitionIn />;
    if (scene.transition === "slide") return <SlideTransitionIn />;
    return null; // cut — no overlay
  };

  return (
    <>
      {renderBackground()}
      {/* Vignette for depth */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,0.55) 100%)",
          pointerEvents: "none",
        }}
      />
      <OnScreenText text={scene.onScreenText} />
      {renderTransition()}
    </>
  );
};
