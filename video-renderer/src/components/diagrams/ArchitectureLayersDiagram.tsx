import React from "react";
import { useCurrentFrame, interpolate, spring } from "remotion";

const LayerCard: React.FC<{ x: number; y: number; width: number; height: number; label: string; color: string; index: number }> = ({ x, y, width, height, label, color, index }) => {
  const frame = useCurrentFrame();
  const appear = spring({ frame: Math.max(0, frame - index * 10), fps: 30, config: { damping: 10 } });
  const scale = interpolate(appear, [0, 1], [0.88, 1], { extrapolateRight: "clamp" });
  const opacity = interpolate(appear, [0, 1], [0, 1], { extrapolateRight: "clamp" });

  return (
    <g transform={`translate(${x}, ${y}) scale(${scale})`} opacity={opacity}>
      <rect x={0} y={0} width={width} height={height} rx={24} fill={color} fillOpacity={0.18} stroke={color} strokeWidth={2} />
      <text x={width / 2} y={height / 2 + 8} fill="#f8fafc" fontSize={28} fontWeight={700} fontFamily="Arial" textAnchor="middle">{label}</text>
    </g>
  );
};

const ArchitectureLayersDiagram: React.FC<{ data: any }> = ({ data }) => {
  const frame = useCurrentFrame();
  const pulse = interpolate(frame, [0, 90], [0, 1], { extrapolateRight: "clamp" });
  // Prefer explicit `layers` array, but fall back to `nodes` labels when provided
  const layers = data?.layers ?? (data?.nodes ? data.nodes.map((n: any) => n.label) : ["Client", "Gateway", "API", "Storage"]);
  const colors = ["#60a5fa", "#a78bfa", "#34d399", "#fbbf24"];

  return (
    <svg width="100%" height="100%" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet">
      <rect width="1080" height="1920" fill="#020617" />
      {layers.map((label: string, index: number) => {
        const width = 760 - index * 60;
        const height = 120;
        const x = 540 - width / 2;
        const y = 420 + index * 160;
        return <LayerCard key={label} x={x} y={y} width={width} height={height} label={label} color={colors[index % colors.length]} index={index} />;
      })}
      <circle cx={540 + (pulse - 0.5) * 180} cy={1080} r={18} fill="#f87171" opacity={0.8} />
    </svg>
  );
};

export default ArchitectureLayersDiagram;
