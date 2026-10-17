"use client";

import Link from "next/link";
import useSWR from "swr";
import { SignInButton, useUser } from "@clerk/nextjs";
import { FileText, LoaderCircle, RefreshCw, Search, TriangleAlert } from "lucide-react";
import JobCard from "@/components/JobCard";
import { getJob, listLocalJobs, saveLocalJobs } from "@/lib/api";
import { isTerminal, type Job } from "@/lib/types";

/**
 * Refresh every remembered job that has not reached a terminal state.
 * There is no "list jobs" endpoint, so the browser keeps its own list.
 */
async function refreshJobs(): Promise<Job[]> {
  const stored = listLocalJobs();
  if (stored.length === 0) return stored;

  const refreshed = await Promise.all(
    stored.map(async (job) => {
      if (isTerminal(job.status)) return job;
      try {
        return await getJob(job.job_id);
      } catch {
        return job;
      }
    }),
  );

  if (JSON.stringify(refreshed) !== JSON.stringify(stored)) {
    saveLocalJobs(refreshed);
  }

  return refreshed;
}

export default function DashboardPage() {
  const { isLoaded, isSignedIn } = useUser();

  const { data: jobs, error, isLoading, mutate } = useSWR<Job[]>("vishap:jobs", refreshJobs, {
    revalidateOnFocus: true,
    refreshInterval: (latest) =>
      latest && latest.some((job) => !isTerminal(job.status)) ? 2000 : 0,
  });

  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-10">
      <section className="flex flex-col gap-4">
        <h1 className="text-3xl font-semibold tracking-tight text-slate-100 sm:text-4xl">
          Vishap — security analysis for engineering materials
        </h1>
        <p className="max-w-2xl text-slate-400">
          Six-stage LLM pipeline with deterministic SAST/SCA, STRIDE threat modelling, an audit
          trail with SHA-256 provenance, and SARIF 2.1.0 export.
        </p>
      </section>

      {!isLoaded ? (
        <div className="mt-8 flex items-center gap-2 text-sm text-slate-500">
          <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />
          Checking your session…
        </div>
      ) : isSignedIn ? (
        <section className="mt-8 flex flex-wrap items-center gap-3">
          <Link
            href="/analyze"
            className="inline-flex items-center gap-2 rounded-lg bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 transition-colors hover:bg-sky-400"
          >
            <Search className="h-4 w-4" aria-hidden="true" />
            New analysis
          </Link>
          <button
            type="button"
            onClick={() => void mutate()}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-700 px-4 py-2 text-sm text-slate-300 transition-colors hover:border-slate-600 hover:text-slate-100"
          >
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Refresh
          </button>
        </section>
      ) : (
        <section className="mt-8 rounded-xl border border-slate-800 bg-slate-900/50 p-6">
          <h2 className="text-lg font-medium text-slate-100">Sign in to run an analysis</h2>
          <p className="mt-1 max-w-xl text-sm text-slate-400">
            Analyses are tied to your account. Sign in with Clerk to upload material and read the
            generated report.
          </p>
          <div className="mt-4">
            <SignInButton mode="modal">
              <button
                type="button"
                className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 transition-colors hover:bg-sky-400"
              >
                Sign in
              </button>
            </SignInButton>
          </div>
        </section>
      )}

      <section className="mt-10">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium text-slate-100">Recent analyses</h2>
          {isLoading ? (
            <span className="flex items-center gap-1.5 text-xs text-slate-500">
              <LoaderCircle className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
              Loading
            </span>
          ) : null}
        </div>

        <div className="mt-4 flex flex-col gap-3">
          {error ? (
            <p className="flex items-start gap-2 rounded-xl border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-200">
              <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
              <span>{error instanceof Error ? error.message : "Could not load jobs."}</span>
            </p>
          ) : null}

          {!error && jobs && jobs.length === 0 ? (
            <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-slate-800 px-6 py-12 text-center">
              <FileText className="h-6 w-6 text-slate-600" aria-hidden="true" />
              <p className="text-sm text-slate-400">No analyses yet.</p>
              <p className="text-xs text-slate-600">
                Jobs you submit from this browser will appear here.
              </p>
            </div>
          ) : null}

          {jobs?.map((job) => <JobCard key={job.job_id} job={job} />)}
        </div>
      </section>
    </div>
  );
}
