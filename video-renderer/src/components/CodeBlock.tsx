/**
 * components/CodeBlock.tsx
 *
 * Renders a vertical mobile-optimized code editor window with:
 *  - High-contrast syntax highlighting
 *  - Line numbering & active line highlight animation
 *  - Title header with language tag
 *  - Smooth entrance & reveal animations
 *  - Safe-area compliance for 1080×1920 YouTube Shorts
 */

import React from "react";
import { useCurrentFrame, useVideoConfig, spring, interpolate, Easing } from "remotion";
import { SAFE_AREAS } from "./SafeAreas";

interface CodeBlockProps {
  code: string;
  language?: string;
  highlightLines?: number[];
  title?: string;
  focusRange?: [number, number];
}

/** Basic keyword highlighters for Python and JavaScript/TypeScript */
const PYTHON_KEYWORDS = new Set([
  "def", "class", "return", "import", "from", "as", "if", "else", "elif",
  "for", "while", "in", "with", "try", "except", "finally", "raise", "async",
  "await", "lambda", "yield", "pass", "break", "continue", "None", "True", "False",
  "and", "or", "not", "is"
]);

const JS_KEYWORDS = new Set([
  "const", "let", "var", "function", "return", "if", "else", "for", "while",
  "import", "export", "default", "from", "as", "async", "await", "try", "catch",
  "finally", "throw", "new", "class", "extends", "type", "interface", "null",
  "undefined", "true", "false"
]);

function highlightToken(token: string, lang: string): { text: string; color: string } {
  const cleanLang = (lang || "python").toLowerCase();
  const keywords = cleanLang.includes("js") || cleanLang.includes("ts") ? JS_KEYWORDS : PYTHON_KEYWORDS;

  if (keywords.has(token)) {
    return { text: token, color: "#f472b6" }; // Pink keyword
  }
  if (/^["'].*["']$/.test(token)) {
    return { text: token, color: "#34d399" }; // Emerald string
  }
  if (/^\d+$/.test(token)) {
    return { text: token, color: "#fbbf24" }; // Amber number
  }
  if (/^[A-Z][a-zA-Z0-9_]*$/.test(token)) {
    return { text: token, color: "#60a5fa" }; // Blue class/type
  }
  if (/^#.*$/.test(token) || /^\/\/.*$/.test(token)) {
    return { text: token, color: "#94a3b8" }; // Muted comment
  }
  return { text: token, color: "#f3f4f6" }; // Default white
}

function parseAndHighlightLine(line: string, lang: string): React.ReactNode[] {
  const tokens = line.split(/(\s+|".*?"|'.*?'|#.*|\/\/.*|[a-zA-Z_]\w*|\d+|[^\s\w])/g);
  return tokens.map((t, idx) => {
    if (!t) return null;
    if (/^\s+$/.test(t)) return <span key={idx}>{t}</span>;
    const { text, color } = highlightToken(t, lang);
    return (
      <span key={idx} style={{ color }}>
        {text}
      </span>
    );
  });
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language = "python",
  highlightLines = [],
  title = "main.py",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Entrance spring animation
  const pop = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 120, mass: 0.8 },
  });

  const scale = interpolate(pop, [0, 1], [0.85, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  const opacity = interpolate(pop, [0, 1], [0, 1], {
    extrapolateRight: "clamp",
  });

  const lines = code.trim().split("\n");
  const highlightSet = new Set(highlightLines);

  // Line reveal progress (typewriter / line reveal effect)
  const lineRevealCount = Math.floor(
    interpolate(frame, [10, 35], [1, lines.length], {
      extrapolateRight: "clamp",
      extrapolateLeft: "clamp",
    })
  );

  return (
    <div
      style={{
        position: "absolute",
        top: SAFE_AREAS.content.top + 100,
        left: 40,
        right: 40,
        bottom: SAFE_AREAS.captions.bottom + 160,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        zIndex: 20,
        opacity,
        transform: `scale(${scale})`,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 1000,
          background: "rgba(15, 23, 42, 0.92)",
          borderRadius: 20,
          border: "2px solid rgba(59, 130, 246, 0.4)",
          boxShadow:
            "0 25px 50px -12px rgba(0, 0, 0, 0.85), 0 0 30px rgba(59, 130, 246, 0.2)",
          backdropFilter: "blur(16px)",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Window Header */}
        <div
          style={{
            height: 52,
            background: "rgba(30, 41, 59, 0.95)",
            borderBottom: "1px solid rgba(148, 163, 184, 0.2)",
            display: "flex",
            alignItems: "center",
            padding: "0 20px",
            justifyContent: "space-between",
          }}
        >
          {/* macOS Window Controls */}
          <div style={{ display: "flex", gap: 10 }}>
            <div style={{ width: 14, height: 14, borderRadius: "50%", background: "#ef4444" }} />
            <div style={{ width: 14, height: 14, borderRadius: "50%", background: "#f59e0b" }} />
            <div style={{ width: 14, height: 14, borderRadius: "50%", background: "#10b981" }} />
          </div>

          {/* Title */}
          <span
            style={{
              fontFamily: "'Inter', sans-serif",
              fontSize: 22,
              fontWeight: 700,
              color: "#94a3b8",
              letterSpacing: "0.5px",
            }}
          >
            {title}
          </span>

          {/* Language Tag */}
          <span
            style={{
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
              fontSize: 18,
              fontWeight: 800,
              color: "#3b82f6",
              textTransform: "uppercase",
              background: "rgba(59, 130, 246, 0.15)",
              padding: "4px 12px",
              borderRadius: 8,
              border: "1px solid rgba(59, 130, 246, 0.3)",
            }}
          >
            {language}
          </span>
        </div>

        {/* Code Content */}
        <div
          style={{
            padding: "24px 20px",
            fontFamily: "'JetBrains Mono', 'Fira Code', 'Courier New', monospace",
            fontSize: 32,
            lineHeight: 1.6,
            overflowX: "auto",
          }}
        >
          {lines.slice(0, lineRevealCount).map((lineStr, idx) => {
            const lineNum = idx + 1;
            const isHighlighted = highlightSet.has(lineNum);

            return (
              <div
                key={idx}
                style={{
                  display: "flex",
                  alignItems: "center",
                  padding: "4px 12px",
                  borderRadius: 8,
                  background: isHighlighted
                    ? "rgba(251, 191, 36, 0.18)"
                    : "transparent",
                  borderLeft: isHighlighted
                    ? "5px solid #fbbf24"
                    : "5px solid transparent",
                  transition: "all 0.3s ease",
                }}
              >
                {/* Line number */}
                <span
                  style={{
                    width: 50,
                    color: isHighlighted ? "#fbbf24" : "#475569",
                    fontWeight: isHighlighted ? 800 : 500,
                    userSelect: "none",
                    textAlign: "right",
                    marginRight: 24,
                    fontSize: 26,
                  }}
                >
                  {lineNum}
                </span>

                {/* Line text */}
                <span style={{ whiteSpace: "pre" }}>
                  {parseAndHighlightLine(lineStr, language)}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
