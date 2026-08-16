import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from "remotion";

interface ComparisonData {
  nodes?: Array<{ id: string; label: string }>;
  left?: string;
  right?: string;
  animationTimeline?: Array<{ atMs: number; durationMs: number; type: string }>;
}

const CompareCard: React.FC<{ x: number; y: number; width: number; height: number; label: string; accent: string; index: number; delayFrames: number }> = ({ x, y, width, height, label, accent, index, delayFrames }) => {
  const frame = useCurrentFrame();
  const appear = spring({ frame: Math.max(0, frame - delayFrames), fps: 30, config: { damping: 12, stiffness: 140, mass: 0.7 } });
  const scale = interpolate(appear, [0, 1], [0.85, 1], { extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const opacity = interpolate(appear, [0, 0.5, 1], [0, 0.5, 1], { extrapolateRight: "clamp" });

  return (
    <g transform={`translate(${x}, ${y}) scale(${scale})`} opacity={opacity}>
      <rect x={0} y={0} width={width} height={height} rx={28} fill="rgba(15,23,42,0.85)" stroke={accent} strokeWidth={2.5} style={{ filter: `drop-shadow(0 0 18px ${accent}44)` }} />
      <text x={width / 2} y={height / 2 - 24} fill="#f8fafc" fontSize={26} fontWeight={700} fontFamily="Arial" textAnchor="middle">{label}</text>
      <line x1={0} y1={height / 2 + 18} x2={width} y2={height / 2 + 18} stroke={accent} strokeWidth={4} strokeDasharray="10 10" />
    </g>
  );
};

const ComparisonDiagram: React.FC<{ data: ComparisonData; sceneStartMs?: number; sceneDurationMs?: number }> = ({ data, sceneStartMs = 0, sceneDurationMs = 5000 }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  const nodes = data?.nodes ?? [
    { id: "a", label: "PUT" },
    { id: "b", label: "PATCH" },
  ];
  const leftLabel = data?.left ?? nodes[0]?.label ?? "Option A";
  const rightLabel = data?.right ?? nodes[1]?.label ?? "Option B";

  const timeline = data?.animationTimeline ?? [];
  const revealEvent = timeline.find((e) => e.type === "comparison-reveal");

  const revealAt = revealEvent ? Math.min(revealEvent.atMs / 1000 * fps, frame) : 15;
  const barProgress = interpolate(frame, [revealAt, revealAt + 45], [0.15, 1], { extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });

  return (
    <svg width="100%" height="100%" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="comp-bg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#020617" />
          <stop offset="100%" stopColor="#0f172a" />
        </linearGradient>
      </defs>
      <rect width="1080" height="1920" fill="url(#comp-bg)" />
      <CompareCard x={160} y={620} width={300} height={360} label={leftLabel} accent="#60a5fa" index={0} delayFrames={0} />
      <CompareCard x={620} y={620} width={300} height={360} label={rightLabel} accent="#34d399" index={1} delayFrames={10} />
      <rect x={315} y={1030} width={450} height={18} rx={9} fill="rgba(148,163,184,0.25)" />
      <rect x={315} y={1030} width={450 * barProgress} height={18} rx={9} fill="#f59e0b" style={{ filter: "drop-shadow(0 0 10px rgba(245,158,11,0.7))" }} />
      <text x={540} y={1100} fill="#94a3b8" fontSize={20} fontWeight={600} fontFamily="Arial" textAnchor="middle">COMPARISON</text>
    </svg>
  );
};

export default ComparisonDiagram;
