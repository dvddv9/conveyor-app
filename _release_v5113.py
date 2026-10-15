from pathlib import Path
import subprocess
import sys

def run(cmd, check=True):
    print(f">>> {cmd}")
    r = subprocess.run(cmd, shell=True)
    if check and r.returncode != 0:
        print(f"FAIL: exit code {r.returncode}")
        sys.exit(r.returncode)

# ============================================================
# 1. Cleanup
# ============================================================
print("=" * 70)
print("1. CLEANUP")
print("=" * 70)
self_name = Path(__file__).name
for f in Path(".").glob("_*.py"):
    if f.name == self_name:
        print(f"Skipping self: {f.name}")
        continue
    print(f"Removing: {f.name}")
    try:
        f.unlink()
    except Exception as e:
        print(f"WARN: {f.name}: {e}")

# ============================================================
# 2. Git status
# ============================================================
print()
print("=" * 70)
print("2. GIT STATUS")
print("=" * 70)
run("git status --short", check=False)

# ============================================================
# 3. Stage
# ============================================================
print()
print("=" * 70)
print("3. GIT ADD")
print("=" * 70)
run("git add -A")
run("git status --short")

# ============================================================
# 4. Commit
# ============================================================
print()
print("=" * 70)
print("4. GIT COMMIT")
print("=" * 70)

msg = """refactor(v5.11.3): UI api_client.py -- centralized HTTP client

streamlit_app.py had 8 duplicated requests.* calls, each manually
passing headers=HEADERS. Headers defined in 3 places (API_URL,
API_KEY, HEADERS at module level).

New module src/ui/api_client.py:
- get(path, **kwargs), post(path, **kwargs) -- auto-inject X-API-Key
  header + default timeouts (10s GET, 300s POST).
- _url(path) helper -- joins API_URL + path with exactly one slash.

src/config.py:
- Added API_URL, CONVEYOR_API_KEY, API_TIMEOUT_SHORT/DEFAULT/LONG/BATCH.

src/ui/streamlit_app.py:
- 8 requests.* calls replaced with api_client.get/post.
- Removed local API_URL, API_KEY, HEADERS, import requests, import os.

Tests:
- tests/test_api_client.py (new): 16 tests (mocked HTTP).
- tests/test_ui_headers.py (rewritten): 13 tests.
  Now checks api_client + absence of direct requests.* in UI.

Tests: 320 passing (was 297).
No behavior change for end users.
"""

msg_file = Path("_commit_msg.txt")
msg_file.write_text(msg, encoding="utf-8")

run("git commit -F _commit_msg.txt")
msg_file.unlink()

run("git log --oneline -3")

# ============================================================
# 5. Tag
# ============================================================
print()
print("=" * 70)
print("5. GIT TAG")
print("=" * 70)
run('git tag -a v5.11.3 -m "v5.11.3 -- UI api_client.py"')
run('git tag -l "v5.11*"')

# ============================================================
# 6. Push
# ============================================================
print()
print("=" * 70)
print("6. GIT PUSH")
print("=" * 70)
run("git push origin main")
run("git push origin v5.11.3")

print()
print("=" * 70)
print("DONE -- v5.11.3 pushed")
print("=" * 70)
