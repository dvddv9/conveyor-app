"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import useSWR from "swr";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { ArrowLeft, Download, LoaderCircle, TriangleAlert } from "lucide-react";
import { ApiError, getReport } from "@/lib/api";
import type { Report } from "@/lib/types";

function ReportInner() {
  const params = useParams();
  const jobId = typeof params?.id === "string" ? params.id : "";

  const { data: report, error } = useSWR<Report>(
    jobId ? ["report", jobId] : null,
    () => getReport(jobId),
    {
      // `GET /report/{id}` answers 409 until the job is done — keep retrying.
      refreshInterval: (latest) => (latest ? 0 : 3000),
      shouldRetryOnError: true,
      errorRetryInterval: 3000,
      revalidateOnFocus: false,
    },
  );

  const isStillRunning = error instanceof ApiError && error.status === 409;
  const isMissing = error instanceof ApiError && error.status === 404;

  function handleExport() {
    if (!report) return;
    const blob = new Blob([report.final_markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${report.filename.replace(/\.[^.]+$/, "") || "report"}-vishap.md`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  const verdict = report?.audit?.risk_verdict ?? report?.critique_verdict ?? null;

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-10">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-slate-400 transition-colors hover:text-slate-200"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to dashboard
        </Link>

        <div className="flex items-center gap-2">
          {report ? (
            <button
              type="button"
              onClick={handleExport}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-sm text-slate-200 transition-colors hover:border-sky-500 hover:text-sky-300"
            >
              <Download className="h-4 w-4" aria-hidden="true" />
              Export .md
            </button>
          ) : null}
        </div>
      </div>

      {report ? (
        <header className="mb-6">
          <h1 className="truncate font-mono text-xl text-slate-100" title={report.filename}>
            {report.filename}
          </h1>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <span className="font-mono">{report.session_id}</span>
            {verdict ? (
              <span className="badge badge-running" title="Risk verdict">
                {verdict}
              </span>
            ) : null}
            {typeof report.cost_usd === "number" ? (
              <span>${report.cost_usd.toFixed(4)}</span>
            ) : null}
          </div>
        </header>
      ) : null}

      {!report && isStillRunning ? (
        <div className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-900/50 px-4 py-6 text-sm text-slate-400">
          <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />
          The analysis is still running — this page updates automatically.
        </div>
      ) : null}

      {!report && isMissing ? (
        <p className="rounded-xl border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          Job <span className="font-mono">{jobId}</span> was not found.
        </p>
      ) : null}

      {!report && error && !isStillRunning && !isMissing ? (
        <p className="flex items-start gap-2 rounded-xl border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{error instanceof Error ? error.message : "Could not load the report."}</span>
        </p>
      ) : null}

      {!report && !error ? (
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />
          Loading report…
        </div>
      ) : null}

      {report ? (
        <article className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{report.final_markdown}</ReactMarkdown>
          </div>
        </article>
      ) : null}
    </div>
  );
}


export default function ReportPage() {
  return (
    <Suspense fallback={<div className="p-8">Loading report...</div>}>
      <ReportInner />
    </Suspense>
  );
}
