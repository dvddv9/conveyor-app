\# Case Studies — Conveyor V5.7



Real-world validation: Conveyor V5.7 analyzed 5 open-source projects and found \*\*actionable findings\*\* in each.



\## Summary



| # | Project | Level | Cost | Findings | Link |

|---|---------|-------|------|----------|------|

| 1 | FastAPI | D4 | $0.0082 | OOM via id(func), vendored divergence, memory leak | \[→](fastapi-oom-id-func.md) |

| 2 | Django | D3 | $0.0068 | Async race in peers, sync\_to\_async per-chunk, breaking 2028 | \[→](django-async-race.md) |

| 3 | Flask | D4 | $0.0065 | SECRET\_KEY=None, cookie flags, Host header injection, DoS | \[→](flask-secret-key.md) |

| 4 | Express | D3 | $0.0069 | Prototype pollution, req.url trust, runtime registration race | \[→](express-prototype-pollution.md) |

| 5 | Go stdlib | D3 | $0.0074 | CL/TE smuggling, DoS, HTTP/2 handoff race | \[→](go-stdlib-cl-te.md) |



\*\*Total:\*\* 5 analyses, \~$0.036.



\*\*Average cost per analysis:\*\* $0.0072.

\*\*Average time per analysis:\*\* 60 seconds.



\---



\## Why these case studies matter



Each case study demonstrates:



1\. \*\*Real findings\*\* — not hypothetical, not synthetic.

2\. \*\*Specific line numbers\*\* — actionable, not vague.

3\. \*\*Severity classification\*\* — critical / important / optional.

4\. \*\*Senior-level insights\*\* — e.g., id(func) OOM in FastAPI, CL/TE smuggling in Go stdlib.



These are the kinds of findings a \*\*senior engineer with security focus\*\* would identify in 30 minutes.



\*\*Conveyor finds them in 60 seconds.\*\*



\---



\## Methodology



\*\*Input:\*\* A single file from each project (slice, \~12,000 chars).

\*\*Pipeline:\*\* 6 stages — Orchestrator → Scanner → Analyst → Researcher → Synthesizer → Transmitter.

\*\*Model:\*\* DeepSeek (cloud).

\*\*Verification:\*\* Findings cross-checked against known CVEs, framework documentation, and Python/Go security best practices.



\*\*Important:\*\* Results may include false positives. Always verify findings before applying.



\---



\## Reproduce



```bash

pip install -e ".\[dev]"

conveyor analyze path/to/file.py

Links
Main README

GitHub Actions

Source code



