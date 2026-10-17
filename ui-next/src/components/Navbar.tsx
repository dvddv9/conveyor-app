"use client";

import { Suspense } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { SignInButton, UserButton, useUser } from "@clerk/nextjs";
import { ExternalLink, LayoutDashboard, Search } from "lucide-react";

const NAV_LINKS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/analyze", label: "Analyze", icon: Search },
];

const DOCS_URL = "https://dvddv9.github.io/vishap/";

function NavbarInner() {
  const pathname = usePathname();
  const { isLoaded, isSignedIn } = useUser();

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/85 backdrop-blur">
      <nav className="mx-auto flex h-14 w-full max-w-6xl items-center gap-1 px-4">
        <Link
          href="/"
          className="mr-3 flex items-center gap-2 text-base font-semibold tracking-tight text-slate-100 transition-colors hover:text-white"
        >
          <span aria-hidden="true">🐉</span>
          <span>Vishap</span>
        </Link>

        {NAV_LINKS.map(({ href, label, icon: Icon }) => {
          const isActive = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              aria-current={isActive ? "page" : undefined}
              className={`flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm transition-colors ${
                isActive
                  ? "bg-slate-800/80 text-slate-100"
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
              }`}
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">{label}</span>
            </Link>
          );
        })}

        <a
          href={DOCS_URL}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-slate-400 transition-colors hover:bg-slate-800/50 hover:text-slate-200"
        >
          <ExternalLink className="h-4 w-4" aria-hidden="true" />
          <span className="hidden sm:inline">Docs</span>
        </a>

        <div className="ml-auto flex items-center gap-2">
          {!isLoaded ? (
            <span className="h-8 w-8" aria-hidden="true" />
          ) : isSignedIn ? (
            <UserButton />
          ) : (
            <SignInButton mode="modal">
              <button
                type="button"
                className="rounded-md bg-sky-500 px-3 py-1.5 text-sm font-medium text-slate-950 transition-colors hover:bg-sky-400"
              >
                Sign in
              </button>
            </SignInButton>
          )}
        </div>
      </nav>
    </header>
  );
}


export default function Navbar() {
  return (
    <Suspense fallback={<nav className="p-4">Loading...</nav>}>
      <NavbarInner />
    </Suspense>
  );
}
