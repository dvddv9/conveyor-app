import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

/**
 * Clerk auth gate.
 *
 * Next.js 16 renamed the `middleware` file convention to `proxy` (same API,
 * the old name logs a deprecation warning), so this lives in `src/proxy.ts`.
 */
const isProtectedRoute = createRouteMatcher(["/analyze(.*)", "/report(.*)"]);

export default clerkMiddleware(async (auth, request) => {
  if (isProtectedRoute(request)) {
    // Redirects unauthenticated users to NEXT_PUBLIC_CLERK_SIGN_IN_URL ("/").
    await auth.protect();
  }
});

export const config = {
  matcher: [
    // Skip Next.js internals and static files unless they are found in search params.
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    // Always run for API routes.
    "/(api|trpc)(.*)",
  ],
};
