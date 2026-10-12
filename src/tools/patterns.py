# -*- coding: utf-8 -*-
"""PII and compliance patterns.

Dogfood finding: circular import between orchestrator and redact
required extracting patterns into a standalone module.
"""
import re


PII_PATTERNS = {
    "email": re.compile(r"(?<![\w%])[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "phone_ru": re.compile(r"\+7\d{10}|\b8\d{10}\b"),
    "passport_ru": re.compile(r"\b\d{4}\s?\d{6}\b"),
    "snils": re.compile(r"\b\d{3}-\d{3}-\d{3}[ -]?\d{2}\b"),
    "iban": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b"),
    # Secrets
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "aws_secret_key": re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*[\"']?[A-Za-z0-9/+=]{40}[\"']?"),
    "stripe_live_key": re.compile(r"\bsk_live_[A-Za-z0-9]{20,}\b"),
    "stripe_test_key": re.compile(r"\bsk_test_[A-Za-z0-9]{20,}\b"),
    "github_token": re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
    "slack_token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "google_api_key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "private_key": re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "hardcoded_password": re.compile(r"(?i)\bpassword\s*[:=]\s*[\"'][^\"']{8,}[\"']"),
    "hardcoded_secret": re.compile(r"(?i)\b(secret|api_key|access_key|token)\s*[:=]\s*[\"'][^\"']{12,}[\"']"),
}


COMPLIANCE_TRIGGERS = {
    "HIPAA": ["patient", "diagnosis", "medical record", "hipaa", "ehr"],
    "PCI-DSS": ["payment", "card", "cvv", "credit card", "pci"],
    "GDPR": ["personal data", "gdpr", "eu citizen", "right to erasure"],
    "152-ФЗ": ["персональные данные", "152-фз", "оператор данных"],
    "EU AI Act": ["llm", "foundation model", "ai system", "eu ai act"],
    # SECRETS выставляется только через detect_pii (см. ниже),
    # keyword-triggers удалены: они ловили имена переменных, а не секреты.
    # "SECRETS": [...],
}


# Dogfood P0 fix: critical risk patterns that MUST NOT be downgraded
# to WARNING even if audit doesn't find SECRETS/PII.
# These are RCE, code injection, deserialization, path traversal, SQLi.
CRITICAL_RISK_PATTERNS = {
    "rce_shell": re.compile(r"\b(os\.system|subprocess\.(call|run|Popen|check_output|check_call)|os\.popen)\s*\("),
    "rce_eval": re.compile(r"\b(eval|exec)\s*\("),
    "rce_import": re.compile(r"__import__\s*\(|getattr\s*\([^,]+,\s*[a-z_]+\s*\)"),
    "sqli_concat": re.compile(r"(SELECT|INSERT|UPDATE|DELETE|DROP)\s+.*['\"]\s*\+\s*", re.IGNORECASE),
    "sqli_fstring": re.compile(r"execute\s*\(\s*f['\"]", re.IGNORECASE),
    "path_traversal": re.compile(r"open\s*\([^)]*\.\.[/\\]|os\.path\.join\s*\([^,]+,\s*[a-z_]+\s*\)"),
    "insecure_deser": re.compile(r"(pickle\.loads|yaml\.load\s*\([^,)]+\)|marshal\.loads)"),
    "shell_true": re.compile(r"shell\s*=\s*True"),
    "ssti": re.compile(r"render_template_string\s*\(|Template\s*\([^)]+\).*render"),
    "ldap_injection": re.compile(r"search\s*\([^)]*\+\s*[a-z_]+"),
    "xxe": re.compile(r"(etree\.parse|XMLParser|parseString)\s*\(.*resolve_entities"),
}


# OWASP Top 10 mapping (2021 + 2025 preview)
# Dogfood P1: map CWE to OWASP category for compliance reports.
CWE_TO_OWASP = {
    # Injection
    "CWE-89":   {"2021": "A03:2021 Injection", "2025": "A03:2025 Injection", "name": "SQL Injection"},
    "CWE-79":   {"2021": "A03:2021 Injection", "2025": "A03:2025 Injection", "name": "XSS"},
    "CWE-78":   {"2021": "A03:2021 Injection", "2025": "A03:2025 Injection", "name": "OS Command Injection"},
    "CWE-94":   {"2021": "A03:2021 Injection", "2025": "A03:2025 Injection", "name": "Code Injection"},
    "CWE-77":   {"2021": "A03:2021 Injection", "2025": "A03:2025 Injection", "name": "Command Injection"},
    "CWE-129":  {"2021": "A03:2021 Injection", "2025": "A03:2025 Injection", "name": "Array Index"},
    "CWE-787":  {"2021": "A03:2021 Injection", "2025": "A03:2025 Injection", "name": "OOB Write"},
    "CWE-125":  {"2021": "A03:2021 Injection", "2025": "A03:2025 Injection", "name": "OOB Read"},
    "CWE-917":  {"2021": "A03:2021 Injection", "2025": "A03:2025 Injection", "name": "Expression Language Injection"},

    # Broken Access Control
    "CWE-22":   {"2021": "A01:2021 Broken Access Control", "2025": "A01:2025 Broken Access Control", "name": "Path Traversal"},
    "CWE-352":  {"2021": "A01:2021 Broken Access Control", "2025": "A01:2025 Broken Access Control", "name": "CSRF"},
    "CWE-639":  {"2021": "A01:2021 Broken Access Control", "2025": "A01:2025 Broken Access Control", "name": "IDOR"},
    "CWE-284":  {"2021": "A01:2021 Broken Access Control", "2025": "A01:2025 Broken Access Control", "name": "Improper Access Control"},
    "CWE-863":  {"2021": "A01:2021 Broken Access Control", "2025": "A01:2025 Broken Access Control", "name": "Incorrect Authorization"},

    # Cryptographic Failures
    "CWE-327":  {"2021": "A02:2021 Cryptographic Failures", "2025": "A02:2025 Cryptographic Failures", "name": "Broken Crypto"},
    "CWE-328":  {"2021": "A02:2021 Cryptographic Failures", "2025": "A02:2025 Cryptographic Failures", "name": "Weak Hash"},
    "CWE-330":  {"2021": "A02:2021 Cryptographic Failures", "2025": "A02:2025 Cryptographic Failures", "name": "Weak Random"},
    "CWE-798":  {"2021": "A07:2021 Auth Failures", "2025": "A07:2025 Auth Failures", "name": "Hardcoded Credentials"},

    # Insecure Design
    "CWE-434":  {"2021": "A04:2021 Insecure Design", "2025": "A04:2025 Insecure Design", "name": "Unrestricted Upload"},

    # Security Misconfiguration
    "CWE-611":  {"2021": "A05:2021 Security Misconfiguration", "2025": "A05:2025 Security Misconfiguration", "name": "XXE"},
    "CWE-1004": {"2021": "A05:2021 Security Misconfiguration", "2025": "A05:2025 Security Misconfiguration", "name": "Cookie without HttpOnly"},
    "CWE-16":   {"2021": "A05:2021 Security Misconfiguration", "2025": "A05:2025 Security Misconfiguration", "name": "Configuration"},

    # Vulnerable Components
    "CWE-1035": {"2021": "A06:2021 Vulnerable Components", "2025": "A06:2025 Vulnerable Components", "name": "Vulnerable Component"},

    # Auth Failures
    "CWE-287":  {"2021": "A07:2021 Auth Failures", "2025": "A07:2025 Auth Failures", "name": "Improper Authentication"},
    "CWE-306":  {"2021": "A07:2021 Auth Failures", "2025": "A07:2025 Auth Failures", "name": "Missing Authentication"},

    # Software and Data Integrity
    "CWE-502":  {"2021": "A08:2021 Software and Data Integrity", "2025": "A08:2025 Software and Data Integrity", "name": "Insecure Deserialization"},

    # Logging and Monitoring
    "CWE-778":  {"2021": "A09:2021 Logging Failures", "2025": "A09:2025 Logging Failures", "name": "Insufficient Logging"},

    # SSRF
    "CWE-918":  {"2021": "A10:2021 SSRF", "2025": "A10:2025 SSRF", "name": "SSRF"},
}


def cwe_to_owasp(cwe_id: str, year: str = "2025") -> str:
    """Map CWE to OWASP Top 10 category.

    Args:
        cwe_id: e.g. "CWE-89"
        year: "2021" or "2025"

    Returns:
        OWASP category string or empty.
    """
    entry = CWE_TO_OWASP.get(cwe_id)
    if not entry:
        return ""
    return entry.get(year, "")


# Exploitability patterns (Dogfood P2: reachability, auth, blast radius)
EXPLOIT_PATTERNS = {
    # Entry points (reachable from outside)
    "entrypoint_web": re.compile(
        r"@app\.(route|get|post|put|delete|patch)\s*\(|"
        r"@router\.(get|post|put|delete|patch)\s*\(|"
        r"@\w+\.(get|post|put|delete|patch)\s*\(",
        re.IGNORECASE,
    ),
    "entrypoint_func": re.compile(
        r"\bdef\s+(handler|process|handle|route|api_|endpoint)\w*\s*\(",
        re.IGNORECASE,
    ),
    "entrypoint_main": re.compile(r"if\s+__name__\s*==\s*['\"]__main__['\"]"),

    # Auth checks (if present — not exploitable directly)
    "auth_decorator": re.compile(
        r"@\w*(login_required|requires_auth|authenticated|authorized)\w*|"
        r"Depends\(\s*\w*(auth|current_user|get_user|verify)\w*\s*\)",
        re.IGNORECASE,
    ),
    "auth_check": re.compile(
        r"\bif\s+(not\s+)?\w*(is_authenticated|is_authorized|has_permission|check_auth)\b",
        re.IGNORECASE,
    ),

    # Blast radius indicators
    "blast_db": re.compile(
        r"\b(db\.execute|cursor\.execute|session\.execute|conn\.execute|"
        r"\.query\(|\.raw\(|\.filter\(|\.filter_by\()",
        re.IGNORECASE,
    ),
    "blast_shell": re.compile(
        r"\b(os\.system|os\.popen|subprocess\.(call|run|Popen|check_output|check_call))",
        re.IGNORECASE,
    ),
    "blast_fs": re.compile(
        r"\b(open\s*\(|shutil\.(copy|move|rmtree)|os\.(remove|unlink|rmdir))",
        re.IGNORECASE,
    ),
    "blast_network": re.compile(
        r"\b(requests\.(get|post|put|delete|patch)|urllib\.|http\.client|socket\.)",
        re.IGNORECASE,
    ),
    "blast_eval": re.compile(r"\b(eval|exec|__import__)\s*\(", re.IGNORECASE),
}


def detect_exploitability(material: str) -> dict:
    """Detect exploitability: reachability, auth, blast radius.

    Returns:
        {
            "reachable": bool,
            "auth_required": bool,
            "exploit_path": str,
            "blast_radius": str ("high"|"medium"|"low"),
            "entry_points": list[str],
            "blast_indicators": list[str],
        }
    """
    entry_points = []
    blast_indicators = []

    for name, pattern in EXPLOIT_PATTERNS.items():
        if pattern.search(material):
            if name.startswith("entrypoint_"):
                entry_points.append(name.replace("entrypoint_", ""))
            elif name.startswith("blast_"):
                blast_indicators.append(name.replace("blast_", ""))

    reachable = bool(entry_points)
    auth_required = bool(
        EXPLOIT_PATTERNS["auth_decorator"].search(material) or
        EXPLOIT_PATTERNS["auth_check"].search(material)
    )

    # Blast radius: high if shell/eval, medium if db/network, low if fs-only
    if "shell" in blast_indicators or "eval" in blast_indicators:
        blast = "high"
    elif "db" in blast_indicators or "network" in blast_indicators:
        blast = "medium"
    elif "fs" in blast_indicators:
        blast = "low"
    else:
        blast = "none"

    # Exploit path: entry_point -> auth? -> blast
    if reachable:
        path = " -> ".join(entry_points + (["auth?"] if not auth_required else ["auth-required"]) + blast_indicators)
    else:
        path = "not reachable from public entrypoint"

    return {
        "reachable": reachable,
        "auth_required": auth_required,
        "exploit_path": path,
        "blast_radius": blast,
        "entry_points": entry_points,
        "blast_indicators": blast_indicators,
    }
