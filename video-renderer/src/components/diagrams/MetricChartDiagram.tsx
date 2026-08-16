import React from "react";
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from "remotion";

interface MetricChartData {
  values?: number[];
  labels?: string[];
  animationTimeline?: Array<{ atMs: number; durationMs: number; type: string; label?: string }>;
}

const MetricChartDiagram: React.FC<{ data: MetricChartData; sceneStartMs?: number; sceneDurationMs?: number }> = ({ data, sceneStartMs = 0, sceneDurationMs = 5000 }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();

  const values = data?.values ?? [42, 68, 88, 96];
  const labels = data?.labels ?? ["Q1", "Q2", "Q3", "Q4"];

  const timeline = data?.animationTimeline ?? [];
  const metricEvent = timeline.find((e) => e.type === "metric-change");
  const startFrame = metricEvent ? Math.max(0, (metricEvent.atMs / 1000 * fps) - sceneStartMs / 1000 * fps) : 0;
  const progress = interpolate(frame, [startFrame, startFrame + 50], [0.15, 1], { extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) });

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
        const x = 180 + index * 170;
        const barHeight = value * 1.8 * progress;
        return (
          <g key={index} transform={`translate(${x}, 1180)`}>
            <rect x={0} y={0} width={100} height={360} rx={18} fill="rgba(148,163,184,0.15)" />
            <rect x={0} y={360 - barHeight} width={100} height={barHeight} rx={18} fill={index % 2 === 0 ? "#60a5fa" : "#34d399"} style={{ filter: `drop-shadow(0 0 12px ${index % 2 === 0 ? "rgba(96,165,250,0.6)" : "rgba(52,211,153,0.6)"})` }} />
            <text x={50} y={420} fill="#f8fafc" fontSize={22} fontWeight={600} fontFamily="Arial" textAnchor="middle">{value}%</text>
            <text x={50} y={460} fill="#94a3b8" fontSize={18} fontWeight={500} fontFamily="Arial" textAnchor="middle">{labels[index] ?? ""}</text>
          </g>
        );
      })}
      <text x={540} y={1060} fill="#94a3b8" fontSize={20} fontWeight={600} fontFamily="Arial" textAnchor="middle">METRIC CHART</text>
    </svg>
  );
};

export default MetricChartDiagram;
