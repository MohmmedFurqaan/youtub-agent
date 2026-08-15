import React from "react";
import RequestFlowDiagram from "./RequestFlowDiagram";
import ArchitectureLayersDiagram from "./ArchitectureLayersDiagram";
import SequenceDiagram from "./SequenceDiagram";
import ComparisonDiagram from "./ComparisonDiagram";
import TimelineDiagram from "./TimelineDiagram";
import ConceptCardDiagram from "./ConceptCardDiagram";
import MetricChartDiagram from "./MetricChartDiagram";

export interface DiagramSpec {
  template: string;
  data: any;
}

const DiagramRenderer: React.FC<{ spec: DiagramSpec; sceneStartMs?: number; sceneDurationMs?: number }> = ({ spec, sceneStartMs, sceneDurationMs }) => {
  switch (spec.template) {
    case "request-flow":
      return <RequestFlowDiagram data={spec.data} sceneStartMs={sceneStartMs} sceneDurationMs={sceneDurationMs} />;
    case "architecture-layers":
      return <ArchitectureLayersDiagram data={spec.data} sceneStartMs={sceneStartMs} sceneDurationMs={sceneDurationMs} />;
    case "sequence":
      return <SequenceDiagram data={spec.data} sceneStartMs={sceneStartMs} sceneDurationMs={sceneDurationMs} />;
    case "comparison":
      return <ComparisonDiagram data={spec.data} sceneStartMs={sceneStartMs} sceneDurationMs={sceneDurationMs} />;
    case "timeline":
      return <TimelineDiagram data={spec.data} sceneStartMs={sceneStartMs} sceneDurationMs={sceneDurationMs} />;
    case "concept-card":
      return <ConceptCardDiagram data={spec.data} sceneStartMs={sceneStartMs} sceneDurationMs={sceneDurationMs} />;
    case "metric-chart":
      return <MetricChartDiagram data={spec.data} sceneStartMs={sceneStartMs} sceneDurationMs={sceneDurationMs} />;
    default:
      return <div />;
  }
};

export default DiagramRenderer;
