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
  event?: any;
}

export interface BaseDiagramProps {
  data: any;
  event?: any;
  sceneStartMs?: number;
  sceneDurationMs?: number;
}

const DiagramRenderer: React.FC<{ spec: DiagramSpec; sceneStartMs?: number; sceneDurationMs?: number }> = ({ spec, sceneStartMs, sceneDurationMs }) => {
  const { data, event, template } = spec;
  const commonProps = { data, event, sceneStartMs, sceneDurationMs };
  switch (template) {
    case "request-flow":
      return <RequestFlowDiagram {...commonProps} />;
    case "architecture-layers":
      return <ArchitectureLayersDiagram {...commonProps} />;
    case "sequence":
      return <SequenceDiagram {...commonProps} />;
    case "comparison":
      return <ComparisonDiagram {...commonProps} />;
    case "timeline":
      return <TimelineDiagram {...commonProps} />;
    case "concept-card":
      return <ConceptCardDiagram {...commonProps} />;
    case "metric-chart":
      return <MetricChartDiagram {...commonProps} />;
    default:
      return <div />;
  }
};

export default DiagramRenderer;
