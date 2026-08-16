import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from "remotion";

interface ConceptCardData {
  title?: string;
  subtitle?: string;
  animationTimeline?: Array<{ atMs: number; durationMs: number; type: string }>;
}

const ConceptCardDiagram: React.FC<{ data: ConceptCardData; sceneStartMs?: number; sceneDurationMs?: number }> = ({ data, sceneStartMs = 0, sceneDurationMs = 5000 }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  const focus = spring({ frame, fps: 30, config: { damping: 12, stiffness: 160, mass: 0.7 } });
  const scale = interpolate(focus, [0, 1], [0.94, 1], { extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const title = data?.title ?? "Choose the right method";
  const subtitle = data?.subtitle ?? "Match intent to action";

  const timeline = data?.animationTimeline ?? [];
  const revealAt = timeline.find((e) => e.type === "enter")?.atMs ?? 0;
  const revealFrame = Math.max(0, Math.min(revealAt / 1000 * fps, frame));
  const barProgress = interpolate(revealFrame, [0, 60], [0.2, 1], { extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });

  return (
    <svg width="100%" height="100%" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="concept-bg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#020617" />
          <stop offset="100%" stopColor="#0f172a" />
        </linearGradient>
      </defs>
      <rect width="1080" height="1920" fill="url(#concept-bg)" />
      <g transform={`translate(540 960) scale(${scale})`}>
        <rect x={-320} y={-220} width={640} height={440} rx={36} fill="rgba(15,23,42,0.9)" stroke="#a78bfa" strokeWidth={3} style={{ filter: "drop-shadow(0 0 24px rgba(167,139,250,0.35))" }} />
        <circle cx={-120} cy={-60} r={72} fill="rgba(167,139,250,0.2)" />
        <text x={0} y={-20} fill="#f8fafc" fontSize={42} fontWeight={800} fontFamily="Arial" textAnchor="middle">{title}</text>
        <text x={0} y={80} fill="#cbd5e1" fontSize={26} fontWeight={500} fontFamily="Arial" textAnchor="middle">{subtitle}</text>
        <rect x={-170} y={150} width={340} height={12} rx={8} fill="rgba(148,163,184,0.3)" />
        <rect x={-170} y={150} width={340 * barProgress} height={12} rx={8} fill="#fbbf24" style={{ filter: "drop-shadow(0 0 8px rgba(251,191,36,0.6))" }} />
      </g>
      <text x={540} y={1280} fill="#94a3b8" fontSize={20} fontWeight={600} fontFamily="Arial" textAnchor="middle">CONCEPT CARD</text>
    </svg>
  );
};

export default ConceptCardDiagram;
