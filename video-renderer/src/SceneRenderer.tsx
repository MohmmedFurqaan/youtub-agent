import { AbsoluteFill, Audio, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { Scene } from "./types";

interface SceneRendererProps {
  scene: Scene;
}

/**
 * SceneRenderer — renders one scene of a faceless video.
 *
 * Layout (1080×1920 portrait):
 * ┌────────────────────────────┐
 * │  [Ken Burns background]    │  full-frame, slow zoom + pan
 * │                            │
 * │  ╔══════════════════════╗  │
 * │  ║  ON SCREEN TEXT      ║  │  keyword badge — top-center
 * │  ╚══════════════════════╝  │
 * │                            │
 * │  ┌──────────────────────┐  │
 * │  │  word  by  WORD  rev │  │  TikTok-style word-by-word captions — bottom
 * │  └──────────────────────┘  │
 * │  ████████████░░░░░░░░░░░   │  scene progress bar — very bottom
 * └────────────────────────────┘
 */
export const SceneRenderer: React.FC<SceneRendererProps> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  // ── Ken Burns — slow zoom + alternating pan direction ───────────────────
  // Even scenes pan right→left, odd scenes pan left→right
  const panDir = scene.scene_number % 2 === 0 ? 1 : -1;
  const kenBurnsScale = interpolate(frame, [0, durationInFrames], [1.0, 1.1]);
  const kenBurnsX = interpolate(frame, [0, durationInFrames], [0, panDir * 24]);
  const kenBurnsY = interpolate(frame, [0, durationInFrames], [0, -12]);

  // ── Keyword badge — fade in over first 10 frames, hold, fade out last 8 ─
  const badgeFadeIn = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const badgeFadeOut = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const badgeOpacity = Math.min(badgeFadeIn, badgeFadeOut);
  const badgeScale = interpolate(badgeFadeIn, [0, 1], [0.88, 1]);

  // ── Word-by-word captions ────────────────────────────────────────────────
  const words = scene.narration.trim().split(/\s+/);
  const framesPerWord = durationInFrames / Math.max(words.length, 1);
  const currentWordIdx = Math.min(Math.floor(frame / framesPerWord), words.length - 1);

  // Group words in chunks of 4 (TikTok window)
  const GROUP = 4;
  const groupStart = Math.floor(currentWordIdx / GROUP) * GROUP;
  const groupWords = words.slice(groupStart, groupStart + GROUP);
  const activeInGroup = currentWordIdx - groupStart;

  // Group slides in from below on the first frame it appears
  const groupFirstFrame = groupStart * framesPerWord;
  const groupSlide = interpolate(frame - groupFirstFrame, [0, 6], [20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const groupFadeIn = interpolate(frame - groupFirstFrame, [0, 6], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // ── Progress bar ─────────────────────────────────────────────────────────
  const progressPct = (frame / durationInFrames) * 100;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000", overflow: "hidden" }}>

      {/* ── Background with Ken Burns ───────────────────────────────────── */}
      <AbsoluteFill
        style={{
          transform: `scale(${kenBurnsScale}) translate(${kenBurnsX}px, ${kenBurnsY}px)`,
          transformOrigin: "center center",
        }}
      >
        <Img
          src={staticFile(scene.background_image)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            objectPosition: "center",
          }}
        />
      </AbsoluteFill>

      {/* ── Dark gradient — top and bottom for text legibility ──────────── */}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(to bottom, rgba(0,0,0,0.65) 0%, transparent 30%, transparent 60%, rgba(0,0,0,0.82) 100%)",
        }}
      />

      {/* ── TTS Audio ───────────────────────────────────────────────────── */}
      {scene.audio_file && <Audio src={staticFile(scene.audio_file)} />}

      {/* ── Keyword Badge (top-center) ───────────────────────────────────── */}
      <div
        style={{
          position: "absolute",
          top: "6%",
          left: 0,
          right: 0,
          display: "flex",
          justifyContent: "center",
          opacity: badgeOpacity,
          transform: `scale(${badgeScale})`,
          zIndex: 10,
        }}
      >
        <div
          style={{
            background: "linear-gradient(135deg, #6C63FF 0%, #FF6584 100%)",
            borderRadius: 999,
            padding: "14px 44px",
            boxShadow: "0 8px 32px rgba(108,99,255,0.45)",
          }}
        >
          <span
            style={{
              fontFamily: "'Inter', 'Helvetica Neue', sans-serif",
              fontSize: 44,
              fontWeight: 900,
              color: "#FFFFFF",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              textShadow: "0 2px 8px rgba(0,0,0,0.3)",
            }}
          >
            {scene.on_screen_text}
          </span>
        </div>
      </div>

      {/* ── Word-by-word Caption Bar (bottom) ───────────────────────────── */}
      <div
        style={{
          position: "absolute",
          bottom: "10%",
          left: "5%",
          right: "5%",
          display: "flex",
          justifyContent: "center",
          flexWrap: "wrap",
          gap: 10,
          opacity: groupFadeIn,
          transform: `translateY(${groupSlide}px)`,
          zIndex: 10,
        }}
      >
        {groupWords.map((word, i) => {
          const isActive = i === activeInGroup;
          return (
            <span
              key={`${groupStart}-${i}`}
              style={{
                fontFamily: "'Inter', 'Helvetica Neue', sans-serif",
                fontSize: 72,
                fontWeight: isActive ? 900 : 700,
                color: isActive ? "#FFE066" : "rgba(255,255,255,0.85)",
                textShadow: isActive
                  ? "0 0 24px rgba(255,224,102,0.7), 0 2px 12px rgba(0,0,0,0.8)"
                  : "0 2px 10px rgba(0,0,0,0.7)",
                transform: isActive ? "scale(1.08)" : "scale(1)",
                transition: "color 0.1s, transform 0.1s",
                letterSpacing: "-0.01em",
                lineHeight: 1.2,
              }}
            >
              {word}
            </span>
          );
        })}
      </div>

      {/* ── Progress Bar (very bottom) ───────────────────────────────────── */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          width: "100%",
          height: 8,
          backgroundColor: "rgba(255,255,255,0.15)",
          zIndex: 20,
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${progressPct}%`,
            background: "linear-gradient(90deg, #6C63FF, #FF6584)",
            borderRadius: "0 4px 4px 0",
          }}
        />
      </div>

    </AbsoluteFill>
  );
};
