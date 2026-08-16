/**
 * components/SceneRenderer.tsx
 *
 * Renders a single scene with:
 *  - ParticleBackground  (animated grid/dots — replaces flat gradients)
 *  - ReactFlowDiagram    (node-edge diagrams with DiceBear avatars)
 *  - CartoonCharacter    (DiceBear avatar with idle bounce)
 *  - KineticTextOverlay  (large Google Fonts headline)
 *  - Transition overlays (cut | fade | slide | zoom-punch | glitch)
 *
 * Captions are removed for this phase.
 */

import React from "react";
import {
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  Img,
  OffthreadVideo,
  staticFile,
  Easing,
  AbsoluteFill,
} from "remotion";
import type { SceneProp } from "../schemas";
import { ParticleBackground } from "./ParticleBackground";
import { CartoonCharacter } from "./CartoonCharacter";
import { KineticTextOverlay } from "./KineticTextOverlay";
import DiagramRenderer from "./diagrams/DiagramRenderer";

interface Props {
  scene: SceneProp;
  storyRole?: string;
}

// ── Transitions ───────────────────────────────────────────────────────────────

const FadeIn: React.FC = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 12], [1, 0], { extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", inset: 0, background: "#000", opacity, pointerEvents: "none" }} />
  );
};

const SlideIn: React.FC = () => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const x = interpolate(frame, [0, 18], [width, 0], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
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

const ZoomPunchIn: React.FC = () => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, 14], [1.35, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const opacity = interpolate(frame, [0, 6], [0, 1], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill
      style={{
        transform: `scale(${scale})`,
        opacity,
        transformOrigin: "center center",
        pointerEvents: "none",
      }}
    />
  );
};

const GlitchIn: React.FC = () => {
  const frame = useCurrentFrame();
  if (frame > 10) return null;

  const glitchFrame = frame % 3;
  const opacity = interpolate(frame, [0, 10], [1, 0], { extrapolateRight: "clamp" });

  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", pointerEvents: "none", opacity }}>
      {/* Horizontal glitch bands */}
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            height: 80 + i * 40,
            top: 300 + i * 220 + (glitchFrame === i ? 20 : -10),
            background: i % 2 === 0 ? "rgba(239,68,68,0.35)" : "rgba(96,165,250,0.35)",
            mixBlendMode: "exclusion",
          }}
        />
      ))}
      {/* Scanline */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "repeating-linear-gradient(0deg, rgba(0,0,0,0.08) 0px, rgba(0,0,0,0.08) 1px, transparent 1px, transparent 4px)",
        }}
      />
    </div>
  );
};

// ── Still / Video backgrounds for non-diagram scenes ─────────────────────────

const StillBackground: React.FC<{ assetSrc: string }> = ({ assetSrc }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.05], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
      <div style={{ transform: `scale(${scale})`, width: "100%", height: "100%" }}>
        <Img src={staticFile(assetSrc)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </div>
    </div>
  );
};

const VideoBackground: React.FC<{ assetSrc: string }> = ({ assetSrc }) => (
  <div style={{ position: "absolute", inset: 0 }}>
    <OffthreadVideo src={staticFile(assetSrc)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
  </div>
);

// ── Vignette overlay ──────────────────────────────────────────────────────────

const Vignette: React.FC = () => (
  <div
    style={{
      position: "absolute",
      inset: 0,
      background: "radial-gradient(ellipse at center, transparent 30%, rgba(0,0,0,0.65) 100%)",
      pointerEvents: "none",
    }}
  />
);

// ── Scene ─────────────────────────────────────────────────────────────────────

export const SceneRenderer: React.FC<Props> = ({ scene, storyRole }) => {
  const { fps } = useVideoConfig();
  const sceneStartMs = (scene.fromFrame / fps) * 1000;
  const sceneDurationMs = (scene.durationInFrames / fps) * 1000;

  // Infer role from scene id if not passed (scene-01 = hook, etc.)
  const roleFromId = (() => {
    if (scene.id.includes("01")) return "hook";
    if (scene.id.includes("02")) return "problem";
    if (scene.id.includes("03")) return "explanation";
    if (scene.id.includes("04")) return "mechanism";
    if (scene.id.includes("05")) return "insight";
    return "explanation";
  })();
  const role = storyRole ?? roleFromId;

  // Character position — alternate sides per scene
  const charPosition = ["01", "03", "05"].some((s) => scene.id.includes(s))
    ? "bottom-right"
    : "bottom-left";

  // Background
  const renderBackground = () => {
    if (scene.assetKind === "diagram" || scene.assetKind === "screen_capture") {
      return <ParticleBackground background={scene.background} />;
    }
    if (scene.assetKind === "image") {
      return <StillBackground assetSrc={scene.assetSrc} />;
    }
    return <VideoBackground assetSrc={scene.assetSrc} />;
  };

  // Diagram layer
  const renderDiagram = () => {
    const diag = (scene as any).diagram;
    if (!diag) return null;
    return (
      <div style={{ position: "absolute", inset: 0 }}>
        <DiagramRenderer
          spec={diag}
          sceneStartMs={sceneStartMs}
          sceneDurationMs={sceneDurationMs}
        />
      </div>
    );
  };

  // Transition
  const renderTransition = () => {
    switch (scene.transition) {
      case "fade":  return <FadeIn />;
      case "slide": return <SlideIn />;
      case "zoom-punch" as any: return <ZoomPunchIn />;
      case "glitch" as any: return <GlitchIn />;
      default: return null;
    }
  };

  return (
    <>
      {renderBackground()}
      <Vignette />
      {renderDiagram()}
      <CartoonCharacter
        seed={scene.id}
        storyRole={role}
        position={charPosition as any}
        size={280}
      />
      <KineticTextOverlay text={scene.onScreenText} storyRole={role} />
      {renderTransition()}
    </>
  );
};
