import React from "react";
import { useCurrentFrame, useVideoConfig, Easing, interpolate, spring } from "remotion";
import iconRegistry from "./iconRegistry";

const Node: React.FC<{ x: number; y: number; label: string; icon?: string; index: number }> = ({ x, y, label, icon, index }) => {
  const frame = useCurrentFrame();
  const appear = spring({ frame: Math.max(0, frame - index * 8), fps: 30, config: { damping: 8 } });
  const scale = interpolate(appear, [0, 1], [0.92, 1], { extrapolateRight: "clamp" });
  const opacity = interpolate(appear, [0, 1], [0, 1], { extrapolateRight: "clamp" });

  const IconComp = icon ? (iconRegistry as any)[icon] : null;

  return (
    <g transform={`translate(${x}, ${y}) scale(${scale})`} style={{ opacity }}>
      <rect x={-120} y={-40} width={240} height={80} rx={16} fill="#071033" stroke="#3b82f6" strokeWidth={2} />
      {IconComp && (
        <g transform={`translate(${-90}, -12)`}>
          <IconComp color="#60a5fa" size={28} />
        </g>
      )}
      <text x={-40} y={8} fill="#fff" fontSize={24} fontFamily="Arial" fontWeight={700}>{label}</text>
    </g>
  );
};

const Arrow: React.FC<{ x1: number; y1: number; x2: number; y2: number; index: number }> = ({ x1, y1, x2, y2, index }) => {
  const frame = useCurrentFrame();
  const t = Math.min(1, Math.max(0, (frame - index * 6) / 12));
  const strokeDash = `${interpolate(t, [0, 1], [100, 0])}`;
  return (
    <g>
      <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#60a5fa" strokeWidth={4} strokeLinecap="round" strokeDasharray={strokeDash} />
      <circle cx={interpolate(t, [0, 1], [x1, x2])} cy={interpolate(t, [0, 1], [y1, y2])} r={6} fill="#f97316" />
    </g>
  );
};

const RequestFlowDiagram: React.FC<{ data: any }> = ({ data }) => {
  const { width, height } = useVideoConfig();
  const nodes = data.nodes || [];
  const edges = data.edges || [];

  // Simple horizontal layout
  const step = Math.min(300, Math.floor((width - 200) / Math.max(1, nodes.length)));

  return (
    <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="xMidYMid meet">
      <rect width="100%" height="100%" fill="#071033" />
      <g transform={`translate(${width / 2 - (nodes.length - 1) * step / 2}, ${height / 2})`}>
        {edges.map((e: any, i: number) => {
          const fromIndex = nodes.findIndex((n: any) => n.id === e.from);
          const toIndex = nodes.findIndex((n: any) => n.id === e.to);
          const x1 = fromIndex * step;
          const x2 = toIndex * step;
          return <Arrow key={i} x1={x1 + 80} y1={0} x2={x2 - 80} y2={0} index={i} />;
        })}
        {nodes.map((n: any, i: number) => (
          <g key={n.id}>
            <Node x={i * step} y={0} label={n.label} icon={n.icon} index={i} />
          </g>
        ))}
      </g>
    </svg>
  );
};

export default RequestFlowDiagram;
