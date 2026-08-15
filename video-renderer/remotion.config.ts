/**
 * Remotion configuration for yt-agent video renderer.
 * Tailwind is removed — this project uses inline styles for deterministic rendering.
 * All configuration options: https://remotion.dev/docs/config
 */

import { Config } from "@remotion/cli/config";

Config.setRspack(true);
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
