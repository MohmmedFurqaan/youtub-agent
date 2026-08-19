import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from "remotion";
import iconRegistry from "./iconRegistry";
import type { BaseDiagramProps } from "./DiagramRenderer";

type NodeData = { id: string; label: string; icon?: string };
type EdgeData = { from: string; to: string; label?: string };
type AnimEvent = { atMs: number; durationMs: number; type: string; from?: string; to?: string; text?: string; target?: string };

const Node: React.FC<{ x: number; y: number; label: string; icon?: string; index: number; delayFrames: number; active?: boolean }> = ({ x, y, label, icon, index, delayFrames, active = false }) => {
  const frame = useCurrentFrame();
  const appear = spring({ frame: Math.max(0, frame - delayFrames), fps: 30, config: { damping: 12, stiffness: 160, mass: 0.7 } });
  const scale = interpolate(appear, [0, 1], [0.8, 1], { extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const opacity = interpolate(appear, [0, 0.4, 1], [0, 0.8, 1], { extrapolateRight: "clamp" });
  const IconComp = icon ? (iconRegistry as any)[icon] : null;

  return (
    <g transform={`translate(${x}, ${y}) scale(${scale})`} opacity={opacity}>
      <rect x={-110} y={-42} width={220} height={84} rx={18} fill="rgba(15,23,42,0.9)" stroke={active ? "#fbbf24" : "#67e8f9"} strokeWidth={active ? 4 : 2.5} style={{ filter: `drop-shadow(0 0 ${active ? 20 : 16}px ${active ? "rgba(251,191,36,0.6)" : "rgba(103,232,249,0.35)"})` }} />
      {IconComp && (
        <g transform={`translate(${-85}, -16)`}>
          <IconComp color={active ? "#fbbf24" : "#67e8f9"} size={28} />
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

const SequenceDiagram: React.FC<BaseDiagramProps> = ({ data, sceneStartMs = 0, sceneDurationMs }) => {
  const { width, height } = useVideoConfig();
  const frame = useCurrentFrame();

  const nodes: NodeData[] = data?.nodes ?? [];
  const edges: EdgeData[] = data?.edges ?? [];
  const timeline: AnimEvent[] = data?.animationTimeline ?? [];

  // Highlight active nodes based on animation timeline
  const currentMs = (frame / useVideoConfig().fps) * 1000 - sceneStartMs;
  const activeNodeIds = new Set<string>();
  const activePackets: AnimEvent[] = [];

  timeline.forEach((event) => {
    const isActive = currentMs >= event.atMs && currentMs <= event.atMs + event.durationMs;
    if (event.type === "highlight-node" && isActive && event.target) {
      activeNodeIds.add(event.target);
    }
    if (event.type === "move-packet" && isActive) {
      activePackets.push(event);
    }
  });

  if (nodes.length === 0) {
    return (
      <svg width="100%" height="100%" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet">
        <rect width="1080" height="1920" fill="#020617" />
        <text x={540} y={960} fill="#94a3b8" fontSize={28} fontWeight={600} fontFamily="Arial" textAnchor="middle">No sequence data</text>
      </svg>
    );
  }

  // Compute node positions vertically centered
  const nodeCount = Math.max(1, nodes.length);
  const nodeSpacingY = Math.min(280, (height - 400) / Math.max(1, nodeCount - 1));
  const totalHeight = (nodeCount - 1) * nodeSpacingY;
  const startY = height / 2 - totalHeight / 2 - 50;

  const nodePositions = nodes.map((_, i) => ({
    x: i === 0 ? width / 2 - 220 :
       i === nodeCount - 1 ? width / 2 + 220 :
       width / 2,
    y: startY + i * nodeSpacingY,
  }));

  // Map node id to index for quick lookup
  const nodeIndexMap = new Map<string, number>();
  nodes.forEach((n, i) => nodeIndexMap.set(n.id, i));

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
        {nodes.map((node, i) => {
          const pos = nodePositions[i];
          return (
            <Node
              key={node.id}
              x={pos.x}
              y={pos.y}
              label={node.label || `Node ${i + 1}`}
              icon={node.icon}
              index={i}
              delayFrames={i * 12}
              active={activeNodeIds.has(node.id)}
            />
          );
        })}

        {/* Trails between connected nodes */}
        {edges.map((edge, i) => {
          const fromIdx = nodeIndexMap.get(edge.from);
          const toIdx = nodeIndexMap.get(edge.to);
          if (fromIdx === undefined || toIdx === undefined) return null;
          const fromPos = nodePositions[fromIdx];
          const toPos = nodePositions[toIdx];
          return (
            <Trail
              key={`trail-${edge.from}-${edge.to}-${i}`}
              startX={fromPos.x + 110}
              startY={fromPos.y + 21}
              endX={toPos.x - 110}
              endY={toPos.y + 21}
              index={i}
              delayFrames={Math.min(fromIdx, toIdx) * 12 + 18}
            />
          );
        })}

        {/* Moving packets from animation timeline */}
        {activePackets.map((event, i) => {
          const fromIdx = nodeIndexMap.get(event.from ?? "");
          const toIdx = nodeIndexMap.get(event.to ?? "");
          if (fromIdx === undefined || toIdx === undefined) return null;
          const fromPos = nodePositions[fromIdx];
          const toPos = nodePositions[toIdx];
          const progress = Math.min(1, Math.max(0, (currentMs - event.atMs) / event.durationMs));
          const startOffsetX = fromPos.x < toPos.x ? 110 : (fromPos.x > toPos.x ? -110 : 0);
          const endOffsetX = fromPos.x < toPos.x ? -110 : (fromPos.x > toPos.x ? 110 : 0);
          const packetX = interpolate(progress, [0, 1], [fromPos.x + startOffsetX, toPos.x + endOffsetX], { extrapolateRight: "clamp" });
          const packetY = interpolate(progress, [0, 1], [fromPos.y + 21, toPos.y + 21], { extrapolateRight: "clamp" });
          const size = 13 + 7 * Math.sin(progress * Math.PI);

          return (
            <g key={`packet-${i}`} transform={`translate(${packetX}, ${packetY})`}>
              <circle r={size * 1.8} fill="rgba(245,158,11,0.12)" />
              <circle r={size} fill="#f59e0b" style={{ filter: "drop-shadow(0 4px 14px rgba(245,158,11,0.8))" }} />
              <circle r={size * 0.35} fill="#fff7ed" />
              {event.text && (
                <text x={size + 12} y={6} fill="#ffffff" fontSize={18} fontFamily="Arial" fontWeight={700}>
                  {event.text}
                </text>
              )}
            </g>
          );
        })}
      </g>
      <text x={540} y={1100} fill="#94a3b8" fontSize={20} fontWeight={600} fontFamily="Arial" textAnchor="middle">SEQUENCE</text>
    </svg>
  );
};

export default SequenceDiagram;
