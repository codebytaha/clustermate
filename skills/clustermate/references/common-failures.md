# Common Kubernetes failure patterns

Background knowledge for diagnosis. Match snapshot evidence (events, container
states, log lines) against these patterns before concluding.

## ImagePullBackOff / ErrImagePull
- **Signals:** event `Failed to pull image`, container state `waiting.reason = ImagePullBackOff`.
- **Causes:** wrong image tag, private registry without `imagePullSecrets`, typo in registry host, rate limiting.
- **Fix:** `kubectl set image deployment/<name> <container>=<registry>/<image>:<tag>`; add `imagePullSecrets` for private registries; check tag exists with `docker manifest inspect` or registry UI.

## CrashLoopBackOff
- **Signals:** high `restartCount`, `terminated.reason = Error`, logs show the same crash repeatedly.
- **Causes:** app bug on startup (missing env var, bad config, port already bound), failing DB connection, missing file/volume mount.
- **Fix:** read the *previous* container logs (`kubectl logs -p`); check env (`kubectl exec env`); fix the app config or Deployment env, then `kubectl rollout restart`.

## OOMKilled
- **Signals:** `terminated.reason = OOMKilled`, exit code 137.
- **Causes:** container exceeded its memory `limits` (or node memory pressure).
- **Fix:** raise `resources.limits.memory` (and `requests`), or fix the memory leak. Check with `kubectl top pod`.

## CreateContainerConfigError
- **Signals:** pod stuck in `ContainerCreating`, event about missing ConfigMap/Secret key.
- **Causes:** Deployment references a ConfigMap/Secret key that does not exist.
- **Fix:** `kubectl describe` names the missing key; create/fix the ConfigMap/Secret.

## Pending (unschedulable)
- **Signals:** phase `Pending`, event `FailedScheduling` with reason like `Insufficient cpu/memory` or `node(s) didn't match Pod's node affinity`.
- **Causes:** requests exceed node capacity, nodeSelector/affinity too strict, taints without tolerations.
- **Fix:** lower `resources.requests`, fix affinity, or add nodes.

## Liveness/Readiness probe failures
- **Signals:** events `Liveness probe failed` / `Readiness probe failed`, restarts without app crash.
- **Causes:** probe path wrong, app slow to start (needs `initialDelaySeconds` / `startupProbe`), port mismatch.
- **Fix:** correct probe path/port, add `startupProbe` for slow starters.

## Terminology cheat-sheet
- **Deployment** = desired state for stateless apps. **Pod** = one running instance. **Events** = the cluster's own log of what it tried to do — read these first.
