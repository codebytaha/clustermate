---
name: clustermate
description: Diagnose Kubernetes cluster problems with a local open-weight model. Use when pods are failing, CrashLoopBackOff, ImagePullBackOff, OOMKilled, pending pods, or the user asks "why is my app down" on Kubernetes. Explains root causes in plain English and Urdu, cites evidence, and suggests exact kubectl fixes. Fully offline — no API keys, no cloud.
license: MIT
---

# ClusterMate

Give an agent the ability to troubleshoot Kubernetes clusters. The skill collects
live cluster state with bundled scripts, reasons over it with a **local
open-weight model via Ollama** (default `qwen3.5:4b`), Apache-2.0, and returns a
structured diagnosis with evidence and fixes.

**Capabilities:** reads live cluster state · diagnoses with local AI (fully
offline) · explains in plain English **and Urdu** · flags security
misconfigurations (`:latest` tags, root containers, missing limits) ·
generates a shareable HTML report · verifies the fix worked.

## Workflow

1. **Snapshot the cluster.** Run the collector (no dependencies beyond `kubectl`):
   ```bash
   python3 skills/clustermate/scripts/cluster_snapshot.py --output /tmp/snapshot.json
   ```
   Use `-n <namespace>` to scope it, or omit for all namespaces. The snapshot is
   one JSON document: nodes, unhealthy pods (with `describe` + recent logs),
   the latest cluster events, and `security_notes` (static checks for `:latest`
   image tags, containers running as root, and missing memory limits).

2. **Diagnose with the open-weight model.** This is the core reasoning step —
   it must run against the local model, not a cloud API:
   ```bash
   python3 skills/clustermate/scripts/diagnose.py --snapshot /tmp/snapshot.json --html /tmp/report.html
   ```
   Set `CLUSTERMATE_MODEL` to pick another local Ollama model
   (e.g. `qwen3.5:9b` on a 16 GB machine). `CLUSTERMATE_NUM_CTX` tunes the
   context window (default 8192 — lower it if you're tight on RAM). The script appends
   `references/common-failures.md` as background knowledge and asks the model
   for: summary, root cause, evidence, suggested `kubectl` fixes, security
   observations, and an explanation in Urdu. The `--html` flag saves the same
   report as a styled page you can share or demo in a browser.

3. **Present and fix.** Show the diagnosis to the user, then apply the
   suggested fix (e.g. `kubectl set image`, `kubectl apply -f`) and re-run the
   snapshot to confirm the cluster is healthy. The loop is
   observe → diagnose → act → verify — never act without evidence, never stop
   without verifying.

## What the output looks like

```
## Summary
The `broken-web` Deployment can't start: Kubernetes cannot pull
`nginx:9.9.9-nonexistent` — that tag doesn't exist.

## Root cause
Wrong image tag in the Deployment manifest.

## Evidence
- Container state `ImagePullBackOff` on pod `broken-web-…`
- Event `Failed to pull image "nginx:9.9.9-nonexistent"` (count 5)

## Suggested fix
1. kubectl set image deployment/broken-web web=nginx:1.27 -n clustermate-demo
2. kubectl rollout status deployment/broken-web -n clustermate-demo

## Security observations
- Container has no memory limit — a leak could take the node down.

## اردو میں وضاحت
…plain-Urdu explanation of the problem and the fix…
```

## Rules

- Never send cluster data to a cloud/proprietary model. The whole point of
  this skill is private, offline diagnosis — keep it on the local model.
- Do not invent log lines or events. If the snapshot lacks evidence, say so
  and ask the user for the namespace or workload name.
- Prefer the smallest safe fix first (image tag, resource limit, env var)
  over destructive actions. Never delete production workloads without asking.
- Keep secrets out of output: redact tokens, passwords, and keys if they
  appear in env vars or logs.

## Example

See `examples/example-session.md` for a full worked session:
a broken Deployment (`demo/broken-app.yaml`) diagnosed end-to-end.

## Install

Copy this folder to one of the standard skill paths — no build step:

- Claude Code: `~/.claude/skills/clustermate/` (personal) or `.claude/skills/clustermate/` (project)
- GitHub Copilot: `.github/skills/clustermate/`
- OpenAI Codex / Gemini CLI: `.agents/skills/clustermate/`
