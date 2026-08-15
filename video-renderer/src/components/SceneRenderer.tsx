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
  Easing,
} from "remotion";
import type { SceneProp } from "../schemas";
import DiagramRenderer from "./diagrams/DiagramRenderer";
import { SAFE_AREAS } from "./SafeAreas";

interface Props {
  scene: SceneProp;
}

// Very soft paper/noise SVG used as a repeating overlay. Kept low-opacity.
const NOISE_SVG = `<?xml version="1.0" encoding="UTF-8"?><svg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'><filter id='t'><feTurbulence baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix type='saturate' values='0'/></filter><rect width='100%' height='100%' filter='url(%23t)' fill='white' opacity='1'/></svg>`;
const NOISE_DATA_URL = `data:image/svg+xml;utf8,${encodeURIComponent(NOISE_SVG)}`;

// ── Background ────────────────────────────────────────────────────────────────

const backgroundStyles: Record<string, string> = {
  // Subtle, low-contrast gradients for a professional technical look
  "midnight-blue": "linear-gradient(180deg, #061026 0%, #0b1624 100%)",
  "deep-purple": "linear-gradient(180deg, #100a17 0%, #171426 100%)",
  "teal": "linear-gradient(180deg, #052025 0%, #0b2430 100%)",
  "amber": "linear-gradient(180deg, #140f09 0%, #20160f 100%)",
  "slate": "linear-gradient(180deg, #09101a 0%, #121827 100%)",
  "graphite": "linear-gradient(180deg, #0b0b0d 0%, #14171b 100%)",
};

const DiagramBackground: React.FC<{ assetSrc: string; diagram?: any; background?: string; sceneStartMs?: number; sceneDurationMs?: number }> = ({ assetSrc, diagram, background, sceneStartMs, sceneDurationMs }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.02], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const driftX = interpolate(frame, [0, durationInFrames], [-4, 4], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const driftY = interpolate(frame, [0, durationInFrames], [-3, 3], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const resolvedBackground = backgroundStyles[background ?? "midnight-blue"] ?? backgroundStyles["midnight-blue"];

  if (diagram) {
    return (
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          overflow: "hidden",
          background: resolvedBackground,
        }}
      >
        <div
          style={{
            transform: `scale(${scale}) translate(${driftX}px, ${driftY}px)`,
            width: "100%",
            height: "100%",
            filter: "saturate(1.2)",
          }}
        >
          <DiagramRenderer spec={diagram} sceneStartMs={sceneStartMs} sceneDurationMs={sceneDurationMs} />
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
        background: resolvedBackground,
      }}
    >
      <div
        style={{
          transform: `scale(${scale}) translate(${driftX}px, ${driftY}px)`,
          width: "100%",
          height: "100%",
        }}
      >
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

  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.04], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
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

  const opacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const translateY = interpolate(frame, [0, 10], [22, 0], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const scale = interpolate(frame, [0, 12], [0.985, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
    output: "perceptual-scale",
  });

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top: SAFE_AREAS.title.top,
        display: "flex",
        justifyContent: "center",
        padding: "0 72px",
        opacity,
        transform: `translateY(${translateY}px) scale(${scale})`,
      }}
    >
      <div
        style={{
          background: "linear-gradient(180deg, rgba(15, 23, 42, 0.58), rgba(15, 118, 110, 0.18))",
          backdropFilter: "blur(12px)",
          border: "1.5px solid rgba(148, 163, 184, 0.34)",
          borderRadius: 20,
          padding: "18px 30px",
          boxShadow: "0 18px 40px rgba(2, 6, 23, 0.32)",
          maxWidth: "820px",
          width: "100%",
          textAlign: "center",
        }}
      >
        <span
          style={{
            display: "block",
            fontFamily: "'Arial Black', 'Arial', sans-serif",
            fontSize: 68,
            lineHeight: 1.06,
            letterSpacing: 2,
            fontWeight: 900,
            color: "#f8fafc",
            textTransform: "uppercase",
            textShadow: "0 0 18px rgba(125,211,252,0.6)",
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
  const { fps } = useVideoConfig();
  const sceneStartMs = (scene.fromFrame / fps) * 1000;
  const sceneDurationMs = (scene.durationInFrames / fps) * 1000;
  const renderBackground = () => {
    if (scene.assetKind === "diagram" || scene.assetKind === "screen_capture") {
      return <DiagramBackground assetSrc={scene.assetSrc} diagram={(scene as any).diagram} background={scene.background} sceneStartMs={sceneStartMs} sceneDurationMs={sceneDurationMs} />;
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
      {/* Very soft paper/noise overlay (repeating SVG) */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage: `url(${NOISE_DATA_URL})`,
          backgroundRepeat: "repeat",
          backgroundSize: "400px 400px",
          opacity: 0.035,
          mixBlendMode: "overlay",
          pointerEvents: "none",
        }}
      />
      <OnScreenText text={scene.onScreenText} />
      {renderTransition()}
    </>
  );
};
