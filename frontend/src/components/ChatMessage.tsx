import { useChat } from "../context/ChatContext";
import type { ChatTurnResponse } from "../types";
import { isNavigationOnly, isVisualWalkthrough } from "../types";
import NavigationActions from "./NavigationActions";
import SupportFlow from "./SupportFlow";
import VisualGuideCarousel from "./VisualGuideCarousel";

function formatInlineBold(text: string, strongClassName: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    const m = part.match(/^\*\*(.+)\*\*$/);
    if (m) {
      return (
        <strong key={i} className={strongClassName}>
          {m[1]}
        </strong>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

type Props = {
  role: "user" | "assistant";
  content: string;
  meta?: ChatTurnResponse | null;
};

function walkthroughIntroText(content: string, walkthrough: boolean): string {
  if (!walkthrough || !content.trim()) return content;
  if (!/Step\s+\d+\s+of\s+\d+:/i.test(content)) return content;
  const first = content.split(/\r?\n/)[0]?.trim() ?? "";
  return first || content;
}

export default function ChatMessage({ role, content, meta }: Props) {
  const { navigateTo, currentRoute } = useChat();
  const isUser = role === "user";
  const navOnly = !isUser && isNavigationOnly(meta);
  const walkthrough = !isUser && isVisualWalkthrough(meta);
  const steps = meta?.visual_steps ?? [];
  const displayContent = walkthroughIntroText(content, walkthrough);
  const navActions = meta?.navigation_actions ?? [];

  return (
    <div className={isUser ? "flex justify-end" : "flex justify-start"}>
      <div
        className={
          isUser
            ? "max-w-[92%] rounded-2xl bg-violet-700 px-3 py-2 text-sm font-medium leading-relaxed text-white shadow-sm"
            : "max-w-[92%] rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium leading-relaxed text-slate-800 shadow-sm"
        }
      >
        {displayContent ? (
          <div className="whitespace-pre-wrap text-inherit">
            {isUser
              ? displayContent
              : formatInlineBold(displayContent, "font-semibold text-slate-900")}
          </div>
        ) : null}

        {navOnly ? (
          <div className="mt-2 inline-flex rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-emerald-900 ring-1 ring-emerald-600/25">
            Navigating in app
          </div>
        ) : null}

        {!isUser && navActions.length > 0 ? (
          <NavigationActions actions={navActions} onNavigate={navigateTo} currentRoute={currentRoute} />
        ) : null}

        {walkthrough ? (
          <div className="mt-2 inline-flex rounded-full bg-violet-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-violet-900 ring-1 ring-violet-300/50">
            Visual walkthrough
            {meta?.flow_title ? (
              <span className="ml-1 normal-case font-semibold text-violet-800">· {meta.flow_title}</span>
            ) : null}
          </div>
        ) : null}

        {walkthrough && steps.length > 0 ? (
          <SupportFlow
            steps={steps}
            matchedIntent={meta?.matched_flow_intent}
            intentConfidence={meta?.intent_match_confidence}
            onNavigate={navigateTo}
            currentRoute={currentRoute}
          />
        ) : null}

        {!walkthrough && !isUser && steps.length > 0 ? (
          <VisualGuideCarousel steps={steps} />
        ) : null}

        {!isUser && meta?.follow_up_question ? (
          <div className="mt-2 rounded-lg bg-slate-50 p-2 text-xs font-medium leading-relaxed text-slate-800 ring-1 ring-slate-200">
            <span className="font-semibold text-slate-900">Follow-up:</span> {meta.follow_up_question}
          </div>
        ) : null}

        {!isUser && meta?.escalate ? (
          <div className="mt-2 rounded-lg bg-amber-50 p-2 text-xs font-medium leading-relaxed text-amber-950 ring-1 ring-amber-300">
            I've flagged this for a human specialist. If urgent, email support from your account settings.
          </div>
        ) : null}

        {!isUser && meta?.citations?.length ? (
          <div className="mt-2 space-y-1 text-[11px] leading-relaxed text-slate-700">
            {meta.citations.slice(0, 3).map((c, idx) => (
              <div key={idx}>
                <span className="font-semibold text-slate-900">{c.title}:</span> {c.snippet}
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
