import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from "remotion";
import type { BaseDiagramProps } from "./DiagramRenderer";

type NodeData = { id: string; label: string; icon?: string };
type AnimEvent = { atMs: number; durationMs: number; type: string; label?: string; result?: string };

const MetricChartDiagram: React.FC<BaseDiagramProps> = ({ data, event, sceneStartMs = 0, sceneDurationMs }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  const nodes: NodeData[] = data?.nodes ?? [];
  const timeline: AnimEvent[] = data?.animationTimeline ?? [];

  // Derive values and labels from data or event
  const providedValues: number[] | undefined = data?.values;
  const providedLabels: string[] | undefined = data?.labels;

  // If explicit values provided in data, use them
  if (providedValues && providedLabels) {
    return renderChart(providedValues, providedLabels, nodes, timeline, fps, frame, sceneStartMs, event);
  }

  // Derive from nodes + event
  let labels: string[];
  let values: number[];

  if (nodes.length > 0) {
    labels = nodes.map((n) => n.label || n.id);

    // Try to parse numeric value from event.result
    const resultStr = event?.result || "";
    const numericMatch = resultStr.match(/(\d+(?:\.\d+)?)/);
    const finalValue = numericMatch ? parseFloat(numericMatch[1]) : 100;

    // If one node, use the final value; if multiple nodes, ramp up to it
    if (nodes.length === 1) {
      values = [finalValue];
    } else {
      values = nodes.map((_, i) => {
        const ratio = (i + 1) / nodes.length;
        return Math.round(finalValue * ratio * 0.7 + finalValue * 0.3);
      });
      values[values.length - 1] = finalValue; // last value is the final result
    }
  } else {
    // Fallback: use event labels or generic labels
    const label = event?.label || event?.action || "Metric";
    labels = [label];
    const resultStr = event?.result || "100";
    const numericMatch = resultStr.match(/(\d+(?:\.\d+)?)/);
    values = [numericMatch ? parseFloat(numericMatch[1]) : 100];
  }

  return renderChart(values, labels, nodes, timeline, fps, frame, sceneStartMs, event);
};

function renderChart(
  values: number[],
  labels: string[],
  nodes: NodeData[],
  timeline: AnimEvent[],
  fps: number,
  frame: number,
  sceneStartMs: number,
  event?: any,
): React.ReactElement {
  if (values.length === 0 || labels.length === 0) {
    return (
      <svg width="100%" height="100%" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet">
        <rect width="1080" height="1920" fill="#020617" />
        <text x={540} y={960} fill="#94a3b8" fontSize={28} fontWeight={600} fontFamily="Arial" textAnchor="middle">No metric data</text>
      </svg>
    );
  }

  const metricEvent = timeline.find((e) => e.type === "metric-change");
  const startFrame = metricEvent
    ? Math.max(0, (metricEvent.atMs / 1000 * fps) - sceneStartMs / 1000 * fps)
    : 0;
  const progress = interpolate(frame, [startFrame, startFrame + 50], [0.15, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const maxLabelLength = Math.max(...labels.map((l) => l.length));
  const fontSize = maxLabelLength > 12 ? 18 : 22;

  return (
    <svg width="100%" height="100%" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="metric-bg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#020617" />
          <stop offset="100%" stopColor="#0f172a" />
        </linearGradient>
      </defs>
      <rect width="1080" height="1920" fill="url(#metric-bg)" />
      {values.map((value, index) => {
        const barCount = values.length;
        const x = 180 + index * Math.floor((720 / Math.max(1, barCount - 1)));
        const barHeight = value * 1.8 * progress;
        const barWidth = Math.min(120, 1200 / barCount);
        const label = labels[index] ?? "";

        return (
          <g key={nodes[index]?.id ?? index} transform={`translate(${x}, 1180)`}>
            <rect x={0} y={0} width={barWidth} height={360} rx={18} fill="rgba(148,163,184,0.15)" />
            <rect
              x={0}
              y={360 - barHeight}
              width={barWidth}
              height={barHeight}
              rx={18}
              fill={index % 2 === 0 ? "#60a5fa" : "#34d399"}
              style={{
                filter: `drop-shadow(0 0 12px ${index % 2 === 0 ? "rgba(96,165,250,0.6)" : "rgba(52,211,153,0.6)"})`,
              }}
            />
            <text x={barWidth / 2} y={420} fill="#f8fafc" fontSize={fontSize} fontWeight={600} fontFamily="Arial" textAnchor="middle">
              {value}
              {event?.result?.includes("%") && "%"}
            </text>
            <text x={barWidth / 2} y={460} fill="#94a3b8" fontSize={fontSize - 4} fontWeight={500} fontFamily="Arial" textAnchor="middle">
              {label}
            </text>
          </g>
        );
      })}
      <text x={540} y={1060} fill="#94a3b8" fontSize={20} fontWeight={600} fontFamily="Arial" textAnchor="middle">
        {event?.label || "METRIC"}
      </text>
    </svg>
  );
}

export default MetricChartDiagram;
