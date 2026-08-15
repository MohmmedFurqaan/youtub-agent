/**
 * components/CaptionsOverlay.tsx
 *
 * Safe-area-aware caption layer.
 *
 * Displays the current word/phrase based on caption timestamps and the
 * current playback position.  Uses useCurrentFrame() only — no CSS animation.
 *
 * Captions are rendered in a safe-area bottom zone (above 120px from bottom)
 * with a high-contrast semi-transparent background for readability.
 */

import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import { SAFE_AREAS } from "./SafeAreas";
import type { Caption } from "../schemas";

interface Props {
  captions: Caption[];
}

function getCurrentCaption(
  captions: Caption[],
  currentMs: number
): Caption | null {
  // Find the caption whose window contains currentMs
  for (const cap of captions) {
    if (currentMs >= cap.startMs && currentMs < cap.endMs) {
      return cap;
    }
  }
  return null;
}

export const CaptionsOverlay: React.FC<Props> = ({ captions }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentMs = (frame / fps) * 1000;

  const current = getCurrentCaption(captions, currentMs);

  if (!current) return null;

  // Fade in quickly at caption start, hold, fade out at end
  const capDuration = current.endMs - current.startMs;
  const capFrame = currentMs - current.startMs;
  const fadeFrames = Math.min(3, capDuration / 2);

  const opacity = interpolate(
    capFrame,
    [0, fadeFrames, capDuration - fadeFrames, capDuration],
    [0, 1, 1, 0],
    { extrapolateRight: "clamp", extrapolateLeft: "clamp" }
  );

  return (
    <div
      style={{
        position: "absolute",
        bottom: SAFE_AREAS.captions.bottom,           // safe area above bottom edge
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        paddingLeft: 60,
        paddingRight: 60,
        opacity,
      }}
    >
      <div
        style={{
          background: "rgba(15, 23, 42, 0.74)",
          borderRadius: 14,
          border: "1px solid rgba(148, 163, 184, 0.4)",
          padding: "16px 30px",
          maxWidth: "82%",
        }}
      >
        <span
          style={{
            fontFamily: "'Arial', sans-serif",
            fontSize: 44,
            fontWeight: 700,
            color: "#ffffff",
            textAlign: "center",
            display: "block",
            lineHeight: 1.2,
            textShadow: "0 2px 8px rgba(0,0,0,0.8)",
          }}
        >
          {current.text}
        </span>
      </div>
    </div>
  );
};
