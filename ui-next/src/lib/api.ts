import type { AnalyzeResponse, Job, Report } from "./types";

/** Base URL of the FastAPI backend. */
export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5001").replace(
  /\/+$/,
  "",
);

/** Optional key — the backend only enforces it when VISHAP_API_KEY is set. */
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function detailFrom(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    return typeof detail === "string" ? detail : JSON.stringify(detail);
  }
  return fallback;
}

/** Thin fetch wrapper: JSON in/out, `X-API-Key`, readable errors. */
export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (API_KEY) {
    headers.set("X-API-Key", API_KEY);
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers, cache: "no-store" });
  } catch {
    throw new ApiError(`Cannot reach the Vishap API at ${API_URL}. Is the backend running?`, 0);
  }

  const raw = await response.text();
  let body: unknown = null;
  if (raw) {
    try {
      body = JSON.parse(raw);
    } catch {
      body = raw;
    }
  }

  if (!response.ok) {
    throw new ApiError(
      detailFrom(body, `Request failed with HTTP ${response.status}`),
      response.status,
    );
  }

  return body as T;
}

export function submitAnalysis(material: string, filename: string): Promise<AnalyzeResponse> {
  return apiFetch<AnalyzeResponse>("/analyze/async", {
    method: "POST",
    body: JSON.stringify({ material, filename }),
  });
}

export function getJob(jobId: string): Promise<Job> {
  return apiFetch<Job>(`/status/${encodeURIComponent(jobId)}`);
}

export function getReport(jobId: string): Promise<Report> {
  return apiFetch<Report>(`/report/${encodeURIComponent(jobId)}`);
}

/* -------------------------------------------------------------------------- *
 * Local job cache
 *
 * The backend has no "list jobs" endpoint (`/status/list` does not exist), so
 * the dashboard remembers the jobs this browser submitted and refreshes each
 * one through `GET /status/{id}`.
 * -------------------------------------------------------------------------- */

const STORAGE_KEY = "vishap.jobs.v1";
const MAX_REMEMBERED = 50;

export function listLocalJobs(): Job[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as Job[]) : [];
  } catch {
    return [];
  }
}

export function saveLocalJobs(jobs: Job[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(jobs.slice(0, MAX_REMEMBERED)));
  } catch {
    /* storage full or disabled — the dashboard still works, it just forgets */
  }
}

export function rememberJob(job: Job): void {
  const others = listLocalJobs().filter((item) => item.job_id !== job.job_id);
  saveLocalJobs([job, ...others]);
}

export function forgetJob(jobId: string): void {
  saveLocalJobs(listLocalJobs().filter((item) => item.job_id !== jobId));
}
