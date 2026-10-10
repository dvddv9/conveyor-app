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

pip install -e ".[dev]"

conveyor analyze path/to/file.py


---

## Hard Case Studies

5 production-grade open-source files analyzed at D3–D4. See [hard/](hard/) for full reports.

| # | Project | Lang | Level | Truncate | Cost | Key findings |
|---|---------|------|-------|----------|------|--------------|
| 1 | [Log4Shell](hard/log4shell-jndi-lookup.md) | Java | D3 | No | $0.0057 | CVE-2021-44228, JNDI injection |
| 2 | [OpenSSL EVP](hard/openssl-evp-enc.md) | C | D3 | 75% | $0.0092 | CVE-2023-5363, race, partial-init UB |
| 3 | [Redis networking](hard/redis-networking.md) | C | D4 | 95% | $0.0071 | TOCTOU auth, io-thread race, UB |
| 4 | [K8s scheduler](hard/k8s-scheduler.md) | Go | D4 | 50% | $0.0080 | Irreversible `metrics.Register()`, shared state |
| 5 | [PostgreSQL execMain](hard/postgres-execmain.md) | C | D4 | 88% | $0.0088 | Snapshot leak, privilege escalation via hook |

**Total:** 10 analyses (5 synthetic + 5 hard), ~$0.075. Average: ~$0.0075.


## Links

- [Main README](../../README.md)
- [GitHub Actions](https://github.com/dvddv9/conveyor-app/actions)
- [Source code](../../src)