import React from "react";
import { useCurrentFrame, useVideoConfig, Easing, interpolate, spring } from "remotion";
import iconRegistry from "./iconRegistry";

const Node: React.FC<{ x: number; y: number; label: string; icon?: string; index: number; isActive?: boolean }> = ({ x, y, label, icon, index, isActive = false }) => {
  const frame = useCurrentFrame();
  const appear = spring({ frame: Math.max(0, frame - index * 7), fps: 30, config: { damping: 18 } });
  const scale = interpolate(appear, [0, 1], [0.92, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
    output: "perceptual-scale",
  });
  const opacity = interpolate(appear, [0, 1], [0, 1], { extrapolateRight: "clamp" });
  const glow = interpolate(appear, [0.4, 1], [0.2, 0.9], { extrapolateRight: "clamp" });
  const activePulse = isActive ? 1 + 0.03 * Math.sin(frame / 6) : 1;

  const IconComp = icon ? (iconRegistry as any)[icon] : null;

  return (
    <g transform={`translate(${x}, ${y}) scale(${scale * activePulse})`} style={{ opacity }}>
      <rect x={-126} y={-46} width={252} height={92} rx={20} fill="rgba(15,23,42,0.92)" stroke={isActive ? "rgba(250,204,21,0.95)" : "rgba(96,165,250,0.9)"} strokeWidth={isActive ? 3.5 : 2.5} style={{ filter: `drop-shadow(0 0 ${18 * (glow + (isActive ? 0.6 : 0))}px rgba(96,165,250,0.8))` }} />
      {IconComp && (
        <g transform={`translate(${-94}, -18)`}>
          <IconComp color="#7dd3fc" size={30} />
        </g>
      )}
      <text x={-34} y={10} fill="#f8fafc" fontSize={25} fontFamily="Arial" fontWeight={700}>{label}</text>
    </g>
  );
};

const Arrow: React.FC<{ x1: number; y1: number; x2: number; y2: number; index: number; isActive?: boolean }> = ({ x1, y1, x2, y2, index, isActive = false }) => {
  const frame = useCurrentFrame();
  const t = Math.min(1, Math.max(0, (frame - index * 6) / 14));
  const pulse = interpolate(t, [0, 1], [0.2, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const x = interpolate(t, [0, 1], [x1, x2], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  const y = interpolate(t, [0, 1], [y1, y2], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  return (
    <g>
      <line
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke={isActive ? "rgba(250,204,21,0.95)" : "rgba(125,211,252,0.7)"}
        strokeWidth={isActive ? 6 : 4}
        strokeLinecap="round"
        strokeDasharray={isActive ? "10 8" : "16 12"}
        style={{ filter: isActive ? "drop-shadow(0 0 16px rgba(250,204,21,0.8))" : undefined }}
      />
      <circle cx={x} cy={y} r={isActive ? 10 * pulse : 8 * pulse} fill={isActive ? "#fbbf24" : "#f8fafc"} opacity={0.95} />
    </g>
  );
};

const PointerClick: React.FC<{ x: number; y: number }> = ({ x, y }) => {
  const frame = useCurrentFrame();
  const pulse = interpolate((frame % 30) / 30, [0, 0.55, 1], [0.4, 1, 0.8], {
    extrapolateRight: "clamp",
  });

  return (
    <g transform={`translate(${x}, ${y})`}>
      <circle r={24 + pulse * 10} fill="rgba(251,191,36,0.18)" />
      <circle r={10 + pulse * 6} fill="rgba(251,191,36,0.6)" />
      <path d="M-10,18 L6,0 L18,10 L8,20 L18,34 L4,30 L-2,40 Z" fill="#f8fafc" opacity={0.9} transform="rotate(-24)" />
    </g>
  );
};

const RequestFlowDiagram: React.FC<{ data: any; sceneStartMs?: number; sceneDurationMs?: number }> = ({ data, sceneStartMs, sceneDurationMs }) => {
  const { width, height, fps } = useVideoConfig();
  const nodes = data?.nodes ?? [];
  const edges = data?.edges ?? [];
  const highlightEdge = data?.highlightEdge ?? 0;
  const step = Math.min(240, Math.floor((width - 240) / Math.max(1, nodes.length)));
  const frame = useCurrentFrame();
  const currentMs = (frame / fps) * 1000;
  const timeline = data?.animationTimeline ?? [];

  // Helpers: determine if a node/edge is active by timeline
  const nodeIsActive = (nodeId: string) => {
    for (const ev of timeline) {
      if ((ev.type === "highlight-node" || ev.type === "pulse") && ev.target === nodeId) {
        if (currentMs >= ev.atMs && currentMs <= ev.atMs + ev.durationMs) return true;
      }
    }
    return false;
  };

  const edgeIsActive = (fromId: string, toId: string) => {
    for (const ev of timeline) {
      if (ev.type === "highlight-edge" && ev.from === fromId && ev.to === toId) {
        if (currentMs >= ev.atMs && currentMs <= ev.atMs + ev.durationMs) return true;
      }
    }
    return false;
  };

  const movingPackets = timeline.filter((ev: any) => ev.type === "move-packet");

  return (
    <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="xMidYMid meet">
      <defs>
        <radialGradient id="diagramGlow" cx="50%" cy="35%" r="70%">
          <stop offset="0%" stopColor="rgba(59,130,246,0.18)" />
          <stop offset="100%" stopColor="rgba(15,23,42,0)" />
        </radialGradient>
      </defs>
      <rect width={width} height={height} fill="#020617" />
      <rect width={width} height={height} fill="url(#diagramGlow)" />

      <g transform={`translate(${width / 2 - (nodes.length - 1) * step / 2}, ${height / 2 + 40})`}>
        {edges.map((e: any, i: number) => {
          const fromIndex = nodes.findIndex((n: any) => n.id === e.from);
          const toIndex = nodes.findIndex((n: any) => n.id === e.to);
          if (fromIndex === -1 || toIndex === -1) return null;
          const x1 = fromIndex * step;
          const x2 = toIndex * step;
          const isActiveEdge = edgeIsActive(e.from, e.to) || i === highlightEdge;
          return <Arrow key={i} x1={x1 + 80} y1={0} x2={x2 - 80} y2={0} index={i} isActive={isActiveEdge} />;
        })}

        {nodes.map((n: any, i: number) => (
          <g key={n.id}>
            <Node x={i * step} y={0} label={n.label} icon={n.icon} index={i} isActive={nodeIsActive(n.id)} />
          </g>
        ))}

        <PointerClick x={-110} y={-92} />

        {/* Moving packets: render above edges */}
        {movingPackets.map((ev: any, idx: number) => {
          const fromIndex = nodes.findIndex((n: any) => n.id === ev.from);
          const toIndex = nodes.findIndex((n: any) => n.id === ev.to);
          if (fromIndex === -1 || toIndex === -1) return null;
          const startX = fromIndex * step + 80;
          const endX = toIndex * step - 80;
          const progress = Math.min(1, Math.max(0, (currentMs - ev.atMs) / ev.durationMs));
          if (progress <= 0 || progress >= 1) return null;
          const x = startX + (endX - startX) * progress;
          const y = 0;
          const size = 14 + 6 * Math.sin(progress * Math.PI);
          return (
            <g key={`pkt-${idx}`} transform={`translate(${x}, ${y - 14})`}>
              <circle cx={0} cy={0} r={size} fill="rgba(245,158,11,0.95)" style={{ filter: "drop-shadow(0 4px 12px rgba(245,158,11,0.6))" }} />
              {ev.text && (
                <text x={size + 6} y={6} fill="#fff" fontSize={18} fontFamily="Arial" fontWeight={700}>{ev.text}</text>
              )}
            </g>
          );
        })}
      </g>
    </svg>
  );
};

export default RequestFlowDiagram;
