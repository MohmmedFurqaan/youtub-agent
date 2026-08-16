/**
 * components/CaptionsOverlay.tsx
 *
 * TikTok-style word-at-a-time kinetic pop captions.
 *
 * Displays the current word based on caption timestamps and the
 * current playback position. Each word pops in with a spring animation,
 * and keywords (API, server, database, etc.) are highlighted in amber.
 *
 * Positioned in the mobile safe area (above 140px bottom margin).
 */

import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from "remotion";
import { SAFE_AREAS } from "./SafeAreas";
import type { Caption } from "../schemas";

interface Props {
  captions: Caption[];
}

const KEYWORDS = new Set([
  "api", "server", "database", "db", "cache", "queue", "request", "response",
  "client", "user", "data", "cloud", "microservice", "docker", "kubernetes",
  "auth", "token", "dns", "http", "rest", "json", "websocket", "endpoint",
  "latency", "throughput", "load", "security", "encryption", "ssl", "tls",
]);

function isKeyword(word: string): boolean {
  const lower = word.toLowerCase().replace(/[^a-z0-9]/g, "");
  return KEYWORDS.has(lower);
}

export const CaptionsOverlay: React.FC<Props> = ({ captions }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentMs = (frame / fps) * 1000;

  const current = captions.find(
    (cap) => currentMs >= cap.startMs && currentMs < cap.endMs
  );

  if (!current) return null;

  const word = current.text;
  const capDuration = current.endMs - current.startMs;
  const capFrame = currentMs - current.startMs;

  const pop = spring({
    frame: Math.max(0, capFrame),
    fps,
    config: { damping: 12, stiffness: 200, mass: 0.6 },
  });

  const scale = interpolate(pop, [0, 1], [0.5, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const opacity = interpolate(pop, [0, 0.3, 1], [0, 1, 1], {
    extrapolateRight: "clamp",
  });

  const fadeOut = interpolate(
    capFrame,
    [capDuration * 0.7, capDuration],
    [1, 0],
    { extrapolateRight: "clamp", extrapolateLeft: "clamp" }
  );

  const finalOpacity = opacity * fadeOut;
  const finalScale = interpolate(fadeOut, [0, 1], [1, 0.85], {
    extrapolateRight: "clamp",
  }) * scale;

  const highlight = isKeyword(word);

  return (
    <div
      style={{
        position: "absolute",
        bottom: SAFE_AREAS.captions.bottom + 20,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        paddingLeft: 60,
        paddingRight: 60,
        opacity: finalOpacity,
        zIndex: 30,
      }}
    >
      <span
        style={{
          fontFamily: "'Inter', 'Arial', sans-serif",
          fontSize: 56,
          fontWeight: 900,
          color: highlight ? "#fbbf24" : "#ffffff",
          textAlign: "center",
          display: "inline-block",
          lineHeight: 1.2,
          textShadow: highlight
            ? "0 0 20px rgba(251,191,36,0.8), 0 0 40px rgba(251,191,36,0.4), 0 2px 8px rgba(0,0,0,0.9)"
            : "0 2px 12px rgba(0,0,0,0.85)",
          transform: `scale(${finalScale})`,
          padding: "8px 18px",
          background: "rgba(15, 23, 42, 0.55)",
          borderRadius: 14,
          border: highlight
            ? "2px solid rgba(251,191,36,0.6)"
            : "1px solid rgba(148, 163, 184, 0.25)",
          backdropFilter: "blur(8px)",
        }}
      >
        {word}
      </span>
    </div>
  );
};
