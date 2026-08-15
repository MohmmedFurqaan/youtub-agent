import React from "react";
import { useCurrentFrame, interpolate, spring } from "remotion";

const ConceptCardDiagram: React.FC<{ data: any }> = ({ data }) => {
  const frame = useCurrentFrame();
  const focus = spring({ frame, fps: 30, config: { damping: 12 } });
  const scale = interpolate(focus, [0, 1], [0.94, 1], { extrapolateRight: "clamp" });
  const title = data?.title ?? "Choose the right method";
  const subtitle = data?.subtitle ?? "Match intent to action";

  return (
    <svg width="100%" height="100%" viewBox="0 0 1080 1920" preserveAspectRatio="xMidYMid meet">
      <rect width="1080" height="1920" fill="#020617" />
      <g transform={`translate(540 960) scale(${scale})`}>
        <rect x={-320} y={-220} width={640} height={440} rx={36} fill="rgba(15,23,42,0.85)" stroke="#a78bfa" strokeWidth={3} />
        <circle cx={-120} cy={-60} r={72} fill="rgba(167,139,250,0.18)" />
        <text x={0} y={-20} fill="#f8fafc" fontSize={42} fontWeight={800} fontFamily="Arial" textAnchor="middle">{title}</text>
        <text x={0} y={80} fill="#cbd5e1" fontSize={26} fontWeight={500} fontFamily="Arial" textAnchor="middle">{subtitle}</text>
        <rect x={-170} y={150} width={340} height={12} rx={8} fill="rgba(148,163,184,0.3)" />
        <rect x={-170} y={150} width={340 * interpolate(frame, [0, 90], [0.2, 1], { extrapolateRight: "clamp" })} height={12} rx={8} fill="#fbbf24" />
      </g>
    </svg>
  );
};

export default ConceptCardDiagram;
