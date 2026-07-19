# Running SupTech-XAI on OpenShift

These manifests deploy the pipeline as a set of OpenShift-native workloads. One
image (`suptech-xai`) runs every component; the container `command` selects the
role (FMR mock, metrics API, dashboard, or the batch pipeline).

## What gets deployed

| Workload | Kind | Role | Exposed |
|---|---|---|---|
| `suptech-xai` | ImageStream + BuildConfig | builds the app image from `Containerfile` | — |
| `kafka` | Deployment + Service | ephemeral single-node Kafka (KRaft) | in-cluster |
| `fmr` | Deployment + Service + Route | mock Fusion Metadata Registry (SDMX-REST + `/ws/public/data/validate`) | Route |
| `metrics-api` | Deployment + Service + Route | analytics/evaluation REST API (`/metrics/*`) | Route |
| `dashboard` | Deployment + Service + Route | Streamlit analytics dashboard | Route |
| `suptech-pipeline` | CronJob | scheduled end-to-end batch run | logs |

The `metrics-api` and `dashboard` pods each run the full pipeline in an
**initContainer** into a per-pod volume, so they are self-contained and start
cleanly on any cluster (no shared RWX storage required).

## OpenShift compatibility

- Image runs under the **restricted-v2 SCC**: no fixed root UID; the `/app` tree
  is group-`0` owned and group-writable, so OpenShift's arbitrary assigned UID
  can read/write it.
- Containers set `runAsNonRoot`, drop all capabilities, disable privilege
  escalation, and use the `RuntimeDefault` seccomp profile.
- Services listen on unprivileged ports (8000 / 8001 / 8501); Routes use edge TLS.

## Deploy

```bash
# 1. Target a project
oc new-project suptech-xai

# 2. Create the ImageStream + BuildConfig, then build the image from local source
oc apply -f openshift/imagestream.yaml -f openshift/buildconfig.yaml
oc start-build suptech-xai --from-dir=. --follow

# 3. Deploy everything (Deployments pick up the freshly built image via triggers)
oc apply -k openshift/

# 4. Open the UIs
oc get route dashboard   metrics-api   fmr
```

Tear down with `oc delete -k openshift/` (and `oc delete is/suptech-xai bc/suptech-xai`).

## Notes for production

- Replace the ephemeral `kafka` Deployment with the **Strimzi** operator.
- For shared pipeline artifacts across pods, add a `ReadWriteMany` PVC and mount
  it in place of the per-pod `emptyDir`, and run the pipeline as a Job/CronJob
  that writes to it.
- Point `OLLAMA_BASE_URL` at a deployed Ollama service (GPU node) to enable real
  LLM explanations; otherwise the deterministic fallback is used.
