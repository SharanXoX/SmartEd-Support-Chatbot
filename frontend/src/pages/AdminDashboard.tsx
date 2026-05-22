import axios from "axios";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, authHeader } from "../api/client";
import ThemeToggle from "../components/ThemeToggle";

type Analytics = {
  conversations_24h: number;
  messages_24h: number;
  tickets_open: number;
  faq_count: number;
  kb_documents: number;
};

type FAQ = {
  id: string;
  question: string;
  answer: string;
  category?: string | null;
};

type Conversation = {
  id: string;
  session_key: string;
  title?: string | null;
};

const TOKEN_KEY = "smarted_admin_token";

export default function AdminDashboard() {
  const token = useMemo(() => localStorage.getItem(TOKEN_KEY), []);
  const [jwt, setJwt] = useState<string | null>(token);
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("changeme123");

  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);

  const [faqQ, setFaqQ] = useState("How do I reset my password?");
  const [faqA, setFaqA] = useState(
    "Go to Login → Forgot password, enter your email, and follow the reset link within 15 minutes.",
  );
  const [faqCat, setFaqCat] = useState("account");

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refreshAll(auth: string | null) {
    if (!auth) return;
    setBusy(true);
    setError(null);
    try {
      const headers = authHeader(auth);
      const [a, f, c] = await Promise.all([
        api.get<Analytics>("/admin/analytics/summary", { headers }),
        api.get<FAQ[]>("/admin/faqs", { headers }),
        api.get<Conversation[]>("/admin/conversations", { headers }),
      ]);
      setAnalytics(a.data);
      setFaqs(f.data);
      setConversations(c.data);
    } catch (e) {
      if (axios.isAxiosError(e)) {
        setError(e.response?.data?.detail ?? e.message);
      } else {
        setError(e instanceof Error ? e.message : "Failed");
      }
      setJwt(null);
      localStorage.removeItem(TOKEN_KEY);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void refreshAll(jwt);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jwt]);

  async function login() {
    setBusy(true);
    setError(null);
    try {
      const { data } = await api.post<{ access_token: string }>("/auth/login", { email, password });
      localStorage.setItem(TOKEN_KEY, data.access_token);
      setJwt(data.access_token);
    } catch (e) {
      if (axios.isAxiosError(e)) {
        setError(e.response?.data?.detail ?? e.message);
      } else {
        setError(e instanceof Error ? e.message : "Login failed");
      }
    } finally {
      setBusy(false);
    }
  }

  async function createFaq() {
    if (!jwt) return;
    setBusy(true);
    setError(null);
    try {
      await api.post(
        "/admin/faqs",
        { question: faqQ, answer: faqA, category: faqCat },
        { headers: authHeader(jwt) },
      );
      await refreshAll(jwt);
    } catch (e) {
      setError(axios.isAxiosError(e) ? String(e.response?.data?.detail ?? e.message) : "FAQ error");
    } finally {
      setBusy(false);
    }
  }

  async function uploadKb(file: File | null) {
    if (!jwt || !file) return;
    const fd = new FormData();
    fd.append("file", file);
    setBusy(true);
    setError(null);
    try {
      await api.post("/admin/knowledge/upload", fd, {
        headers: { ...authHeader(jwt) },
      });
      await refreshAll(jwt);
    } catch (e) {
      setError(axios.isAxiosError(e) ? String(e.response?.data?.detail ?? e.message) : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function uploadVisual(payload: { title: string; tags: string; file: File | null }) {
    if (!jwt || !payload.file) return;
    const fd = new FormData();
    fd.append("title", payload.title);
    fd.append("tags", payload.tags);
    fd.append("file", payload.file);
    setBusy(true);
    setError(null);
    try {
      await api.post("/admin/visuals/upload", fd, {
        headers: { ...authHeader(jwt) },
      });
      await refreshAll(jwt);
    } catch (e) {
      setError(axios.isAxiosError(e) ? String(e.response?.data?.detail ?? e.message) : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setJwt(null);
    setAnalytics(null);
    setFaqs([]);
    setConversations([]);
  }

  const maxBar = Math.max(
    1,
    analytics?.conversations_24h ?? 0,
    analytics?.messages_24h ?? 0,
    analytics?.faq_count ?? 0,
    analytics?.kb_documents ?? 0,
  );

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-4">
            <Link to="/" className="text-sm font-semibold text-slate-900 hover:underline dark:text-slate-50">
              ← Site
            </Link>
            <div className="text-sm font-semibold text-slate-900 dark:text-slate-50">Admin dashboard</div>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            {jwt ? (
              <button
                type="button"
                className="rounded-lg bg-slate-900 px-3 py-2 text-xs font-semibold text-white dark:bg-white dark:text-slate-950"
                onClick={logout}
              >
                Log out
              </button>
            ) : null}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-6 py-10">
        {!jwt ? (
          <div className="mx-auto max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
            <div className="text-lg font-semibold text-slate-900 dark:text-slate-50">Sign in</div>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              Use the bootstrap admin account from your `.env` (`BOOTSTRAP_ADMIN_EMAIL` / `BOOTSTRAP_ADMIN_PASSWORD`).
            </p>

            <label className="mt-5 block text-xs font-semibold text-slate-700 dark:text-slate-200">Email</label>
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950"
            />

            <label className="mt-4 block text-xs font-semibold text-slate-700 dark:text-slate-200">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950"
            />

            {error ? <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950/40 dark:text-red-100">{error}</div> : null}

            <button
              type="button"
              disabled={busy}
              onClick={() => void login()}
              className="mt-5 w-full rounded-xl bg-brand-600 py-2 text-sm font-semibold text-white disabled:opacity-50"
            >
              {busy ? "Signing in…" : "Continue"}
            </button>

            <div className="mt-5 text-xs text-slate-500 dark:text-slate-400">
              First boot? Hit `POST /api/auth/bootstrap-first-admin` once with JSON `{email,password}` if user table is empty.
            </div>
          </div>
        ) : (
          <>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950 md:col-span-2">
                <div className="text-sm font-semibold text-slate-900 dark:text-slate-50">Analytics (24h)</div>
                <div className="mt-5 grid gap-4 md:grid-cols-2">
                  {analytics ? (
                    <>
                      <Bar label="Conversations" value={analytics.conversations_24h} max={maxBar} />
                      <Bar label="Messages" value={analytics.messages_24h} max={maxBar} />
                      <Bar label="FAQ entries" value={analytics.faq_count} max={maxBar} />
                      <Bar label="KB documents" value={analytics.kb_documents} max={maxBar} />
                      <div className="rounded-xl bg-amber-50 p-4 text-sm text-amber-950 ring-1 ring-amber-200 dark:bg-amber-950/30 dark:text-amber-50 dark:ring-amber-900 md:col-span-2">
                        Open tickets: <span className="font-semibold">{analytics.tickets_open}</span>
                      </div>
                    </>
                  ) : (
                    <div className="text-sm text-slate-600 dark:text-slate-300">{busy ? "Loading…" : "No data"}</div>
                  )}
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
                <div className="text-sm font-semibold text-slate-900 dark:text-slate-50">Upload knowledge</div>
                <p className="mt-2 text-xs text-slate-600 dark:text-slate-300">PDF/DOCX/Markdown/Text/HTML supported.</p>
                <input
                  type="file"
                  className="mt-4 block w-full text-xs"
                  onChange={(e) => void uploadKb(e.target.files?.[0] ?? null)}
                />

                <div className="mt-8 text-sm font-semibold text-slate-900 dark:text-slate-50">Upload screenshot</div>
                <VisualUploader
                  disabled={busy}
                  onUpload={(p) => void uploadVisual(p)}
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
                <div className="text-sm font-semibold text-slate-900 dark:text-slate-50">Create FAQ</div>
                <label className="mt-4 block text-xs font-semibold text-slate-700 dark:text-slate-200">Question</label>
                <textarea
                  value={faqQ}
                  onChange={(e) => setFaqQ(e.target.value)}
                  className="mt-1 min-h-[72px] w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950"
                />
                <label className="mt-4 block text-xs font-semibold text-slate-700 dark:text-slate-200">Answer</label>
                <textarea
                  value={faqA}
                  onChange={(e) => setFaqA(e.target.value)}
                  className="mt-1 min-h-[120px] w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950"
                />
                <label className="mt-4 block text-xs font-semibold text-slate-700 dark:text-slate-200">Category</label>
                <input
                  value={faqCat}
                  onChange={(e) => setFaqCat(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950"
                />
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void createFaq()}
                  className="mt-4 w-full rounded-xl bg-slate-900 py-2 text-sm font-semibold text-white disabled:opacity-50 dark:bg-white dark:text-slate-950"
                >
                  Save FAQ
                </button>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
                <div className="text-sm font-semibold text-slate-900 dark:text-slate-50">Latest conversations</div>
                <div className="mt-4 space-y-2 text-sm">
                  {conversations.map((c) => (
                    <div key={c.id} className="rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-900">
                      <div className="font-mono text-xs text-slate-500">{c.session_key}</div>
                      <div className="text-slate-800 dark:text-slate-100">{c.title ?? "(untitled)"}</div>
                    </div>
                  ))}
                  {!conversations.length ? <div className="text-slate-600 dark:text-slate-300">No conversations yet.</div> : null}
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
              <div className="text-sm font-semibold text-slate-900 dark:text-slate-50">FAQ library</div>
              <div className="mt-4 space-y-3">
                {faqs.map((f) => (
                  <div key={f.id} className="rounded-xl border border-slate-200 p-4 dark:border-slate-800">
                    <div className="text-sm font-semibold text-slate-900 dark:text-slate-50">{f.question}</div>
                    <div className="mt-2 whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-200">{f.answer}</div>
                  </div>
                ))}
                {!faqs.length ? <div className="text-sm text-slate-600 dark:text-slate-300">No FAQs yet.</div> : null}
              </div>
            </div>

            {error ? <div className="rounded-xl bg-red-50 p-4 text-sm text-red-900 dark:bg-red-950/40 dark:text-red-50">{error}</div> : null}
          </>
        )}
      </main>
    </div>
  );
}

function Bar({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = Math.round((value / max) * 100);
  return (
    <div>
      <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-300">
        <div>{label}</div>
        <div className="font-semibold text-slate-900 dark:text-slate-50">{value}</div>
      </div>
      <div className="mt-2 h-2 rounded-full bg-slate-100 dark:bg-slate-900">
        <div className="h-2 rounded-full bg-brand-600" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function VisualUploader({
  disabled,
  onUpload,
}: {
  disabled: boolean;
  onUpload: (p: { title: string; tags: string; file: File | null }) => void;
}) {
  const [title, setTitle] = useState("Account settings overview");
  const [tags, setTags] = useState("settings,navigation");

  return (
    <div className="mt-3 space-y-3">
      <input
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950"
      />
      <input
        value={tags}
        onChange={(e) => setTags(e.target.value)}
        className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-950"
      />
      <input
        type="file"
        accept="image/*"
        disabled={disabled}
        className="block w-full text-xs"
        onChange={(e) =>
          onUpload({
            title,
            tags,
            file: e.target.files?.[0] ?? null,
          })
        }
      />
    </div>
  );
}
