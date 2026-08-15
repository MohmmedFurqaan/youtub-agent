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

const DiagramRenderer: React.FC<{ spec: DiagramSpec }> = ({ spec }) => {
  switch (spec.template) {
    case "request-flow":
      return <RequestFlowDiagram data={spec.data} />;
    case "architecture-layers":
      return <ArchitectureLayersDiagram data={spec.data} />;
    case "sequence":
      return <SequenceDiagram data={spec.data} />;
    case "comparison":
      return <ComparisonDiagram data={spec.data} />;
    case "timeline":
      return <TimelineDiagram data={spec.data} />;
    case "concept-card":
      return <ConceptCardDiagram data={spec.data} />;
    case "metric-chart":
      return <MetricChartDiagram data={spec.data} />;
    default:
      return <div />;
  }
};

export default DiagramRenderer;
