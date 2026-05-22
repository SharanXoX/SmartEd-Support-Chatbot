/** Must match backend ALLOWED_VISUAL_WORKFLOWS in visual_workflow_allowlist.py */
export const ALLOWED_VISUAL_WORKFLOWS = new Set<string>(["password_reset"]);

export function isAllowedVisualWorkflow(intent: string | null | undefined): boolean {
  if (!intent) return false;
  const key = intent.trim().toLowerCase();
  if (key === "reset_password") return true;
  return ALLOWED_VISUAL_WORKFLOWS.has(key);
}
