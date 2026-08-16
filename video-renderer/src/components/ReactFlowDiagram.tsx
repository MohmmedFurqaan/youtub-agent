/**
 * ReactFlowDiagram.tsx
 *
 * Renders animated node-edge diagrams using ReactFlow inside a Remotion scene.
 *
 * Because ReactFlow uses browser interactions we disable all pointer events and
 * use Remotion's useCurrentFrame() to drive the animation state instead of
 * ReactFlow's built-in controls.
 *
 * Node positions are laid out vertically (portrait 9:16) so nodes stack
 * naturally. DiceBear avatars are used as node icons via the HTTP API.
 */

import React, { useMemo } from "react";
import ReactFlow, {
  Node,
  Edge,
  Background,
  BackgroundVariant,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import { useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";

interface NodeData {
  id: string;
  label: string;
  icon?: string;
}

interface EdgeData {
  from: string;
  to: string;
  label?: string;
}

interface AnimEvent {
  atMs: number;
  durationMs: number;
  type: string;
  from?: string;
  to?: string;
  target?: string;
  text?: string;
}

interface DiagramData {
  nodes?: NodeData[];
  edges?: EdgeData[];
  animationTimeline?: AnimEvent[];
}

interface Props {
  data: DiagramData;
  sceneStartMs?: number;
  sceneDurationMs?: number;
}

// Icon → DiceBear style mapping
const ICON_TO_STYLE: Record<string, string> = {
  smartphone: "adventurer",
  monitor: "bottts-neutral",
  server: "bottts",
  database: "identicon",
  cloud: "shapes",
  user: "adventurer-neutral",
  lock: "rings",
  shield: "rings",
  globe: "shapes",
  code: "bottts-neutral",
  gitBranch: "bottts-neutral",
  message: "fun-emoji",
  zap: "thumbs",
  activity: "thumbs",
};

// Role-based node accent colors
const NODE_COLORS = ["#3b82f6", "#8b5cf6", "#06b6d4", "#34d399", "#f59e0b"];

function buildAvatarUrl(icon: string, seed: string, color: string): string {
  const style = ICON_TO_STYLE[icon] ?? "bottts-neutral";
  const bg = color.replace("#", "");
  return `https://api.dicebear.com/10.x/${style}/svg?seed=${encodeURIComponent(seed)}&size=80&backgroundColor=${bg}&backgroundType=solid&radius=20`;
}

// Animated single node card
const AnimatedNode: React.FC<{
  data: { label: string; icon?: string; color: string; index: number; active: boolean; seed: string };
}> = ({ data }) => {
  const frame = useCurrentFrame();
  const appear = spring({ frame: Math.max(0, frame - data.index * 8), fps: 30, config: { damping: 14, stiffness: 130, mass: 0.7 } });
  const scale = interpolate(appear, [0, 1], [0.7, 1], { extrapolateRight: "clamp" });
  const opacity = interpolate(appear, [0, 1], [0, 1], { extrapolateRight: "clamp" });
  const pulse = data.active ? 1 + 0.04 * Math.sin(frame * 0.35) : 1;

  const avatarUrl = buildAvatarUrl(data.icon ?? "server", data.seed, data.color);

  return (
    <div
      style={{
        transform: `scale(${scale * pulse})`,
        opacity,
        display: "flex",
        alignItems: "center",
        gap: 14,
        background: "rgba(15,23,42,0.92)",
        border: `2.5px solid ${data.active ? "#fbbf24" : data.color}`,
        borderRadius: 20,
        padding: "14px 20px",
        minWidth: 220,
        boxShadow: data.active
          ? `0 0 30px rgba(251,191,36,0.6), 0 8px 32px rgba(0,0,0,0.5)`
          : `0 0 16px ${data.color}44, 0 8px 32px rgba(0,0,0,0.4)`,
      }}
    >
      <img src={avatarUrl} width={52} height={52} style={{ borderRadius: 12 }} alt="" />
      <span
        style={{
          fontFamily: "Arial",
          fontWeight: 700,
          fontSize: 22,
          color: data.active ? "#fbbf24" : "#f8fafc",
          textShadow: data.active ? "0 0 12px rgba(251,191,36,0.8)" : "none",
          letterSpacing: 0.5,
        }}
      >
        {data.label}
      </span>
    </div>
  );
};

const nodeTypes = { animated: AnimatedNode };

export const ReactFlowDiagram: React.FC<Props> = ({ data, sceneDurationMs = 5000 }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const currentMs = (frame / fps) * 1000;
  const timeline = data?.animationTimeline ?? [];

  const rawNodes = data?.nodes ?? [];
  const rawEdges = data?.edges ?? [];

  // Which nodes are active at this frame
  const activeNodes = useMemo(() => {
    const set = new Set<string>();
    for (const ev of timeline) {
      if (ev.type === "highlight-node" && currentMs >= ev.atMs && currentMs <= ev.atMs + ev.durationMs) {
        if (ev.target) set.add(ev.target);
      }
    }
    return set;
  }, [currentMs, timeline]);

  // Layout nodes vertically, centered in a portrait frame
  // We render inside a fixed 1080×1920 viewport that Remotion scales
  const nodeSpacingY = Math.min(280, (height - 400) / Math.max(1, rawNodes.length - 1));
  const totalHeight = (rawNodes.length - 1) * nodeSpacingY;
  const startY = height / 2 - totalHeight / 2 - 50;
  const centerX = width / 2 - 130;

  const rfNodes: Node[] = rawNodes.map((n, i) => ({
    id: n.id,
    type: "animated",
    position: { x: centerX, y: startY + i * nodeSpacingY },
    data: {
      label: n.label,
      icon: n.icon,
      color: NODE_COLORS[i % NODE_COLORS.length],
      index: i,
      active: activeNodes.has(n.id),
      seed: n.id + n.label,
    },
    draggable: false,
    selectable: false,
    connectable: false,
  }));

  // Moving packet — find active move-packet event
  const activePacket = useMemo(() => {
    return timeline.find(
      (ev) => ev.type === "move-packet" && currentMs >= ev.atMs && currentMs <= ev.atMs + ev.durationMs
    );
  }, [currentMs, timeline]);

  const rfEdges: Edge[] = rawEdges.map((e, i) => {
    const isActive = activePacket?.from === e.from && activePacket?.to === e.to;
    return {
      id: `edge-${i}`,
      source: e.from,
      target: e.to,
      label: isActive ? (activePacket?.text ?? e.label ?? "") : (e.label ?? ""),
      animated: isActive,
      style: {
        stroke: isActive ? "#fbbf24" : "#3b82f6",
        strokeWidth: isActive ? 4 : 2.5,
        opacity: 0.85,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: isActive ? "#fbbf24" : "#3b82f6",
      },
      labelStyle: {
        fill: isActive ? "#fbbf24" : "#94a3b8",
        fontWeight: 600,
        fontSize: 18,
        fontFamily: "Arial",
      },
      labelBgStyle: { fill: "rgba(15,23,42,0.8)", rx: 8 },
    };
  });

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        pointerEvents: "none",
        background: "transparent",
      }}
    >
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        panOnDrag={false}
        zoomOnScroll={false}
        zoomOnPinch={false}
        zoomOnDoubleClick={false}
        proOptions={{ hideAttribution: true }}
        style={{ background: "transparent", width: "100%", height: "100%" }}
      >
        <Background variant={BackgroundVariant.Dots} gap={48} size={1} color="rgba(148,163,184,0.08)" />
      </ReactFlow>
    </div>
  );
};

export default ReactFlowDiagram;
