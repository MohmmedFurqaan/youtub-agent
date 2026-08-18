/**
 * config/SoundConfig.ts
 *
 * Maps animation events and scene transitions to sound-effect cues.
 * Used by Remotion <Audio> + <Sequence> (server-side rendering & studio preview).
 *
 * Sound files live in `video-renderer/public/sounds/` so that
 * Remotion's `staticFile()` can resolve them for rendering.
 */

import { staticFile } from "remotion";

export type SoundName =
  | "ui/pop_open"
  | "ui/pop_close"
  | "ui/buzz"
  | "ui/button_squishy"
  | "ui/toggle_on"
  | "ui/item_select"
  | "ui/success_chime"
  | "arcade/coin";

export interface SoundDef {
  name: SoundName;
  src: string;
  volume: number;
  description: string;
}

/** All available sound effects */
export const SOUND_LIBRARY: Record<SoundName, SoundDef> = {
  "ui/pop_open": {
    name: "ui/pop_open",
    src: staticFile("sounds/ui/pop_open.mp3"),
    volume: 0.35,
    description: "Energetic pop — scene enter, zoom-punch transition",
  },
  "ui/pop_close": {
    name: "ui/pop_close",
    src: staticFile("sounds/ui/pop_close.mp3"),
    volume: 0.3,
    description: "Soft pop — fade transition, diagram step reveal",
  },
  "ui/buzz": {
    name: "ui/buzz",
    src: staticFile("sounds/ui/buzz.mp3"),
    volume: 0.4,
    description: "Glitch buzz — glitch transition",
  },
  "ui/button_squishy": {
    name: "ui/button_squishy",
    src: staticFile("sounds/ui/button_squishy.mp3"),
    volume: 0.35,
    description: "Soft squish — slide transition, packet arrival",
  },
  "ui/toggle_on": {
    name: "ui/toggle_on",
    src: staticFile("sounds/ui/toggle_on.mp3"),
    volume: 0.25,
    description: "Click toggle — cut transition, node highlight",
  },
  "ui/item_select": {
    name: "ui/item_select",
    src: staticFile("sounds/ui/item_select.mp3"),
    volume: 0.3,
    description: "Item select — diagram reveal, node appearance",
  },
  "ui/success_chime": {
    name: "ui/success_chime",
    src: staticFile("sounds/ui/success_chime.mp3"),
    volume: 0.35,
    description: "Ascending chime — key insight scene, metric reveal",
  },
  "arcade/coin": {
    name: "arcade/coin",
    src: staticFile("sounds/arcade/coin.mp3"),
    volume: 0.25,
    description: "Coin pickup — flow event packet arrival",
  },
};

/** Maps a scene transition type to its sound effect */
export const TRANSITION_SOUND: Record<string, SoundName> = {
  cut: "ui/toggle_on",
  fade: "ui/pop_close",
  slide: "ui/button_squishy",
  "zoom-punch": "ui/pop_open",
  glitch: "ui/buzz",
};

/** Maps a story_role to its sound effect (for scene entry) */
export const STORY_ROLE_SOUND: Record<string, SoundName> = {
  hook: "ui/pop_open",
  problem: "ui/buzz",
  explanation: "ui/item_select",
  mechanism: "ui/button_squishy",
  "key insight": "ui/success_chime",
};

/** Maps a SceneEvent type to its sound effect (for diagram animations) */
export const EVENT_SOUND: Record<string, SoundName> = {
  flow: "arcade/coin",
  response: "arcade/coin",
  reveal: "ui/item_select",
  comparison: "ui/pop_close",
  sequence: "ui/item_select",
  metric: "ui/success_chime",
};
