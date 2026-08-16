import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from "remotion";
import type { BaseDiagramProps } from "./DiagramRenderer";

type NodeData = { id: string; label: string; icon?: string };
type AnimEvent = { atMs: number; durationMs: number; type: string; atFrame?: number };

const TimelineDiagram: React.FC<BaseDiagramProps> = ({ data, sceneStartMs = 0, sceneDurationMs }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  const nodes: NodeData[] = data?.nodes ?? [];
  const timeline: AnimEvent[] = data?.animationTimeline ?? [];

  if (nodes.length === 0) {
    return (
      <svg width="100%" height="100%" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet">
        <rect width="1080" height="1920" fill="#020617" />
        <text x={540} y={960} fill="#94a3b8" fontSize={28} fontWeight={600} fontFamily="Arial" textAnchor="middle">No timeline data</text>
      </svg>
    );
  }

  const steps = nodes.map((n, i) => n.label || `Step ${i + 1}`);

  const enterEvent = timeline.find((e) => e.type === "enter");
  const revealAt = enterEvent
    ? Math.max(0, enterEvent.atMs / 1000 * fps - sceneStartMs / 1000 * fps)
    : 0;
  const progress = interpolate(frame, [revealAt, revealAt + 50], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  return (
    <svg width="100%" height="100%" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="timeline-bg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#020617" />
          <stop offset="100%" stopColor="#0f172a" />
        </linearGradient>
      </defs>
      <rect width="1080" height="1920" fill="url(#timeline-bg)" />

      <line x1={150} y1={980} x2={930} y2={980} stroke="#cbd5e1" strokeWidth={6} strokeDasharray="12 12" />
      <rect x={150} y={930} width={780 * progress} height={100} rx={12} fill="rgba(96,165,250,0.35)" style={{ filter: "drop-shadow(0 0 14px rgba(96,165,250,0.3))" }} />

      {steps.map((label, index) => {
        const x = 180 + index * Math.floor(660 / Math.max(1, steps.length - 1));
        const isActive = index <= progress * (steps.length - 1);
        return (
          <g key={nodes[index]?.id ?? index} transform={`translate(${x}, 900)`}>
            <circle r={24} fill={isActive ? "#34d399" : "#46556d"} style={isActive ? { filter: "drop-shadow(0 0 12px rgba(52,211,153,0.7))" } : undefined} />
            <text x={0} y={80} fill="#f8fafc" fontSize={22} fontWeight={600} fontFamily="Arial" textAnchor="middle">{label}</text>
          </g>
        );
      })}

      <text x={540} y={1060} fill="#94a3b8" fontSize={20} fontWeight={600} fontFamily="Arial" textAnchor="middle">TIMELINE</text>
    </svg>
  );
};

export default TimelineDiagram;
