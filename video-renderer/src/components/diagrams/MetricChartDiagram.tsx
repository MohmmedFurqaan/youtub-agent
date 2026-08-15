import React from "react";
import { useCurrentFrame, interpolate } from "remotion";

const MetricChartDiagram: React.FC<{ data: any }> = ({ data }) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [0, 90], [0.2, 1], { extrapolateRight: "clamp" });
  const values = data?.values ?? [42, 68, 88, 96];

  return (
    <svg width="100%" height="100%" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet">
      <rect width="1080" height="1920" fill="#020617" />
      {values.map((value: number, index: number) => {
        const x = 180 + index * 170;
        const barHeight = value * 1.8 * progress;
        return (
          <g key={index} transform={`translate(${x}, 1180)`}>
            <rect x={0} y={0} width={100} height={360} rx={18} fill="rgba(148,163,184,0.18)" />
            <rect x={0} y={360 - barHeight} width={100} height={barHeight} rx={18} fill={index % 2 === 0 ? "#60a5fa" : "#34d399"} />
            <text x={50} y={420} fill="#f8fafc" fontSize={22} fontWeight={600} fontFamily="Arial" textAnchor="middle">{value}%</text>
          </g>
        );
      })}
    </svg>
  );
};

export default MetricChartDiagram;
