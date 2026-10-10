# Example session: broken Deployment, diagnosed end-to-end

> Illustrative example. Recreate it live with `demo/broken-app.yaml`.

## 1. The symptom

A developer applies a Deployment and the app never comes up:

```bash
kubectl apply -f demo/broken-app.yaml
kubectl get pods -n clustermate-demo
# broken-web-7d9f8c6b4-x2k9p   0/1   ImagePullBackOff   0   2m
```

## 2. Snapshot

```bash
python3 skills/clustermate/scripts/cluster_snapshot.py -n clustermate-demo -o /tmp/snapshot.json
# snapshot written to /tmp/snapshot.json (1 unhealthy pods)
```

The snapshot captures the pod's `ImagePullBackOff` state plus the cluster event:

```json
{ "reason": "Failed", "message": "Failed to pull image \"nginx:9.9.9-nonexistent\": ... not found",
  "object": "Pod/broken-web-7d9f8c6b4-x2k9p", "count": 5 }
```

## 3. Diagnosis (local open-weight model, offline)

```bash
python3 skills/clustermate/scripts/diagnose.py --snapshot /tmp/snapshot.json
```

Model output (abridged):

> ## Summary
> The `broken-web` Deployment cannot start because Kubernetes cannot download
> its container image `nginx:9.9.9-nonexistent` — that tag does not exist.
>
> ## Root cause
> Wrong image tag in the Deployment manifest.
>
> ## Evidence
> - Container state `ImagePullBackOff` on pod `broken-web-…`
> - Event `Failed to pull image "nginx:9.9.9-nonexistent"` (count 5)
>
> ## Suggested fix
> 1. `kubectl set image deployment/broken-web web=nginx:1.27 -n clustermate-demo`
> 2. `kubectl rollout status deployment/broken-web -n clustermate-demo`
>
> ## اردو میں وضاحت
> آپ کی ایپ اس لیے نہیں چل رہی کیونکہ … (plain-Urdu explanation of the bad tag and the fix)

## 4. Fix and verify

```bash
kubectl set image deployment/broken-web web=nginx:1.27 -n clustermate-demo
kubectl get pods -n clustermate-demo
# broken-web-7d9f8c6b4-x2k9p   1/1   Running   0   30s
```

Total time: under two minutes, no cloud API, no API key, full data privacy.
