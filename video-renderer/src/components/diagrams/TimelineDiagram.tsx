import React from "react";
import { useCurrentFrame, interpolate } from "remotion";

const TimelineDiagram: React.FC<{ data: any }> = ({ data }) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [0, 90], [0, 1], { extrapolateRight: "clamp" });
  const steps = data?.steps ?? ["Request", "Validate", "Process", "Respond"];

  return (
    <svg width="100%" height="100%" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet">
      <rect width="1080" height="1920" fill="#020617" />
      <line x1={150} y1={980} x2={930} y2={980} stroke="#cbd5e1" strokeWidth={6} strokeDasharray="12 12" />
      <rect x={150} y={930} width={780 * progress} height={100} rx={12} fill="rgba(96,165,250,0.35)" />
      {steps.map((label: string, index: number) => {
        const x = 180 + index * 200;
        return (
          <g key={label} transform={`translate(${x}, 900)`}>
            <circle r={24} fill={index <= progress * (steps.length - 1) ? "#34d399" : "#46556d"} />
            <text x={0} y={80} fill="#f8fafc" fontSize={22} fontWeight={600} fontFamily="Arial" textAnchor="middle">{label}</text>
          </g>
        );
      })}
    </svg>
  );
};

export default TimelineDiagram;
