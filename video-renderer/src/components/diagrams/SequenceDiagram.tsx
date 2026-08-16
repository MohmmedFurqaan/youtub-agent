import React from "react";
import { useCurrentFrame, interpolate, spring, Easing } from "remotion";
import iconRegistry from "./iconRegistry";

interface SequenceData {
  nodes?: Array<{ id: string; label: string; icon?: string }>;
  edges?: Array<{ from: string; to: string; label?: string }>;
  animationTimeline?: Array<{ atMs: number; durationMs: number; type: string; text?: string }>;
}

const Node: React.FC<{ x: number; y: number; label: string; icon?: string; index: number; delayFrames: number }> = ({ x, y, label, icon, index, delayFrames }) => {
  const frame = useCurrentFrame();
  const appear = spring({ frame: Math.max(0, frame - delayFrames), fps: 30, config: { damping: 12, stiffness: 160, mass: 0.7 } });
  const scale = interpolate(appear, [0, 1], [0.8, 1], { extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const opacity = interpolate(appear, [0, 0.4, 1], [0, 0.8, 1], { extrapolateRight: "clamp" });
  const IconComp = icon ? (iconRegistry as any)[icon] : null;

  return (
    <g transform={`translate(${x}, ${y}) scale(${scale})`} opacity={opacity}>
      <rect x={-110} y={-42} width={220} height={84} rx={18} fill="rgba(15,23,42,0.9)" stroke="#67e8f9" strokeWidth={2.5} style={{ filter: "drop-shadow(0 0 16px rgba(103,232,249,0.35))" }} />
      {IconComp && (
        <g transform={`translate(${-85}, -16)`}>
          <IconComp color="#67e8f9" size={28} />
        </g>
      )}
      <text x={-25} y={10} fill="#f8fafc" fontSize={26} fontWeight={700} fontFamily="Arial">{label}</text>
    </g>
  );
};

const Trail: React.FC<{ startX: number; startY: number; endX: number; endY: number; index: number; delayFrames: number }> = ({ startX, startY, endX, endY, index, delayFrames }) => {
  const frame = useCurrentFrame();
  const progress = Math.min(1, Math.max(0, (frame - delayFrames) / 22));
  const x = interpolate(progress, [0, 1], [startX, endX], { extrapolateRight: "clamp" });
  const y = interpolate(progress, [0, 1], [startY, endY], { extrapolateRight: "clamp" });

  return (
    <g>
      <line x1={startX} y1={startY} x2={endX} y2={endY} stroke="rgba(103,232,249,0.7)" strokeWidth={4} strokeDasharray="14 14" />
      <circle cx={x} cy={y} r={7} fill="#f59e0b" opacity={0.95} style={{ filter: "drop-shadow(0 0 10px rgba(245,158,11,0.8))" }} />
    </g>
  );
};

const SequenceDiagram: React.FC<{ data: SequenceData; sceneStartMs?: number; sceneDurationMs?: number }> = ({ data }) => {

  const nodes = data?.nodes ?? [
    { id: "a", label: "Client", icon: "smartphone" },
    { id: "b", label: "API", icon: "server" },
    { id: "c", label: "Result", icon: "database" },
  ];

  return (
    <svg width="100%" height="100%" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="seq-bg" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stopColor="#020617" />
          <stop offset="100%" stopColor="#0f172a" />
        </linearGradient>
      </defs>
      <rect width="1080" height="1920" fill="url(#seq-bg)" />
      <g transform="translate(0, 120)">
        <Node x={230} y={760} label={nodes[0]?.label ?? "Client"} icon={nodes[0]?.icon} index={0} delayFrames={0} />
        <Node x={540} y={760} label={nodes[1]?.label ?? "API"} icon={nodes[1]?.icon} index={1} delayFrames={12} />
        <Node x={850} y={760} label={nodes[2]?.label ?? "Result"} icon={nodes[2]?.icon} index={2} delayFrames={24} />
        <Trail startX={300} startY={760} endX={430} endY={760} index={0} delayFrames={18} />
        <Trail startX={610} startY={760} endX={740} endY={760} index={1} delayFrames={36} />
      </g>
      <text x={540} y={1100} fill="#94a3b8" fontSize={20} fontWeight={600} fontFamily="Arial" textAnchor="middle">SEQUENCE</text>
    </svg>
  );
};

export default SequenceDiagram;
