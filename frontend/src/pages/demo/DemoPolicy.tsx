import { Link, useParams } from "react-router-dom";

const POLICIES: Record<string, { title: string; body: string }> = {
  refund: {
    title: "Refund Policy",
    body: "Refunds for paid courses may be requested within 14 days of purchase if less than 20% of content has been completed. Processing takes 5–10 business days after approval.",
  },
  grading: {
    title: "Grading Policy",
    body: "Assignments are graded using published rubrics. Late work may incur penalties unless an extension is approved. Final grades appear in Progress and the course gradebook.",
  },
  attendance: {
    title: "Attendance Policy",
    body: "Complete linked activities or watch 80% of live recordings to mark attendance. Extended inactivity may trigger a wellness check-in email from your instructor.",
  },
};

export default function DemoPolicy() {
  const { policyId } = useParams();
  const policy = POLICIES[policyId ?? ""] ?? {
    title: "Policy",
    body: "This demo policy page is a placeholder for full terms in the real LMS.",
  };

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <Link to="/demo/dashboard" className="text-sm font-medium text-brand-600 hover:underline">
        ← Back to dashboard
      </Link>
      <article className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="text-xl font-semibold">{policy.title}</h2>
        <p className="mt-4 text-sm leading-relaxed text-slate-700 dark:text-slate-200">{policy.body}</p>
        <p className="mt-6 text-xs text-slate-500">Demo only — not legal advice.</p>
      </article>
    </div>
  );
}
