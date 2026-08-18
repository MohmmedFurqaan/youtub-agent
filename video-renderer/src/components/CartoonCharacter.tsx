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
  action?:
    | "talk"
    | "point"
    | "think"
    | "surprised"
    | "send"
    | "receive"
    | "walk"
    | "celebrate"
    | "error"
    | "idle";
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

const ACTION_TO_STYLE: Record<string, string> = {
  talk: "bottts-neutral",
  point: "adventurer",
  think: "fun-emoji",
  surprised: "big-smile",
  send: "bottts-neutral",
  receive: "thumbs",
  walk: "adventurer",
  celebrate: "thumbs",
  error: "big-smile",
  idle: "bottts-neutral",
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
  action = "idle",
}) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();

  const style = ACTION_TO_STYLE[action] ?? ROLE_TO_STYLE[storyRole] ?? "bottts-neutral";
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

  // Action-driven motion dynamics
  let bounce = Math.sin(frame * 0.08) * 8;
  let tilt = Math.sin(frame * 0.05) * 3;
  let scaleAction = 1.0;

  if (action === "talk") {
    bounce = Math.sin(frame * 0.25) * 12;
  } else if (action === "point") {
    tilt = -12 + Math.sin(frame * 0.1) * 4;
  } else if (action === "think") {
    tilt = 15;
    bounce = Math.sin(frame * 0.04) * 4;
  } else if (action === "surprised") {
    scaleAction = 1.1 + Math.abs(Math.sin(frame * 0.2)) * 0.08;
    bounce = -10;
  } else if (action === "celebrate") {
    bounce = -15 + Math.abs(Math.sin(frame * 0.3)) * 25;
    tilt = Math.sin(frame * 0.2) * 10;
  } else if (action === "walk") {
    bounce = Math.abs(Math.sin(frame * 0.2)) * 14;
    tilt = Math.sin(frame * 0.15) * 6;
  } else if (action === "error") {
    tilt = (frame % 4 < 2 ? 6 : -6);
  }

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
        transform: `translateY(${bounce}px) rotate(${tilt}deg) scale(${scaleAction})`,
        filter: "drop-shadow(0 20px 40px rgba(0,0,0,0.5))",
        zIndex: 25,
      }}
    >
      {/* Glow ring behind avatar */}
      <div
        style={{
          position: "absolute",
          inset: -12,
          borderRadius: "50%",
          background: `radial-gradient(circle, #${bgColor}44 0%, transparent 70%)`,
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
