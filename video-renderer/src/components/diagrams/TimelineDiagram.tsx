import React from "react";
const TimelineDiagram: React.FC<{ data: any }> = () => (
  <svg width="100%" height="100%" viewBox="0 0 1080 1920">
    <rect width="100%" height="100%" fill="#071033" />
    <text x="50%" y="50%" fill="#fff" textAnchor="middle">Timeline</text>
  </svg>
);
export default TimelineDiagram;
