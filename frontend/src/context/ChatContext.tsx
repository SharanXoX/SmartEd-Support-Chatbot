import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useLocation, useNavigate } from "react-router-dom";
import type { ChatTurnResponse, VisualStep } from "../types";
import { isNavigationOnly, isVisualWalkthrough } from "../types";
import { api } from "../api/client";
import { useLmsState } from "./LmsStateContext";
import { QUICK_ACTIONS, TICKET_TRIGGER } from "../registry/lmsRegistry";
import { matchClientNavigation } from "../lib/clientNavigation";
import { normalizeDemoPath } from "../lib/navigation";

function welcomeMessage(name: string): string {
  return `Hi ${name} — I'm your learning support assistant. I can guide you with screenshots and open pages in the platform as we go. What do you need help with?`;
}

export type ChatMsg = {
  id: string;
  role: "user" | "assistant";
  content: string;
  meta?: ChatTurnResponse | null;
};

function normalizeVisualStep(s: VisualStep & { image?: string | null }): VisualStep {
  const imageUrl = s.image_url ?? s.image ?? null;
  return {
    ...s,
    image_url: imageUrl && String(imageUrl).trim() ? String(imageUrl) : null,
    open_url: normalizeDemoPath(s.open_url ?? null) ?? s.open_url ?? null,
    auto_navigate: Boolean(s.auto_navigate),
    annotations: s.annotations ?? [],
  };
}

function normalizeTurn(raw: ChatTurnResponse): ChatTurnResponse {
  const steps: VisualStep[] = (raw.visual_steps ?? []).map((s) =>
    normalizeVisualStep(s as VisualStep & { image?: string | null }),
  );
  const source = raw.response_source ?? raw.response_type ?? "llm";
  const isFlow = source === "support_flow";
  const nav = (raw.navigation_actions ?? []).map((a) => ({
    label: a.label,
    path: normalizeDemoPath(a.path) ?? a.path,
  }));
  return {
    ...raw,
    visual_steps: steps,
    navigation_actions: nav,
    response_source: isFlow ? "support_flow" : source,
    response_type: raw.response_type ?? (isFlow ? "support_flow" : source),
    flow_title: raw.flow_title ?? null,
    matched_flow_intent: raw.matched_flow_intent ?? null,
    intent_match_confidence:
      raw.intent_match_confidence === undefined ? null : raw.intent_match_confidence,
  };
}

function chatSessionKeyForUser(userId: string): string {
  const storageKey = `smarted_chat_session_${userId}`;
  let v = sessionStorage.getItem(storageKey);
  if (!v) {
    v = crypto.randomUUID().replace(/-/g, "").slice(0, 16);
    sessionStorage.setItem(storageKey, v);
  }
  return v;
}

type ChatContextValue = {
  open: boolean;
  setOpen: (v: boolean) => void;
  toggleOpen: () => void;
  msgs: ChatMsg[];
  busy: boolean;
  streamingText: string | null;
  input: string;
  setInput: (v: string) => void;
  send: () => void;
  sendMessage: (text: string) => Promise<void>;
  ticketOpen: boolean;
  setTicketOpen: (v: boolean) => void;
  sessionKey: string;
  studentName: string;
  studentEmail?: string;
  setStudentProfile: (name: string, email?: string) => void;
  navigateTo: (path: string) => void;
  currentRoute: string;
  latestSuggestions: string[];
};

const ChatContext = createContext<ChatContextValue | null>(null);

export function ChatProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const currentRoute = location.pathname;
  const { buildContextSnapshot, state, activeStudentId } = useLmsState();

  const [studentName, setStudentName] = useState(state.name);
  const [studentEmail, setStudentEmail] = useState<string | undefined>(state.email);
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [ticketOpen, setTicketOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [streamingText, setStreamingText] = useState<string | null>(null);
  const [msgs, setMsgs] = useState<ChatMsg[]>([
    {
      id: "welcome",
      role: "assistant",
      content: welcomeMessage(state.name),
      meta: null,
    },
  ]);

  const sk = useMemo(
    () => chatSessionKeyForUser(activeStudentId || state.student_id),
    [activeStudentId, state.student_id],
  );
  const lastAutoNavRef = useRef<string | null>(null);

  useEffect(() => {
    setStudentName(state.name);
    setStudentEmail(state.email);
    lastAutoNavRef.current = null;
    setInput("");
    setMsgs([
      {
        id: "welcome",
        role: "assistant",
        content: welcomeMessage(state.name),
        meta: null,
      },
    ]);
  }, [activeStudentId, state.student_id, state.name, state.email]);

  const setStudentProfile = useCallback((name: string, email?: string) => {
    setStudentName(name);
    setStudentEmail(email);
  }, []);

  const navigateTo = useCallback(
    (path: string) => {
      const normalized = normalizeDemoPath(path);
      if (!normalized || normalized === currentRoute) return;
      navigate(normalized);
      setOpen(true);
    },
    [navigate, currentRoute],
  );

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || busy) return;

      if (TICKET_TRIGGER.test(text)) {
        setTicketOpen(true);
        setMsgs((prev) => [
          ...prev,
          { id: crypto.randomUUID(), role: "user", content: text },
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content:
              "I'll connect you with our support team. Please fill in the short form so we can follow up by email.",
            meta: null,
          },
        ]);
        return;
      }

      setBusy(true);
      setStreamingText(null);
      const userMsg: ChatMsg = { id: crypto.randomUUID(), role: "user", content: text };
      setMsgs((prev) => [...prev, userMsg]);

      try {
        const resp = await api.post<ChatTurnResponse>("/chat/turn", {
          session_key: sk,
          message: text,
          current_route: currentRoute,
          lms_context: buildContextSnapshot(),
        });
        const data = normalizeTurn(resp.data);
        const walkthrough = isVisualWalkthrough(data);
        let navOnly = isNavigationOnly(data);
        let navPath =
          normalizeDemoPath(data.navigation_actions?.[0]?.path) ??
          normalizeDemoPath(data.visual_steps?.[0]?.open_url);

        if (!navOnly && !walkthrough) {
          const clientPath = matchClientNavigation(text);
          if (clientPath && clientPath !== currentRoute) {
            navOnly = true;
            navPath = clientPath;
            data.navigation_actions = [{ label: "Open page", path: clientPath }];
            data.response_type = "navigation";
            data.response_source = "navigation";
          }
        }

        if (navOnly) {
          const navKey = `nav-${navPath}`;
          if (navPath && lastAutoNavRef.current !== navKey) {
            lastAutoNavRef.current = navKey;
            navigate(navPath);
          }
          setStreamingText(null);
        } else if (!walkthrough) {
          setStreamingText("");
          const words = data.reply.split(/(\s+)/);
          let acc = "";
          for (const w of words) {
            acc += w;
            setStreamingText(acc);
            await new Promise((r) => window.setTimeout(r, 8));
          }
          setStreamingText(null);
        } else {
          const autoStep = data.visual_steps.find((s) => s.auto_navigate && s.open_url);
          const autoPath = normalizeDemoPath(autoStep?.open_url ?? null);
          const autoKey = `${data.matched_flow_intent}-${autoPath}`;
          if (autoPath && lastAutoNavRef.current !== autoKey) {
            lastAutoNavRef.current = autoKey;
            navigate(autoPath);
          }
        }

        setMsgs((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: data.reply,
            meta: data,
          },
        ]);
      } catch (e) {
        const detail = e instanceof Error ? e.message : "Request failed";
        setStreamingText(null);
        setMsgs((prev) => [
          ...prev,
          { id: crypto.randomUUID(), role: "assistant", content: `Sorry — ${detail}`, meta: null },
        ]);
      } finally {
        setBusy(false);
      }
    },
    [busy, sk, currentRoute, navigate, buildContextSnapshot],
  );

  const send = useCallback(() => {
    const text = input.trim();
    if (!text) return;
    setInput("");
    void sendMessage(text);
  }, [input, sendMessage]);

  const latestSuggestions = useMemo(
    () =>
      [...msgs]
        .reverse()
        .find((m) => m.role === "assistant" && m.meta?.suggested_replies?.length)?.meta
        ?.suggested_replies ?? [],
    [msgs],
  );

  const value: ChatContextValue = {
    open,
    setOpen,
    toggleOpen: () => setOpen((v) => !v),
    msgs,
    busy,
    streamingText,
    input,
    setInput,
    send,
    sendMessage,
    ticketOpen,
    setTicketOpen,
    sessionKey: sk,
    studentName,
    studentEmail,
    setStudentProfile,
    navigateTo,
    currentRoute,
    latestSuggestions,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error("useChat must be used within ChatProvider");
  return ctx;
}
