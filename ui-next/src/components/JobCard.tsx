import Link from "next/link";
import { CircleCheckBig, CircleX, Clock, LoaderCircle, TriangleAlert } from "lucide-react";
import type { Job, JobStatus } from "@/lib/types";

const STATUS_META: Record<
  JobStatus,
  { label: string; emoji: string; badge: string; icon: typeof Clock }
> = {
  queued: { label: "Queued", emoji: "🟡", badge: "badge badge-queued", icon: Clock },
  running: { label: "Running", emoji: "🔵", badge: "badge badge-running", icon: LoaderCircle },
  done: { label: "Done", emoji: "🟢", badge: "badge badge-done", icon: CircleCheckBig },
  failed: { label: "Failed", emoji: "🔴", badge: "badge badge-failed", icon: CircleX },
};

function formatTimestamp(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export default function JobCard({ job }: { job: Job }) {
  const meta = STATUS_META[job.status] ?? STATUS_META.queued;
  const Icon = meta.icon;

  return (
    <article className="flex flex-col gap-3 rounded-xl border border-slate-800 bg-slate-900/50 p-4 transition-colors hover:border-slate-700 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className={meta.badge}>
            <Icon className="h-3.5 w-3.5" aria-hidden="true" />
            {meta.label}
          </span>
          <h3 className="truncate font-mono text-sm text-slate-200" title={job.filename}>
            {job.filename}
          </h3>
        </div>
        <p className="mt-1.5 text-xs text-slate-500">
          Created {formatTimestamp(job.created_at)}
          {job.finished_at ? ` · finished ${formatTimestamp(job.finished_at)}` : ""}
        </p>
        {job.status === "failed" && job.error ? (
          <p className="mt-1.5 flex items-start gap-1.5 text-xs text-red-300">
            <TriangleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <span className="break-words">{job.error}</span>
          </p>
        ) : null}
      </div>

      <div className="flex shrink-0 items-center gap-2">
        {job.status === "done" ? (
          <Link
            href={`/report/${job.job_id}`}
            className="rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-200 transition-colors hover:border-sky-500 hover:text-sky-300"
          >
            View
          </Link>
        ) : (
          <Link
            href={`/report/${job.job_id}`}
            className="rounded-md border border-slate-800 px-3 py-1.5 text-sm text-slate-500 transition-colors hover:border-slate-700 hover:text-slate-300"
          >
            Open
          </Link>
        )}
        <span className="hidden font-mono text-[0.7rem] text-slate-600 sm:inline">
          {job.job_id.slice(0, 8)}
        </span>
      </div>
    </article>
  );
}
