import React from "react";
import { useCurrentFrame, interpolate, spring } from "remotion";

const CompareCard: React.FC<{ x: number; y: number; width: number; height: number; label: string; accent: string; index: number }> = ({ x, y, width, height, label, accent, index }) => {
  const frame = useCurrentFrame();
  const appear = spring({ frame: Math.max(0, frame - index * 12), fps: 30, config: { damping: 10 } });
  const scale = interpolate(appear, [0, 1], [0.9, 1], { extrapolateRight: "clamp" });

  return (
    <g transform={`translate(${x}, ${y}) scale(${scale})`}>
      <rect x={0} y={0} width={width} height={height} rx={28} fill="rgba(15,23,42,0.8)" stroke={accent} strokeWidth={2} />
      <text x={width / 2} y={height / 2 - 24} fill="#f8fafc" fontSize={26} fontWeight={700} fontFamily="Arial" textAnchor="middle">{label}</text>
      <line x1={0} y1={height / 2 + 18} x2={width} y2={height / 2 + 18} stroke={accent} strokeWidth={4} strokeDasharray="10 10" />
    </g>
  );
};

const ComparisonDiagram: React.FC<{ data: any }> = ({ data }) => {
  const nodes = data?.nodes ?? [
    { id: "a", label: "PUT" },
    { id: "b", label: "PATCH" },
  ];
  const frame = useCurrentFrame();
  const bar = interpolate(frame, [0, 90], [0.2, 1], { extrapolateRight: "clamp" });

  return (
    <svg width="100%" height="100%" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet">
      <rect width="1080" height="1920" fill="#020617" />
      <CompareCard x={160} y={620} width={300} height={360} label={nodes[0]?.label ?? "PUT"} accent="#60a5fa" index={0} />
      <CompareCard x={620} y={620} width={300} height={360} label={nodes[1]?.label ?? "PATCH"} accent="#34d399" index={1} />
      <rect x={315} y={1030} width={450} height={18} rx={9} fill="rgba(148,163,184,0.25)" />
      <rect x={315} y={1030} width={450 * bar} height={18} rx={9} fill="#f59e0b" />
    </svg>
  );
};

export default ComparisonDiagram;
