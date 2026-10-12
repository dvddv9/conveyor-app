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
