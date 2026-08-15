import React from "react";
const ComparisonDiagram: React.FC<{ data: any }> = () => (
  <svg width="100%" height="100%" viewBox="0 0 1080 1920">
    <rect width="100%" height="100%" fill="#071033" />
    <text x="50%" y="50%" fill="#fff" textAnchor="middle">Comparison</text>
  </svg>
);
export default ComparisonDiagram;
