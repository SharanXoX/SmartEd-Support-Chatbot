import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef } from "react";
import { useChat } from "../context/ChatContext";
import { QUICK_ACTIONS } from "../registry/lmsRegistry";
import ChatMessage from "./ChatMessage";
import TicketModal from "./TicketModal";

export default function FloatingChat() {
  const {
    open,
    setOpen,
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
    navigateTo,
    currentRoute,
    latestSuggestions,
  } = useChat();

  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, open, streamingText]);

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-3">
      <AnimatePresence>
        {open ? (
          <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 16, scale: 0.98 }}
            className="floating-chat-panel flex h-[560px] w-[380px] max-w-[calc(100vw-2.5rem)] flex-col overflow-hidden rounded-2xl border border-slate-300 bg-white text-slate-800 shadow-2xl"
          >
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
              <div>
                <div className="text-sm font-semibold text-slate-900">Learning support</div>
                <div className="text-xs font-medium text-slate-600">
                  Visual guides · navigates with you
                </div>
              </div>
              <button
                type="button"
                className="rounded-full px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900"
                onClick={() => setOpen(false)}
              >
                Close
              </button>
            </div>

            <div className="floating-chat-messages flex-1 space-y-3 overflow-y-auto bg-slate-50/80 px-4 py-3">
              {msgs.map((m) => (
                <ChatMessage key={m.id} role={m.role} content={m.content} meta={m.meta} />
              ))}

              {streamingText !== null ? (
                <div className="flex justify-start">
                  <div className="max-w-[92%] rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium leading-relaxed text-slate-800 shadow-sm">
                    <div className="whitespace-pre-wrap">{streamingText}</div>
                  </div>
                </div>
              ) : null}

              <div ref={bottomRef} />
            </div>

            {latestSuggestions.length ? (
              <div className="flex flex-wrap gap-2 border-t border-slate-200 bg-white px-4 py-2">
                {latestSuggestions.map((s) => (
                  <button
                    key={s}
                    type="button"
                    className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-800 shadow-sm hover:border-violet-300 hover:bg-violet-50 hover:text-violet-900"
                    onClick={() => setInput(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            ) : null}

            <div className="flex max-h-24 flex-wrap gap-1.5 overflow-y-auto border-t border-slate-200 bg-white px-4 py-2">
              {QUICK_ACTIONS.map((a) => (
                <button
                  key={a.label}
                  type="button"
                  disabled={busy}
                  onClick={() => {
                    if ("navigateTo" in a && a.navigateTo) navigateTo(a.navigateTo);
                    void sendMessage(a.message);
                  }}
                  className="rounded-full border border-violet-200 bg-violet-50 px-2.5 py-1 text-[11px] font-semibold text-violet-900 hover:border-violet-300 hover:bg-violet-100 disabled:opacity-50"
                >
                  {a.label}
                </button>
              ))}
            </div>

            <div className="flex gap-2 border-t border-slate-200 bg-white p-3">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void send();
                }}
                placeholder="Describe what you're trying to do…"
                className="floating-chat-input flex-1 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-800 placeholder:text-slate-500 placeholder:font-normal outline-none ring-violet-600 focus:ring-2"
              />
              <button
                type="button"
                disabled={busy}
                onClick={() => void send()}
                className="rounded-xl bg-violet-700 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-violet-800 disabled:opacity-50"
              >
                Send
              </button>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>

      <motion.button
        type="button"
        layout
        onClick={() => setOpen((v) => !v)}
        className="rounded-full bg-violet-700 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-violet-700/30"
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.98 }}
      >
        Need help?
      </motion.button>

      <TicketModal
        open={ticketOpen}
        onClose={() => setTicketOpen(false)}
        sessionKey={sk}
        defaultName={studentName !== "there" ? studentName : ""}
        defaultEmail={studentEmail ?? ""}
      />
    </div>
  );
}
