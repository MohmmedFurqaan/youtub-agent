import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from "remotion";
import type { BaseDiagramProps } from "./DiagramRenderer";

type NodeData = { id: string; label: string; icon?: string };
type EdgeData = { from: string; to: string; label?: string };
type AnimEvent = { atMs: number; durationMs: number; type: string; target?: string };

const LAYER_COLORS = ["#60a5fa", "#a78bfa", "#34d399", "#fbbf24", "#f97316", "#ec4899"];

const LayerCard: React.FC<{
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
  color: string;
  index: number;
  delayFrames: number;
}> = ({ x, y, width, height, label, color, index, delayFrames }) => {
  const frame = useCurrentFrame();
  const appear = spring({ frame: Math.max(0, frame - delayFrames), fps: 30, config: { damping: 14, stiffness: 140, mass: 0.7 } });
  const scale = interpolate(appear, [0, 1], [0.88, 1], { extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const opacity = interpolate(appear, [0, 0.4, 1], [0, 0.6, 1], { extrapolateRight: "clamp" });

  return (
    <g transform={`translate(${x}, ${y}) scale(${scale})`} opacity={opacity}>
      <rect x={0} y={0} width={width} height={height} rx={24} fill="rgba(15,23,42,0.85)" stroke={color} strokeWidth={2.5} style={{ filter: `drop-shadow(0 0 18px ${color}44)` }} />
      <text x={width / 2} y={height / 2 + 8} fill="#f8fafc" fontSize={28} fontWeight={700} fontFamily="Arial" textAnchor="middle">{label}</text>
    </g>
  );
};

const ArchitectureLayersDiagram: React.FC<BaseDiagramProps> = ({ data, sceneStartMs = 0, sceneDurationMs }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  const nodes: NodeData[] = data?.nodes ?? [];
  const edges: EdgeData[] = data?.edges ?? [];
  const timeline: AnimEvent[] = data?.animationTimeline ?? [];
  const highlightEdge: number | undefined = data?.highlightEdge;

  if (nodes.length === 0) {
    return (
      <svg width="100%" height="100%" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet">
        <rect width="1080" height="1920" fill="#020617" />
        <text x={540} y={960} fill="#94a3b8" fontSize={28} fontWeight={600} fontFamily="Arial" textAnchor="middle">No layer data</text>
      </svg>
    );
  }

  const layers = nodes.map((n, i) => n.label || `Layer ${i + 1}`);

  const currentMs = (frame / fps) * 1000 - sceneStartMs;
  const enterEvents = timeline.filter((e) => e.type === "enter" && e.target);
  const revealedCount = enterEvents.length > 0
    ? enterEvents.filter((e) => currentMs >= e.atMs + e.durationMs).length
    : layers.length;

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
        const layerWidth = 760 - index * (760 / Math.max(1, layers.length - 1)) * 0.08;
        const layerHeight = 120;
        const x = 540 - layerWidth / 2;
        const y = 420 + index * 160;
        const color = LAYER_COLORS[index % LAYER_COLORS.length];
        const delayFrames = index * 12;

        if (index >= revealedCount) return null;

        return (
          <LayerCard
            key={nodes[index]?.id ?? index}
            x={x}
            y={y}
            width={layerWidth}
            height={layerHeight}
            label={label}
            color={color}
            index={index}
            delayFrames={delayFrames}
          />
        );
      })}

      {/* Active edge indicator */}
      {highlightEdge !== undefined && highlightEdge < edges.length && (
        <g>
          {(() => {
            const edge = edges[highlightEdge];
            const fromNode = nodes.find((n) => n.id === edge.from);
            const toNode = nodes.find((n) => n.id === edge.to);
            if (!fromNode || !toNode) return null;
            const fromIdx = nodes.indexOf(fromNode);
            const toIdx = nodes.indexOf(toNode);
            const x1 = 540;
            const y1 = 420 + fromIdx * 160 + 60;
            const x2 = 540;
            const y2 = 420 + toIdx * 160 + 60;
            return (
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#fbbf24" strokeWidth={4} strokeDasharray="8 6" opacity={0.7} />
            );
          })()}
        </g>
      )}

      <text x={540} y={1080} fill="#94a3b8" fontSize={20} fontWeight={600} fontFamily="Arial" textAnchor="middle">
        {nodes.length > 0 ? nodes[0].label : "ARCHITECTURE"}
      </text>
    </svg>
  );
};

export default ArchitectureLayersDiagram;
