import {
  Smartphone,
  Monitor,
  Server,
  Database,
  Cloud,
  User,
  Lock,
  Shield,
  Globe2,
  Code2,
  GitBranch,
  MessageSquare,
  Zap,
  Activity,
} from "lucide-react";

export const iconRegistry = {
  smartphone: Smartphone,
  monitor: Monitor,
  server: Server,
  database: Database,
  cloud: Cloud,
  user: User,
  lock: Lock,
  shield: Shield,
  globe: Globe2,
  code: Code2,
  gitBranch: GitBranch,
  message: MessageSquare,
  zap: Zap,
  activity: Activity,
} as const;

export type SupportedIcon = keyof typeof iconRegistry;

export default iconRegistry;
