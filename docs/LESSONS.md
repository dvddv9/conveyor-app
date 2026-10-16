# Lessons from upstream contributions

## 2026-10-16 -- curl/curl incident

Context: I ran a Vishap audit on curl docs and submitted 3 issues
(#23438-#23440) directly to github.com/curl/curl. The maintainers
(Daniel Stenberg, Stefan Eissing) responded negatively -- the format
was too long, AI-generated, and not in the contributor's voice.

Actions taken:
- Issues closed by maintainers.
- Replied once with a short human apology.
- Left the project.

Lessons for Vishap users:
1. Never post AI-generated audit output directly to upstream projects.
2. Read CONTRIBUTING.md before filing any issue or PR.
3. Prefer PRs over issues.
4. Keep reports short (<=100 words). Write in your own voice, not the
   tool's.
5. Do not argue with maintainers. They are right by default.
6. If asked to stop -- stop immediately, close, and leave.
7. Vishap is a tool for local analysis / internal review. It is not a
   replacement for human communication.

What changed in the process:
- Added this LESSONS.md.
- Added a note in docs/case-studies/dogfood/curl-docs/README.md.
