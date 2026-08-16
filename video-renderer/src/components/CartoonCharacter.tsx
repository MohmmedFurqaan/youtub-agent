/**
 * CartoonCharacter.tsx
 *
 * Renders a DiceBear cartoon avatar using the HTTP API (no extra bundle size).
 * The avatar is deterministic — seeded from the scene id.
 * An idle bounce animation is applied via Remotion spring().
 *
 * DiceBear styles used per scene role:
 *   hook        → "adventurer"        (bold, expressive)
 *   problem     → "big-smile"         (worried/stressed)
 *   explanation → "bottts-neutral"    (tech robot)
 *   mechanism   → "fun-emoji"         (focused)
 *   insight     → "thumbs"            (celebrating)
 */

import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";

interface Props {
  seed: string;
  storyRole?: string;
  position?: "bottom-left" | "bottom-right" | "bottom-center";
  size?: number;
}

const ROLE_TO_STYLE: Record<string, string> = {
  hook: "adventurer",
  problem: "big-smile",
  explanation: "bottts-neutral",
  mechanism: "fun-emoji",
  insight: "thumbs",
};

// Background circle colors per role
const ROLE_TO_COLOR: Record<string, string> = {
  hook: "f97316",
  problem: "ef4444",
  explanation: "3b82f6",
  mechanism: "8b5cf6",
  insight: "34d399",
};

function buildDiceBearUrl(style: string, seed: string, size: number, bg: string): string {
  const params = new URLSearchParams({
    seed,
    size: String(size),
    backgroundColor: bg,
    backgroundType: "gradientLinear",
    radius: "50",
  });
  return `https://api.dicebear.com/10.x/${style}/svg?${params}`;
}

export const CartoonCharacter: React.FC<Props> = ({
  seed,
  storyRole = "explanation",
  position = "bottom-right",
  size = 320,
}) => {
  const frame = useCurrentFrame();
  const { width, height: _height } = useVideoConfig();

  const style = ROLE_TO_STYLE[storyRole] ?? "bottts-neutral";
  const bgColor = ROLE_TO_COLOR[storyRole] ?? "3b82f6";
  const avatarUrl = buildDiceBearUrl(style, seed, size, bgColor);

  // Entrance spring
  const appear = spring({
    frame,
    fps: 30,
    config: { damping: 14, stiffness: 120, mass: 0.9 },
  });
  const entryY = interpolate(appear, [0, 1], [size * 0.6, 0], {
    extrapolateRight: "clamp",
  });
  const entryOpacity = interpolate(appear, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Idle bounce
  const bounce = Math.sin(frame * 0.08) * 8;
  const tilt = Math.sin(frame * 0.05) * 3;

  // Positioning
  const padding = 60;
  let left: number | undefined;
  let right: number | undefined;
  let bottom: number = 180;

  if (position === "bottom-left") {
    left = padding;
  } else if (position === "bottom-right") {
    right = padding;
  } else {
    left = width / 2 - size / 2;
  }

  return (
    <div
      style={{
        position: "absolute",
        bottom: bottom + entryY,
        left,
        right,
        width: size,
        height: size,
        opacity: entryOpacity,
        transform: `translateY(${bounce}px) rotate(${tilt}deg)`,
        filter: "drop-shadow(0 20px 40px rgba(0,0,0,0.5))",
      }}
    >
      {/* Glow ring behind avatar */}
      <div
        style={{
          position: "absolute",
          inset: -12,
          borderRadius: "50%",
          background: `radial-gradient(circle, #${bgColor}44 0%, transparent 70%)`,
          animation: "none",
        }}
      />
      <img
        src={avatarUrl}
        width={size}
        height={size}
        style={{
          borderRadius: "50%",
          display: "block",
          border: `4px solid #${bgColor}88`,
          boxShadow: `0 0 40px #${bgColor}66, 0 20px 60px rgba(0,0,0,0.4)`,
        }}
        alt="character"
      />
    </div>
  );
};

export default CartoonCharacter;
