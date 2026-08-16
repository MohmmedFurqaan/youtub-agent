/**
 * KineticTextOverlay.tsx
 *
 * Large, punchy on-screen text using Google Fonts via @remotion/google-fonts.
 * Uses Bangers font for hook/insight scenes, Outfit for technical scenes.
 * Color-coded and positioned per scene story role.
 */

import React from "react";
import { useCurrentFrame, spring, interpolate, Easing } from "remotion";
import { loadFont as loadBangers } from "@remotion/google-fonts/Bangers";
import { loadFont as loadOutfit } from "@remotion/google-fonts/Outfit";

const { fontFamily: bangersFamily } = loadBangers();
const { fontFamily: outfitFamily } = loadOutfit();

interface Props {
  text: string;
  storyRole?: string;
}

const ROLE_STYLES: Record<string, { color: string; glow: string; font: "bangers" | "outfit"; size: number; top: number }> = {
  hook:        { color: "#ff6b35", glow: "rgba(255,107,53,0.8)", font: "bangers", size: 128, top: 200 },
  problem:     { color: "#ef4444", glow: "rgba(239,68,68,0.75)", font: "bangers", size: 112, top: 180 },
  explanation: { color: "#7dd3fc", glow: "rgba(125,211,252,0.65)", font: "outfit", size: 90, top: 160 },
  mechanism:   { color: "#c4b5fd", glow: "rgba(196,181,253,0.65)", font: "outfit", size: 90, top: 160 },
  insight:     { color: "#34d399", glow: "rgba(52,211,153,0.75)", font: "bangers", size: 118, top: 180 },
};

function splitLines(text: string, max: number): string[] {
  const words = text.split(" ");
  const lines: string[] = [];
  let line = "";
  for (const word of words) {
    if ((line + " " + word).trim().length <= max) {
      line = (line + " " + word).trim();
    } else {
      if (line) lines.push(line);
      line = word;
    }
  }
  if (line) lines.push(line);
  return lines;
}

export const KineticTextOverlay: React.FC<Props> = ({ text, storyRole = "explanation" }) => {
  const frame = useCurrentFrame();
  const rs = ROLE_STYLES[storyRole] ?? ROLE_STYLES.explanation;
  const fontFamily = rs.font === "bangers" ? bangersFamily : outfitFamily;

  const appear = spring({ frame, fps: 30, config: { damping: 12, stiffness: 180, mass: 0.6 } });
  const scale = interpolate(appear, [0, 1], [0.72, 1], { extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const opacity = interpolate(appear, [0, 0.4, 1], [0, 1, 1], { extrapolateRight: "clamp" });
  const slideY = interpolate(appear, [0, 1], [50, 0], { extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const glowPulse = storyRole === "hook" ? 1 + 0.15 * Math.sin(frame * 0.12) : 1;

  const lines = splitLines(text, rs.font === "bangers" ? 12 : 18);

  return (
    <div
      style={{
        position: "absolute",
        top: rs.top,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        padding: "0 56px",
        opacity,
        transform: `translateY(${slideY}px) scale(${scale})`,
        zIndex: 20,
      }}
    >
      <div style={{ textAlign: "center" }}>
        {lines.map((line, i) => (
          <span
            key={i}
            style={{
              display: "block",
              fontFamily,
              fontSize: rs.size,
              fontWeight: rs.font === "outfit" ? 800 : 400,
              letterSpacing: rs.font === "bangers" ? 6 : 1,
              lineHeight: 1.05,
              color: rs.color,
              textTransform: "uppercase",
              textShadow: [
                `0 0 ${30 * glowPulse}px ${rs.glow}`,
                `0 0 ${60 * glowPulse}px ${rs.glow}`,
                "0 4px 24px rgba(0,0,0,0.8)",
                "2px 2px 0 rgba(0,0,0,0.5)",
              ].join(", "),
            }}
          >
            {line}
          </span>
        ))}
      </div>
    </div>
  );
};

export default KineticTextOverlay;
