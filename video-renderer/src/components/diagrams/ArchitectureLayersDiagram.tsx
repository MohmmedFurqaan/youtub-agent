import React from "react";
import { useCurrentFrame, interpolate, spring, Easing } from "remotion";

interface LayerData {
  layers?: string[];
  animationTimeline?: Array<{ atMs: number; durationMs: number; type: string }>;
}

const LayerCard: React.FC<{ x: number; y: number; width: number; height: number; label: string; color: string; index: number; delayFrames: number }> = ({ x, y, width, height, label, color, index, delayFrames }) => {
  const frame = useCurrentFrame();
  const appear = spring({ frame: Math.max(0, frame - delayFrames), fps: 30, config: { damping: 14, stiffness: 140, mass: 0.7 } });
  const scale = interpolate(appear, [0, 1], [0.88, 1], { extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const opacity = interpolate(appear, [0, 0.4, 1], [0, 0.6, 1], { extrapolateRight: "clamp" });

  return (
    <g transform={`translate(${x}, ${y}) scale(${scale})`} opacity={opacity}>
      <rect x={0} y={0} width={width} height={height} rx={24} fill={color} fillOpacity={0.15} stroke={color} strokeWidth={2} style={{ filter: `drop-shadow(0 0 14px ${color}33)` }} />
      <text x={width / 2} y={height / 2 + 8} fill="#f8fafc" fontSize={28} fontWeight={700} fontFamily="Arial" textAnchor="middle">{label}</text>
    </g>
  );
};

const ArchitectureLayersDiagram: React.FC<{ data: LayerData; sceneStartMs?: number; sceneDurationMs?: number }> = ({ data }) => {
  const frame = useCurrentFrame();

  const layers = data?.layers ?? ["Client", "Gateway", "API", "Storage"];
  const colors = ["#60a5fa", "#a78bfa", "#34d399", "#fbbf24"];

  const pulse = interpolate(frame, [0, 90], [0, 1], { extrapolateRight: "clamp" });

  return (
    <svg width="100%" height="100%" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="arch-bg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#020617" />
          <stop offset="100%" stopColor="#0f172a" />
        </linearGradient>
      </defs>
      <rect width="1080" height="1920" fill="url(#arch-bg)" />
      {layers.map((label, index) => {
        const width = 760 - index * 60;
        const height = 120;
        const x = 540 - width / 2;
        const y = 420 + index * 160;
        return <LayerCard key={label} x={x} y={y} width={width} height={height} label={label} color={colors[index % colors.length]} index={index} delayFrames={index * 12} />;
      })}
      <circle cx={540 + (pulse - 0.5) * 180} cy={1080} r={18} fill="#f87171" opacity={0.8} style={{ filter: "drop-shadow(0 0 16px rgba(248,113,113,0.7))" }} />
      <text x={540} y={1160} fill="#94a3b8" fontSize={20} fontWeight={600} fontFamily="Arial" textAnchor="middle">ARCHITECTURE LAYERS</text>
    </svg>
  );
};

export default ArchitectureLayersDiagram;
