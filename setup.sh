#!/usr/bin/env bash
# ClusterMate setup: checks prerequisites and pulls the default open-weight model.
set -euo pipefail

MODEL="${CLUSTERMATE_MODEL:-qwen3.5:4b}"
ok=1

need() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "  [ok] $1"
  else
    echo "  [MISSING] $1 -- $2"
    ok=0
  fi
}

# A real interpreter, not the Windows "python3" Store alias (it is on PATH and exits 9009).
pick_python() {
  if python3 -c "import sys" >/dev/null 2>&1; then
    echo python3
  elif python -c "import sys" >/dev/null 2>&1; then
    echo python
  elif py -3 -c "import sys" >/dev/null 2>&1; then
    echo "py -3"
  fi
}

echo "ClusterMate prerequisites:"
PY="$(pick_python || true)"
if [ -n "$PY" ]; then
  echo "  [ok] python ($PY)"
else
  echo "  [MISSING] python -- install from https://www.python.org/downloads/"
  echo "            On Windows, disable the Microsoft Store python3 alias and use python or py -3."
  ok=0
fi
need kubectl "install from https://kubernetes.io/docs/tasks/tools/"
need ollama  "install from https://ollama.com/download"

if [ "$ok" -eq 0 ]; then
  echo "Install the missing tools above, then re-run ./setup.sh"
  exit 1
fi

echo "Pulling open-weight model: $MODEL"
ollama pull "$MODEL"

echo "Checking cluster access:"
kubectl cluster-info --request-timeout=10s >/dev/null \
  && echo "  [ok] kubectl can reach a cluster" \
  || echo "  [warn] kubectl has no cluster yet — start one (e.g. 'kind create cluster')"

echo
echo "Done. Next:"
echo "  kind create cluster                         # if you need a local cluster"
echo "  kubectl apply -f demo/broken-app.yaml       # bad tag -> ImagePullBackOff"
echo "  cp -r skills/clustermate ~/.claude/skills/  # install the skill"
echo "  $PY skills/clustermate/scripts/cluster_snapshot.py -n clustermate-demo -o snapshot.json"
echo "  $PY skills/clustermate/scripts/diagnose.py --snapshot snapshot.json --html report.html"
echo "  # CPU diagnosis takes about 10 minutes. Thinking is disabled so the report can finish."
