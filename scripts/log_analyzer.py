#!/usr/bin/env python3
"""
log_analyzer.py — AI-driven root-cause analysis for the self-healing pipeline.

Reads deployment/application logs from stdin or a file, sends them to the
OpenAI Chat Completions API for root-cause analysis, and returns a structured
JSON report. The CI/CD workflow uses this report to decide whether to retry,
roll back, or escalate.

Usage:
    # From a file
    python scripts/log_analyzer.py --log-file /var/log/app/deploy.log

    # From stdin
    cat deploy.log | python scripts/log_analyzer.py

    # With explicit output file
    python scripts/log_analyzer.py --log-file deploy.log --output report.json

Environment variables:
    OPENAI_API_KEY  – Required. Your OpenAI API key.
    OPENAI_MODEL    – Optional. Model to use (default: gpt-4o-mini).
    MAX_LOG_CHARS   – Optional. Truncate logs to this many characters (default: 8000).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import textwrap
from datetime import datetime, timezone
from typing import Any

# Third-party
try:
    from openai import OpenAI, APIError, AuthenticationError
except ImportError:
    print(
        "ERROR: openai package not found. Install it with: pip install openai",
        file=sys.stderr,
    )
    sys.exit(1)

# --------------------------------------------------------------------------- #
#  Logging                                                                     #
# --------------------------------------------------------------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
#  Constants / defaults                                                        #
# --------------------------------------------------------------------------- #
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_MAX_LOG_CHARS = 8_000

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an expert Site Reliability Engineer (SRE) assistant specialised in
    diagnosing CI/CD pipeline and application deployment failures.

    Given a block of deployment or application logs, you will:
    1. Identify the most likely root cause of the failure.
    2. Classify the severity (critical, high, medium, low).
    3. Suggest a recommended corrective action from exactly one of:
       "retry", "rollback", "scale", "investigate", "no_action".
    4. Provide a concise explanation (3–5 sentences).
    5. List up to five specific remediation steps an engineer could take.

    Respond ONLY with a valid JSON object matching this schema — no markdown, no
    extra text:
    {
      "root_cause": "<string>",
      "severity": "<critical|high|medium|low>",
      "recommended_action": "<retry|rollback|scale|investigate|no_action>",
      "explanation": "<string>",
      "remediation_steps": ["<step1>", "<step2>", ...]
    }
    """
).strip()


# --------------------------------------------------------------------------- #
#  Core analysis function                                                      #
# --------------------------------------------------------------------------- #

def analyze_logs(
    log_content: str,
    model: str = DEFAULT_MODEL,
    max_log_chars: int = DEFAULT_MAX_LOG_CHARS,
) -> dict[str, Any]:
    """
    Send *log_content* to the OpenAI API and return the parsed analysis dict.

    Raises:
        ValueError: if the API response cannot be parsed as JSON.
        RuntimeError: on API or authentication errors.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set. "
            "Export it before running this script."
        )

    # Trim logs to avoid excessive token usage
    if len(log_content) > max_log_chars:
        logger.warning(
            "Log content truncated from %d to %d characters.",
            len(log_content),
            max_log_chars,
        )
        log_content = log_content[-max_log_chars:]

    client = OpenAI(api_key=api_key)

    logger.info("Sending %d chars of log data to OpenAI (%s) …", len(log_content), model)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Analyze the following deployment logs:\n\n```\n{log_content}\n```",
                },
            ],
            temperature=0.2,
            max_tokens=600,
        )
    except AuthenticationError as exc:
        raise RuntimeError(f"OpenAI authentication failed: {exc}") from exc
    except APIError as exc:
        raise RuntimeError(f"OpenAI API error: {exc}") from exc

    raw = response.choices[0].message.content.strip()
    logger.info("Raw API response: %s", raw[:200])

    try:
        analysis = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse API response as JSON.\nRaw response:\n{raw}"
        ) from exc

    return analysis


_REQUIRED_ANALYSIS_KEYS = frozenset(
    {"root_cause", "severity", "recommended_action", "explanation", "remediation_steps"}
)

_VALID_ACTIONS = frozenset(
    {"retry", "rollback", "scale", "investigate", "no_action"}
)

_VALID_SEVERITIES = frozenset({"critical", "high", "medium", "low"})


def build_report(analysis: dict[str, Any], log_source: str) -> dict[str, Any]:
    """Validate *analysis* and wrap it in a timestamped report envelope."""
    missing = _REQUIRED_ANALYSIS_KEYS - analysis.keys()
    if missing:
        raise ValueError(
            f"Analysis dict is missing required keys: {sorted(missing)}"
        )

    action = analysis.get("recommended_action")
    if action not in _VALID_ACTIONS:
        raise ValueError(
            f"Invalid recommended_action '{action}'. Must be one of: {sorted(_VALID_ACTIONS)}"
        )

    severity = analysis.get("severity")
    if severity not in _VALID_SEVERITIES:
        raise ValueError(
            f"Invalid severity '{severity}'. Must be one of: {sorted(_VALID_SEVERITIES)}"
        )

    return {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "log_source": log_source,
        "analysis": analysis,
    }


# --------------------------------------------------------------------------- #
#  Fallback / offline mode                                                     #
# --------------------------------------------------------------------------- #

HEURISTIC_PATTERNS: list[tuple[str, dict[str, Any]]] = [
    (
        "oom|out of memory|memory limit exceeded|killed",
        {
            "root_cause": "Container or process OOM-killed due to memory pressure.",
            "severity": "critical",
            "recommended_action": "rollback",
            "explanation": (
                "The deployment process was terminated by the OOM killer, indicating "
                "memory consumption exceeded configured limits. This will recur on "
                "retry without a memory-limit increase."
            ),
            "remediation_steps": [
                "Roll back to the previous stable version immediately.",
                "Profile heap usage of the new build.",
                "Increase container memory limit in the deployment manifest.",
                "Add memory-usage metrics and alerting thresholds.",
                "Investigate recent code changes for memory leaks.",
            ],
        },
    ),
    (
        "connection refused|unable to connect|dial tcp|econnrefused",
        {
            "root_cause": "Downstream service or database is unreachable.",
            "severity": "high",
            "recommended_action": "retry",
            "explanation": (
                "The application could not establish a network connection to a "
                "dependency (database, cache, or external API). This may be a "
                "transient network blip that a retry can resolve."
            ),
            "remediation_steps": [
                "Verify the downstream service is running and healthy.",
                "Check firewall / security-group rules.",
                "Confirm DNS resolution and service-discovery configuration.",
                "Add connection retry logic with exponential back-off in the app.",
                "Implement a circuit breaker to prevent cascade failures.",
            ],
        },
    ),
    (
        "exit code 1|non-zero exit|build failed|error:",
        {
            "root_cause": "Build or startup script exited with a non-zero status code.",
            "severity": "high",
            "recommended_action": "investigate",
            "explanation": (
                "A build step or the application entrypoint returned an error exit "
                "code. This usually indicates a misconfiguration or missing dependency "
                "that requires manual investigation."
            ),
            "remediation_steps": [
                "Review the full build and startup logs for the specific error.",
                "Reproduce the failure locally with the same environment variables.",
                "Ensure all required dependencies are present in requirements/package files.",
                "Check for syntax errors or typos in configuration files.",
                "Compare the failing build against the last successful build.",
            ],
        },
    ),
]


def heuristic_analyze(log_content: str) -> dict[str, Any]:
    """
    Lightweight offline fallback when the OpenAI API is unavailable.
    Matches against known error patterns and returns a pre-canned analysis.
    """
    import re

    lower = log_content.lower()
    for pattern, analysis in HEURISTIC_PATTERNS:
        if re.search(pattern, lower):
            logger.info("Heuristic match: pattern=%r", pattern)
            return analysis

    return {
        "root_cause": "Unknown failure — no matching heuristic pattern found.",
        "severity": "medium",
        "recommended_action": "investigate",
        "explanation": (
            "The log analyser could not identify a known error pattern. "
            "Manual investigation is required."
        ),
        "remediation_steps": [
            "Review the full log output for anomalies.",
            "Compare metrics around the time of failure.",
            "Check recent commits for changes that could cause instability.",
            "Consult the runbook for this service.",
        ],
    }


# --------------------------------------------------------------------------- #
#  CLI entry point                                                             #
# --------------------------------------------------------------------------- #

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI-driven log analysis for the self-healing CI/CD pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--log-file",
        metavar="PATH",
        help="Path to the log file to analyse. Reads from stdin if omitted.",
    )
    parser.add_argument(
        "--output",
        metavar="PATH",
        help="Write the JSON report to this file (default: stdout).",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        help=f"OpenAI model to use (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=int(os.getenv("MAX_LOG_CHARS", DEFAULT_MAX_LOG_CHARS)),
        help="Maximum log characters to send to the API.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use offline heuristic analysis instead of the OpenAI API.",
    )
    parser.add_argument(
        "--get-action",
        metavar="REPORT_FILE",
        help=(
            "Read an existing JSON report file and print only the "
            "recommended_action to stdout. Exits 0 for retry/no_action, 2 otherwise."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # ---- Short-circuit: extract action from existing report ---------------- #
    if args.get_action:
        try:
            with open(args.get_action, "r", encoding="utf-8") as fh:
                report = json.load(fh)
            action = report["analysis"]["recommended_action"]
            print(action)
            return 0 if action in ("no_action", "retry") else 2
        except (OSError, KeyError, json.JSONDecodeError) as exc:
            logger.error("Cannot extract action from %s: %s", args.get_action, exc)
            print("rollback")
            return 2

    # ---- Read log content -------------------------------------------------- #
    if args.log_file:
        try:
            with open(args.log_file, "r", encoding="utf-8", errors="replace") as fh:
                log_content = fh.read()
            log_source = args.log_file
        except OSError as exc:
            logger.error("Cannot read log file: %s", exc)
            return 1
    else:
        if sys.stdin.isatty():
            logger.error("No log file provided and stdin is a terminal. Aborting.")
            return 1
        log_content = sys.stdin.read()
        log_source = "stdin"

    if not log_content.strip():
        logger.error("Log content is empty — nothing to analyse.")
        return 1

    logger.info("Log source: %s (%d chars)", log_source, len(log_content))

    # ---- Perform analysis -------------------------------------------------- #
    try:
        if args.offline:
            logger.info("Running in offline / heuristic mode.")
            analysis = heuristic_analyze(log_content)
        else:
            analysis = analyze_logs(log_content, model=args.model, max_log_chars=args.max_chars)
    except (RuntimeError, ValueError) as exc:
        logger.error("Analysis failed: %s", exc)
        logger.info("Falling back to heuristic analysis …")
        analysis = heuristic_analyze(log_content)

    report = build_report(analysis, log_source)

    # ---- Output report ----------------------------------------------------- #
    report_json = json.dumps(report, indent=2)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(report_json + "\n")
            logger.info("Report written to %s", args.output)
        except OSError as exc:
            logger.error("Cannot write output file: %s", exc)
            print(report_json)
    else:
        print(report_json)

    # Propagate the recommended action as an exit code hint (useful in scripts):
    #   0 = no_action / retry (non-fatal)
    #   2 = rollback / investigate / scale (requires intervention)
    action = analysis.get("recommended_action", "investigate")
    return 0 if action in ("no_action", "retry") else 2


if __name__ == "__main__":
    sys.exit(main())
