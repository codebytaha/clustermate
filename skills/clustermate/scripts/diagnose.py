#!/usr/bin/env python3
"""ClusterMate diagnosis engine (Python standard library only).

Sends a cluster snapshot to a LOCAL open-weight model via Ollama and prints a
structured diagnosis in Markdown. No API keys, no cloud, no internet needed.

Usage:
    python3 diagnose.py --snapshot /tmp/snapshot.json [--model qwen3.5:4b]

Env:
    CLUSTERMATE_MODEL       Ollama model tag (default: qwen3.5:4b)
    CLUSTERMATE_OLLAMA_URL  Ollama base URL (default: http://localhost:11434)
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

OLLAMA_URL = os.environ.get("CLUSTERMATE_OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("CLUSTERMATE_MODEL", "qwen3.5:4b")
NUM_CTX = int(os.environ.get("CLUSTERMATE_NUM_CTX", "8192"))
HERE = os.path.dirname(os.path.abspath(__file__))

SYSTEM_PROMPT = """You are ClusterMate, an expert Kubernetes site-reliability engineer.
You diagnose real cluster problems from a JSON snapshot collected by kubectl.

Rules:
- Base every claim on the snapshot. Quote pod names, events, and log lines as evidence.
- If evidence is missing, say what is missing instead of guessing.
- Prefer the smallest safe fix first (image tag, resource limit, env var, probe).
- Never suggest deleting production workloads without confirmation.
- Write for a developer who is new to Kubernetes: plain language, no jargon without explanation.

Respond in Markdown with exactly these sections:
## Summary (one paragraph, what is broken)
## Root cause (the single most likely cause)
## Evidence (bullet list mapping each claim to snapshot data)
## Suggested fix (numbered kubectl commands, copy-paste ready)
## اردو میں وضاحت (explain the problem and fix in simple Urdu, 4-6 sentences)

If the snapshot contains a "security_notes" list, add one more section at the end:
## Security observations (bullet list, plain language — what to fix and why it matters)
"""


def load_reference():
    """Append the skill's failure-pattern knowledge as background."""
    ref = os.path.join(HERE, "..", "references", "common-failures.md")
    try:
        with open(ref) as f:
            return "\n\n## Known failure patterns (reference)\n" + f.read()
    except OSError:
        return ""


def ollama_generate(model, prompt):
    body = json.dumps({
        "model": model,
        "prompt": SYSTEM_PROMPT + "\n\n## Cluster snapshot\n```json\n" + prompt + "\n```" + load_reference(),
        "stream": False,
        "options": {"num_ctx": NUM_CTX, "temperature": 0.2},
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL + "/api/generate", data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            return json.loads(resp.read().decode())["response"]
    except urllib.error.URLError:
        sys.exit(
            "error: cannot reach Ollama at %s.\n"
            "  1. Install Ollama: https://ollama.com\n"
            "  2. Start it (it usually runs automatically), then:\n"
            "       ollama pull %s" % (OLLAMA_URL, model))
    except (KeyError, json.JSONDecodeError, TimeoutError) as e:
        msg = str(e)
        if "not found" in msg.lower():
            sys.exit("error: model '%s' is not pulled. Run: ollama pull %s" % (model, model))
        sys.exit("error: unexpected Ollama response: %s" % msg)


def to_html(body_markdown, title="ClusterMate diagnosis report"):
    """Minimal markdown-to-HTML for a shareable report. Stdlib only."""
    import html as _html
    import re as _re

    def inline(s):
        s = _html.escape(s)
        s = _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = _re.sub(r"`(.+?)`", r"<code>\1</code>", s)
        return s

    out = []
    for line in body_markdown.splitlines():
        s = line.strip()
        if s.startswith("## "):
            out.append("<h2>%s</h2>" % inline(s[3:]))
        elif s.startswith("- ") or s.startswith("* "):
            out.append("<li>%s</li>" % inline(s[2:]))
        elif _re.match(r"^\d+\.\s", s):
            out.append("<li>%s</li>" % inline(_re.sub(r"^\d+\.\s", "", s)))
        elif s.startswith("```"):
            continue
        elif s:
            out.append("<p>%s</p>" % inline(s))
    return ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<title>%s</title><style>"
            "body{font-family:system-ui,sans-serif;max-width:760px;margin:2em auto;padding:0 1em;line-height:1.6}"
            "h2{color:#1a56db;border-bottom:2px solid #1a56db;padding-bottom:.2em}"
            "code{background:#f3f4f6;padding:.15em .4em;border-radius:4px}"
            "li{margin:.3em 0}</style></head><body><h1>🐳 %s</h1>%s</body></html>"
            % (_html.escape(title), _html.escape(title), "\n".join(out)))


def main():
    ap = argparse.ArgumentParser(description="Diagnose a ClusterMate snapshot with a local open-weight model.")
    ap.add_argument("--snapshot", required=True, help="Path to snapshot JSON from cluster_snapshot.py")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model tag (default: %(default)s)")
    ap.add_argument("--html", default="", help="Also save a styled HTML report to FILE")
    args = ap.parse_args()

    try:
        with open(args.snapshot) as f:
            snapshot_text = f.read()
        json.loads(snapshot_text)  # validate
    except (OSError, json.JSONDecodeError) as e:
        sys.exit("error: cannot read snapshot: %s" % e)

    print("diagnosing with local open-weight model '%s' (no cloud, no API key)...\n" % args.model, file=sys.stderr)
    report = ollama_generate(args.model, snapshot_text)
    print(report)
    if args.html:
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(to_html(report))
        print("\nHTML report saved to %s" % args.html, file=sys.stderr)


if __name__ == "__main__":
    main()
