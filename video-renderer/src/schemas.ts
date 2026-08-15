/**
 * schemas.ts
 *
 * Zod schema for the ShortVideo Remotion composition props.
 * Must mirror the Python VideoPlan → props.json structure produced by run_pipeline.py.
 */

import { z } from "zod";

// Caption record — matches @remotion/captions Caption type
export const captionSchema = z.object({
  text: z.string(),
  startMs: z.number(),
  endMs: z.number(),
  timestampMs: z.number(),
  confidence: z.number(),
});

// One scene prop passed to Remotion
export const scenePropSchema = z.object({
  id: z.string(),
  fromFrame: z.number().int().nonnegative(),
  durationInFrames: z.number().int().positive(),
  /** Relative path inside video-renderer/public/runs/<run-id>/ */
  assetSrc: z.string(),
  assetKind: z.enum(["stock_video", "image", "diagram", "screen_capture"]),
  onScreenText: z.string(),
  transition: z.enum(["cut", "fade", "slide"]),
  // Optional typed diagram payload for Remotion-native diagrams
  diagram: z
    .object({
      template: z.enum([
        "request-flow",
        "architecture-layers",
        "sequence",
        "comparison",
        "timeline",
        "concept-card",
        "metric-chart",
      ]),
      data: z.object({
        nodes: z.array(
          z.object({
            id: z.string(),
            label: z.string(),
            icon: z.string().optional(),
          })
        ),
        edges: z.array(
          z.object({ from: z.string(), to: z.string(), label: z.string().optional() })
        ),
        highlightEdge: z.number().int().nonnegative().optional(),
      }),
    })
    .optional(),
});

// Root props passed to the ShortVideo composition
export const shortVideoSchema = z.object({
  /** Relative path to narration.mp3 inside video-renderer/public/runs/<run-id>/ */
  audioSrc: z.string(),
  scenes: z.array(scenePropSchema).min(4).max(5),
  captions: z.array(captionSchema),
  /** Optional: video title shown in Studio preview */
  title: z.string().optional(),
});

export type ShortVideoProps = z.infer<typeof shortVideoSchema>;
export type SceneProp = z.infer<typeof scenePropSchema>;
export type Caption = z.infer<typeof captionSchema>;
