from pathlib import Path
import subprocess
import sys

def run(cmd, check=True):
    print(f">>> {cmd}")
    r = subprocess.run(cmd, shell=True)
    if check and r.returncode != 0:
        sys.exit(r.returncode)

# Cleanup
self_name = Path(__file__).name
for f in Path(".").glob("_*.py"):
    if f.name == self_name:
        continue
    print(f"Removing: {f.name}")
    try:
        f.unlink()
    except Exception as e:
        print(f"WARN: {f.name}: {e}")

run("git status --short", check=False)
run("git add -A")
run("git status --short")

msg = """feat(v5.11.5): P2-7 Java taint patterns

P2-7 was blind on Java. Now detects Servlet/Spring taint sources,
SQL/cmd/file/reflection/deserialization sinks, and entry points.

src/tools/patterns.py:
- TAINT_SOURCES["source_java"] -- request.getParameter/getHeader/getCookies,
  System.in/getenv/getProperty, Scanner, BufferedReader, @RequestParam/...
- TAINT_SINKS["sink_java_sql|cmd|file|reflect|deser|jndi"] -- executeQuery/
  executeUpdate/createStatement, Runtime.exec/ProcessBuilder, new File/
  FileInputStream/Paths.get, Class.forName/Method.invoke, ObjectInputStream/
  readObject, JndiManager/InitialContext/Context.lookup (Log4Shell).
- EXPLOIT_PATTERNS["entrypoint_java_main|spring|servlet"] -- main, Spring
  annotations, Servlet doGet/doPost.

src/tools/reachability.py:
- _LANG_ENTRYPOINTS["java"] -- java entry points mapping.
- trace_taint -- auto-detect Java in language loop.
- _is_comment_line() -- skip // # * /* lines in find_taint_* / find_entry_points.

Tests:
- tests/test_patterns_java.py (new): 41 tests.
- 361 passing (was 320).

Dogfood:
- examples/own/ServletSqli.java (new) -- path doGet -> getParameter -> createStatement.
- Known limitation: DbConnection.java path empty (source via method arg, no Java AST).
"""

msg_file = Path("_commit_msg.txt")
msg_file.write_text(msg, encoding="utf-8")

run("git commit -F _commit_msg.txt")
msg_file.unlink()
run("git log --oneline -3")

run('git tag -a v5.11.5 -m "v5.11.5 -- P2-7 Java taint patterns"')
run('git tag -l "v5.11*"')

run("git push origin main")
run("git push origin v5.11.5")

print()
print("=" * 70)
print("DONE -- v5.11.5 pushed")
print("=" * 70)
