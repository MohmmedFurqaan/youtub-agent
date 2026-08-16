import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from "remotion";
import iconRegistry from "./iconRegistry";
import type { BaseDiagramProps } from "./DiagramRenderer";

type NodeData = { id: string; label: string; icon?: string };
type EdgeData = { from: string; to: string; label?: string };

type AnimationEvent = {
  atMs: number;
  durationMs: number;
  type: string;
  target?: string;
  from?: string;
  to?: string;
  text?: string;
};

type DiagramData = {
  nodes?: NodeData[];
  edges?: EdgeData[];
  highlightEdge?: number;
  animationTimeline?: AnimationEvent[];
};

type NodeProps = {
  x: number;
  y: number;
  label: string;
  icon?: string;
  index: number;
  active?: boolean;
  visible?: boolean;
};

const Node: React.FC<NodeProps> = ({
  x,
  y,
  label,
  icon,
  index,
  active = false,
  visible = true,
}) => {
  const frame = useCurrentFrame();

  /*
   * Node entrance is still deterministic, but can be disabled
   * when the timeline controls visibility.
   */
  const appear = spring({
    frame: Math.max(0, frame - index * 6),
    fps: 30,
    config: {
      damping: 16,
      stiffness: 140,
      mass: 0.7,
    },
  });

  const scale = interpolate(appear, [0, 1], [0.82, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const opacity = visible
    ? interpolate(appear, [0, 1], [0, 1], {
        extrapolateRight: "clamp",
      })
    : 0;

  const pulse = active
    ? 1 + 0.035 * Math.sin(frame * 0.45)
    : 1;

  const glowAmount = active ? 24 : 10;

  const IconComp = icon
    ? (iconRegistry as any)[icon]
    : null;

  return (
    <g
      transform={`translate(${x}, ${y}) scale(${scale * pulse})`}
      opacity={opacity}
    >
      <rect
        x={-126}
        y={-46}
        width={252}
        height={92}
        rx={20}
        fill="rgba(15,23,42,0.94)"
        stroke={
          active
            ? "rgba(250,204,21,0.98)"
            : "rgba(96,165,250,0.9)"
        }
        strokeWidth={active ? 4 : 2.5}
        style={{
          filter: `drop-shadow(0 0 ${glowAmount}px ${
            active
              ? "rgba(250,204,21,0.75)"
              : "rgba(96,165,250,0.35)"
          })`,
        }}
      />

      {IconComp && (
        <g transform="translate(-94, -18)">
          <IconComp color="#7dd3fc" size={30} />
        </g>
      )}

      <text
        x={-34}
        y={10}
        fill="#f8fafc"
        fontSize={25}
        fontFamily="Arial"
        fontWeight={700}
      >
        {label}
      </text>
    </g>
  );
};

type ArrowProps = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  active?: boolean;
};

const Arrow: React.FC<ArrowProps> = ({
  x1,
  y1,
  x2,
  y2,
  active = false,
}) => {
  const frame = useCurrentFrame();

  const pulse = active
    ? interpolate(
        (frame % 24) / 24,
        [0, 0.5, 1],
        [0.75, 1, 0.75]
      )
    : 0.75;

  return (
    <g>
      <line
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke={
          active
            ? "rgba(250,204,21,0.98)"
            : "rgba(125,211,252,0.55)"
        }
        strokeWidth={active ? 6 : 4}
        strokeLinecap="round"
        strokeDasharray={active ? "10 8" : "16 12"}
        opacity={pulse}
        style={{
          filter: active
            ? "drop-shadow(0 0 14px rgba(250,204,21,0.7))"
            : undefined,
        }}
      />

      {/* Direction marker */}
      <circle
        cx={x2}
        cy={y2}
        r={active ? 6 : 4}
        fill={active ? "#fbbf24" : "#7dd3fc"}
        opacity={0.9}
      />
    </g>
  );
};

type PacketProps = {
  x: number;
  y: number;
  text?: string;
  progress: number;
};

const Packet: React.FC<PacketProps> = ({
  x,
  y,
  text,
  progress,
}) => {
  const size =
    13 + 7 * Math.sin(progress * Math.PI);

  const opacity = interpolate(
    progress,
    [0, 0.05, 0.9, 1],
    [0, 1, 1, 0],
    {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }
  );

  return (
    <g
      transform={`translate(${x}, ${y})`}
      opacity={opacity}
    >
      {/* outer glow */}
      <circle
        r={size * 1.8}
        fill="rgba(245,158,11,0.12)"
      />

      {/* packet */}
      <circle
        r={size}
        fill="#f59e0b"
        style={{
          filter:
            "drop-shadow(0 4px 14px rgba(245,158,11,0.8))",
        }}
      />

      {/* packet core */}
      <circle
        r={size * 0.35}
        fill="#fff7ed"
      />

      {text && (
        <text
          x={size + 12}
          y={6}
          fill="#ffffff"
          fontSize={18}
          fontFamily="Arial"
          fontWeight={700}
        >
          {text}
        </text>
      )}
    </g>
  );
};

type CursorProps = {
  x: number;
  y: number;
  visible: boolean;
  clicking: boolean;
};

const Cursor: React.FC<CursorProps> = ({
  x,
  y,
  visible,
  clicking,
}) => {
  const frame = useCurrentFrame();

  if (!visible) {
    return null;
  }

  const clickPulse = clicking
    ? interpolate(
        (frame % 12) / 12,
        [0, 0.4, 1],
        [0.4, 1, 0.4]
      )
    : 0;

  return (
    <g
      transform={`translate(${x}, ${y})`}
      pointerEvents="none"
    >
      {clicking && (
        <>
          <circle
            r={30 + clickPulse * 12}
            fill="none"
            stroke="rgba(250,204,21,0.85)"
            strokeWidth={4}
            opacity={1 - clickPulse * 0.5}
          />

          <circle
            r={12 + clickPulse * 6}
            fill="rgba(250,204,21,0.2)"
          />
        </>
      )}

      {/* Cursor */}
      <path
        d="M-8 -22 L-2 18 L7 8 L18 25 L25 20 L14 4 L27 2 Z"
        fill="#ffffff"
        stroke="#020617"
        strokeWidth={3}
        transform="rotate(-12)"
        style={{
          filter:
            "drop-shadow(0 3px 8px rgba(0,0,0,0.65))",
        }}
      />
    </g>
  );
};

const RequestFlowDiagram: React.FC<BaseDiagramProps> = ({
  data,
  event: _event,
  sceneStartMs = 0,
  sceneDurationMs: _sceneDurationMs,
}) => {
  const { width, height, fps } = useVideoConfig();
  const frame = useCurrentFrame();

  const currentMs = (frame / fps) * 1000;
  const typedData: DiagramData = data;
  const nodes: NodeData[] = typedData?.nodes ?? [];
  const edges: EdgeData[] = typedData?.edges ?? [];
  const timeline: AnimationEvent[] = typedData?.animationTimeline ?? [];

  /*
   * Position nodes horizontally.
   */
  const step = Math.min(
    280,
    Math.floor(
      (width - 260) / Math.max(1, nodes.length - 1)
    )
  );

  const nodePositions = nodes.map((_, index) => {
    const totalWidth =
      Math.max(0, nodes.length - 1) * step;

    const startX =
      width / 2 - totalWidth / 2;

    return {
      x: startX + index * step,
      y: height / 2 + 40,
    };
  });

  const getNodePosition = (id?: string) => {
    if (!id) return null;

    const index = nodes.findIndex(
      (node) => node.id === id
    );

    if (index === -1) return null;

    return nodePositions[index];
  };

  /*
   * ---------------------------------------------------------
   * EVENT HELPERS
   * ---------------------------------------------------------
   */

  const eventIsActive = (
    event: AnimationEvent
  ) => {
    return (
      currentMs >= event.atMs &&
      currentMs <= event.atMs + event.durationMs
    );
  };

  const nodeIsActive = (nodeId: string) => {
    return timeline.some((event) => {
      if (
        event.type !== "highlight-node" &&
        event.type !== "pulse"
      ) {
        return false;
      }

      return (
        event.target === nodeId &&
        eventIsActive(event)
      );
    });
  };

  const edgeIsActive = (
    fromId: string,
    toId: string
  ) => {
    return timeline.some((event) => {
      if (event.type !== "highlight-edge") {
        return false;
      }

      return (
        event.from === fromId &&
        event.to === toId &&
        eventIsActive(event)
      );
    });
  };

  /*
   * ---------------------------------------------------------
   * NODE VISIBILITY
   * ---------------------------------------------------------
   *
   * If there is no explicit enter/exit event, nodes appear
   * normally.
   *
   * If an enter event exists for a node, it becomes visible
   * during that event.
   */

  const nodeIsVisible = (nodeId: string) => {
    const enterEvents = timeline.filter(
      (event) =>
        event.type === "enter" &&
        event.target === nodeId
    );

    const exitEvents = timeline.filter(
      (event) =>
        event.type === "exit" &&
        event.target === nodeId
    );

    /*
     * No explicit visibility control.
     */
    if (
      enterEvents.length === 0 &&
      exitEvents.length === 0
    ) {
      return true;
    }

    const hasEntered = enterEvents.some(
      (event) =>
        currentMs >=
        event.atMs + event.durationMs
    );

    const hasStartedEntering = enterEvents.some(
      (event) =>
        currentMs >= event.atMs
    );

    const hasExited = exitEvents.some(
      (event) =>
        currentMs >=
        event.atMs + event.durationMs
    );

    if (hasExited) {
      return false;
    }

    return hasEntered || hasStartedEntering;
  };

  /*
   * ---------------------------------------------------------
   * PACKET ANIMATION
   * ---------------------------------------------------------
   */

  const movingPackets = timeline.filter(
    (event) => event.type === "move-packet"
  );

  /*
   * ---------------------------------------------------------
   * CURSOR ANIMATION
   * ---------------------------------------------------------
   */

  const cursorEvents = timeline.filter(
    (event) => event.type === "cursor-move"
  );

  const clickEvents = timeline.filter(
    (event) => event.type === "click"
  );

  const cursorIsVisible =
    cursorEvents.length > 0;

  let cursorX = width / 2;
  let cursorY = height / 2;

  if (cursorEvents.length > 0) {
    /*
     * Find the current cursor movement.
     */
    let currentCursorEvent:
      | AnimationEvent
      | undefined;

    for (let i = 0; i < cursorEvents.length; i++) {
      const event = cursorEvents[i];

      const targetPosition =
        getNodePosition(event.target);

      if (!targetPosition) continue;

      if (currentMs < event.atMs) {
        break;
      }

      if (
        currentMs <=
        event.atMs + event.durationMs
      ) {
        currentCursorEvent = event;
        break;
      }
    }

    if (currentCursorEvent) {
      const targetPosition =
        getNodePosition(
          currentCursorEvent.target
        );

      if (targetPosition) {
        const progress = Math.min(
          1,
          Math.max(
            0,
            (currentMs -
              currentCursorEvent.atMs) /
              currentCursorEvent.durationMs
          )
        );

        /*
         * Find where the cursor started.
         */
        const eventIndex =
          cursorEvents.indexOf(
            currentCursorEvent
          );

        const previousEvent =
          eventIndex > 0
            ? cursorEvents[eventIndex - 1]
            : undefined;

        const previousPosition =
          getNodePosition(
            previousEvent?.target
          ) ?? {
            x: targetPosition.x - 220,
            y: targetPosition.y - 160,
          };

        cursorX = interpolate(
          progress,
          [0, 1],
          [
            previousPosition.x,
            targetPosition.x,
          ],
          {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(
              0.16,
              1,
              0.3,
              1
            ),
          }
        );

        cursorY = interpolate(
          progress,
          [0, 1],
          [
            previousPosition.y - 120,
            targetPosition.y - 120,
          ],
          {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(
              0.16,
              1,
              0.3,
              1
            ),
          }
        );
      }
    } else {
      /*
       * After all cursor movements, keep the cursor
       * at the final target.
       */
      const lastEvent =
        cursorEvents[cursorEvents.length - 1];

      const lastPosition =
        getNodePosition(lastEvent.target);

      if (lastPosition) {
        cursorX = lastPosition.x;
        cursorY = lastPosition.y - 120;
      }
    }
  }

  const clicking = clickEvents.some(
    (event) => eventIsActive(event)
  );

  /*
   * ---------------------------------------------------------
   * RENDER
   * ---------------------------------------------------------
   */

  return (
    <svg
      width="100%"
      height="100%"
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="xMidYMid meet"
    >
      <defs>
        <radialGradient
          id="requestFlowGlow"
          cx="50%"
          cy="35%"
          r="70%"
        >
          <stop
            offset="0%"
            stopColor="rgba(59,130,246,0.18)"
          />
          <stop
            offset="100%"
            stopColor="rgba(15,23,42,0)"
          />
        </radialGradient>

        <linearGradient
          id="packetGradient"
          x1="0"
          y1="0"
          x2="1"
          y2="1"
        >
          <stop
            offset="0%"
            stopColor="#fde68a"
          />
          <stop
            offset="100%"
            stopColor="#f59e0b"
          />
        </linearGradient>
      </defs>

      {/* Background */}
      <rect
        width={width}
        height={height}
        fill="#020617"
      />

      <rect
        width={width}
        height={height}
        fill="url(#requestFlowGlow)"
      />

      {/* Diagram */}
      <g>
        {/* Edges */}
        {edges.map((edge, index) => {
          const fromPosition =
            getNodePosition(edge.from);

          const toPosition =
            getNodePosition(edge.to);

          if (
            !fromPosition ||
            !toPosition
          ) {
            return null;
          }

          const active =
            edgeIsActive(
              edge.from,
              edge.to
            );

          return (
            <Arrow
              key={`edge-${index}`}
              x1={fromPosition.x + 126}
              y1={fromPosition.y}
              x2={toPosition.x - 126}
              y2={toPosition.y}
              active={active}
            />
          );
        })}

        {/* Nodes */}
        {nodes.map((node, index) => {
          const position =
            nodePositions[index];

          if (!position) {
            return null;
          }

          return (
            <Node
              key={node.id}
              x={position.x}
              y={position.y}
              label={node.label}
              icon={node.icon}
              index={index}
              active={nodeIsActive(node.id)}
              visible={nodeIsVisible(node.id)}
            />
          );
        })}

        {/* Moving packets */}
        {movingPackets.map(
          (event, index) => {
            const fromPosition =
              getNodePosition(event.from);

            const toPosition =
              getNodePosition(event.to);

            if (
              !fromPosition ||
              !toPosition
            ) {
              return null;
            }

            const progress = Math.min(
              1,
              Math.max(
                0,
                (currentMs -
                  event.atMs) /
                  event.durationMs
              )
            );

            /*
             * Keep packet visible at both endpoints
             * for a few frames so the movement doesn't
             * appear to pop.
             */
            const packetX = interpolate(
              progress,
              [0, 1],
              [
                fromPosition.x + 126,
                toPosition.x - 126,
              ],
              {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
                easing: Easing.bezier(
                  0.16,
                  1,
                  0.3,
                  1
                ),
              }
            );

            const packetY = interpolate(
              progress,
              [0, 1],
              [
                fromPosition.y,
                toPosition.y,
              ],
              {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              }
            );

            /*
             * Don't render before the event begins.
             */
            if (
              currentMs <
              event.atMs
            ) {
              return null;
            }

            /*
             * Don't render too far after the event.
             */
            if (
              currentMs >
              event.atMs +
                event.durationMs
            ) {
              return null;
            }

            return (
              <Packet
                key={`packet-${index}`}
                x={packetX}
                y={packetY - 22}
                text={event.text}
                progress={progress}
              />
            );
          }
        )}

        {/* Timeline-driven cursor */}
        <Cursor
          x={cursorX}
          y={cursorY}
          visible={cursorIsVisible}
          clicking={clicking}
        />
      </g>
    </svg>
  );
};

export default RequestFlowDiagram;