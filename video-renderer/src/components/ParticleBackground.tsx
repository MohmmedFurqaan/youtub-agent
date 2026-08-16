/**
 * ParticleBackground.tsx
 *
 * Animated particle/grid background that replaces flat CSS gradients.
 * Uses only Remotion-safe APIs (no Math.random inside render).
 * All particle positions are computed deterministically from their index.
 */

import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from "remotion";

interface Props {
  /** One of the named palettes */
  palette?: PaletteKey;
  background?: string;
}

type PaletteKey = "hook" | "problem" | "explanation" | "mechanism" | "insight";

// Map scene background names → richer color palettes
const PALETTE_MAP: Record<string, PaletteKey> = {
  "midnight-blue": "explanation",
  "deep-purple": "mechanism",
  "teal": "insight",
  "amber": "problem",
  "slate": "explanation",
  "graphite": "insight",
};

const PALETTES = {
  hook: {
    bg1: "#1a0520",
    bg2: "#2d0a14",
    grid: "rgba(239,68,68,0.15)",
    glow: "rgba(239,68,68,0.6)",
    particle: "#f97316",
    particle2: "#ec4899",
    accent: "#fbbf24",
  },
  problem: {
    bg1: "#110a00",
    bg2: "#1f1000",
    grid: "rgba(245,158,11,0.15)",
    glow: "rgba(245,158,11,0.5)",
    particle: "#f59e0b",
    particle2: "#ef4444",
    accent: "#fde68a",
  },
  explanation: {
    bg1: "#040c1a",
    bg2: "#061026",
    grid: "rgba(96,165,250,0.14)",
    glow: "rgba(59,130,246,0.5)",
    particle: "#3b82f6",
    particle2: "#8b5cf6",
    accent: "#7dd3fc",
  },
  mechanism: {
    bg1: "#0d0520",
    bg2: "#100a2a",
    grid: "rgba(139,92,246,0.14)",
    glow: "rgba(139,92,246,0.5)",
    particle: "#8b5cf6",
    particle2: "#06b6d4",
    accent: "#c4b5fd",
  },
  insight: {
    bg1: "#001a10",
    bg2: "#00200f",
    grid: "rgba(52,211,153,0.15)",
    glow: "rgba(52,211,153,0.5)",
    particle: "#34d399",
    particle2: "#06b6d4",
    accent: "#a7f3d0",
  },
};

// Deterministic "random" — seeded by index so it's render-stable
function drand(seed: number): number {
  const x = Math.sin(seed + 1) * 10000;
  return x - Math.floor(x);
}

interface Particle {
  x: number;
  y: number;
  r: number;
  speed: number;
  phase: number;
  opacity: number;
}

function makeParticles(count: number, w: number, h: number): Particle[] {
  return Array.from({ length: count }, (_, i) => ({
    x: drand(i * 3) * w,
    y: drand(i * 3 + 1) * h,
    r: 2 + drand(i * 3 + 2) * 4,
    speed: 0.3 + drand(i * 7) * 0.7,
    phase: drand(i * 13) * Math.PI * 2,
    opacity: 0.3 + drand(i * 17) * 0.5,
  }));
}

export const ParticleBackground: React.FC<Props> = ({
  palette,
  background,
}) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  // Resolve palette
  const palKey: PaletteKey =
    palette ??
    (background ? (PALETTE_MAP[background] ?? "explanation") : "explanation");
  const colors = PALETTES[palKey];

  // Grid line spacing
  const cols = 8;
  const rows = 14;
  const cellW = width / cols;
  const cellH = height / rows;

  // Particles — computed once from deterministic seed
  const particles = React.useMemo(
    () => makeParticles(32, width, height),
    [width, height]
  );

  // Global pulse / breathe effect
  const breathe = Math.sin(frame * 0.04) * 0.5 + 0.5; // 0..1

  // Slow background drift
  const driftX = interpolate(frame, [0, 900], [-30, 30], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.4, 0, 0.6, 1),
  });
  const driftY = interpolate(frame, [0, 900], [-20, 20], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.4, 0, 0.6, 1),
  });

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        overflow: "hidden",
        background: `linear-gradient(160deg, ${colors.bg1} 0%, ${colors.bg2} 100%)`,
      }}
    >
      <svg
        width={width}
        height={height}
        style={{ position: "absolute", inset: 0 }}
        viewBox={`${driftX} ${driftY} ${width} ${height}`}
      >
        {/* Radial glow */}
        <defs>
          <radialGradient id="centerGlow" cx="50%" cy="45%" r="55%">
            <stop
              offset="0%"
              stopColor={colors.glow}
              stopOpacity={0.18 + breathe * 0.06}
            />
            <stop offset="100%" stopColor="transparent" stopOpacity={0} />
          </radialGradient>
          <radialGradient id="topGlow" cx="20%" cy="10%" r="35%">
            <stop
              offset="0%"
              stopColor={colors.particle2}
              stopOpacity={0.08 + breathe * 0.04}
            />
            <stop offset="100%" stopColor="transparent" stopOpacity={0} />
          </radialGradient>
        </defs>

        {/* Dot grid */}
        {Array.from({ length: cols + 1 }, (_, ci) =>
          Array.from({ length: rows + 1 }, (_, ri) => {
            const x = ci * cellW;
            const y = ri * cellH;
            const dist = Math.sqrt(
              Math.pow((x - width / 2) / width, 2) +
                Math.pow((y - height / 2) / height, 2)
            );
            const opacity =
              (0.25 - dist * 0.35) *
              (1 + 0.3 * Math.sin(frame * 0.05 + ci * 0.4 + ri * 0.3));
            return (
              <circle
                key={`dot-${ci}-${ri}`}
                cx={x}
                cy={y}
                r={2}
                fill={colors.grid}
                opacity={Math.max(0, opacity)}
              />
            );
          })
        )}

        {/* Grid lines — very faint */}
        {Array.from({ length: cols + 1 }, (_, ci) => (
          <line
            key={`vl-${ci}`}
            x1={ci * cellW}
            y1={0}
            x2={ci * cellW}
            y2={height}
            stroke={colors.grid}
            strokeWidth={0.5}
            opacity={0.3}
          />
        ))}
        {Array.from({ length: rows + 1 }, (_, ri) => (
          <line
            key={`hl-${ri}`}
            x1={0}
            y1={ri * cellH}
            x2={width}
            y2={ri * cellH}
            stroke={colors.grid}
            strokeWidth={0.5}
            opacity={0.3}
          />
        ))}

        {/* Glow layers */}
        <rect width={width} height={height} fill="url(#centerGlow)" />
        <rect width={width} height={height} fill="url(#topGlow)" />

        {/* Floating particles */}
        {particles.map((p, i) => {
          const py =
            ((p.y + frame * p.speed * 0.6 + p.phase * 40) % (height + 40)) - 20;
          return (
            <g key={`p-${i}`}>
              {/* Glow halo */}
              <circle
                cx={p.x}
                cy={py}
                r={p.r * 3}
                fill={i % 2 === 0 ? colors.particle : colors.particle2}
                opacity={p.opacity * 0.12}
              />
              {/* Core dot */}
              <circle
                cx={p.x}
                cy={py}
                r={p.r}
                fill={i % 2 === 0 ? colors.particle : colors.particle2}
                opacity={p.opacity}
              />
            </g>
          );
        })}

        {/* Accent horizontal line scan */}
        <line
          x1={0}
          y1={((frame * 3) % (height * 1.2)) - 50}
          x2={width}
          y2={((frame * 3) % (height * 1.2)) - 50}
          stroke={colors.accent}
          strokeWidth={1.5}
          opacity={0.08}
        />
      </svg>
    </div>
  );
};

export default ParticleBackground;
