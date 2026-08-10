// ─── Type Definitions ──────────────────────────────────────────────────────
// Faceless video format — no characters, no speaker.
// Narration is delivered by a single invisible narrator via TTS.

export interface Scene {
  scene_number: number;
  /** The exact words the narrator speaks — used for word-by-word captions */
  narration: string;
  /** 1–4 word keyword badge shown at the top of the frame */
  on_screen_text: string;
  /** Static path served via video-renderer/public/ (e.g. "metadata/scene/scene1_bg.png") */
  background_image: string;
  /** Static path to the TTS MP3 (e.g. "metadata/scene/scene1.mp3") */
  audio_file: string;
  /** Duration of the scene in Remotion frames (audio length × fps) */
  duration_in_frames: number;
}

export interface VideoProps extends Record<string, unknown> {
  title: string;
  fps: number;
  scenes: Scene[];
  total_duration_frames: number;
}
