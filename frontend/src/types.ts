import { isAllowedVisualWorkflow } from "./lib/visualWorkflowAllowlist";

export type Annotation = {
  kind: "circle" | "arrow" | "highlight" | "label";
  x: number;
  y: number;
  w: number;
  h: number;
  label?: string | null;
};

export type NavigationAction = {
  label: string;
  path: string;
};

export type VisualStep = {
  step: number;
  title: string;
  description: string;
  image_url?: string | null;
  /** API may send `image` — normalized in the client */
  image?: string | null;
  open_url?: string | null;
  auto_navigate?: boolean;
  annotations?: Annotation[];
};

export type ChatTurnResponse = {
  reply: string;
  intent: string;
  confidence: number;
  visual_steps: VisualStep[];
  suggested_replies: string[];
  escalate: boolean;
  follow_up_question?: string | null;
  citations: { title: string; snippet: string }[];
  response_source?: "support_flow" | "llm" | "fallback" | "navigation";
  response_type?: "support_flow" | "llm" | "fallback" | "navigation";
  response_mode?: string | null;
  flow_title?: string | null;
  matched_flow_intent?: string | null;
  intent_match_confidence?: number | null;
  navigation_actions?: NavigationAction[];
};

export function isNavigationOnly(meta?: ChatTurnResponse | null): boolean {
  if (!meta) return false;
  const t = meta.response_type ?? meta.response_source;
  if (t === "navigation") return true;
  const steps = meta.visual_steps ?? [];
  return Boolean(meta.navigation_actions?.length && steps.length === 0);
}

export function isVisualWalkthrough(meta?: ChatTurnResponse | null): boolean {
  if (!meta) return false;
  if (isNavigationOnly(meta)) return false;
  const steps = meta.visual_steps ?? [];
  if (steps.length === 0) return false;
  const intent = meta.matched_flow_intent ?? meta.intent;
  if (!isAllowedVisualWorkflow(intent)) return false;
  const t = meta.response_type ?? meta.response_source;
  if (t === "support_flow") return true;
  return Boolean(normalized && steps.length > 0);
}
