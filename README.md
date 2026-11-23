# Python GKE Platform — GitOps Repository

Declarative GitOps repository managed by **Argo CD** (App-of-Apps pattern) for the **Python GKE Platform** and **Raspberry Pi CM5 Hybrid Edge Extension**.

## Repository Structure
- `bootstrap/`
  - `argocd/` — Kustomize installation overlay for Argo CD.
  - `projects/` — RBAC-isolated Argo CD `AppProject` definitions:
    - `platform-root.yaml` — Root control-plane synchronization project.
    - `python-platform.yaml` — Application workloads (`platform-staging`, `platform-production`).
    - `platform-system.yaml` — Cluster monitoring & observability stack (`monitoring`, `kube-system`).
    - `platform-edge.yaml` — Hybrid Edge K3s workloads on Raspberry Pi CM5 over WireGuard (`https://10.200.0.2:6443`).
  - `applications/` & `root-application.yaml` — Child Argo CD `Application` definitions.
- `charts/python-platform/` — Application Helm chart (Deployment, Service, HPA, PVC, NetworkPolicy, PDB, Ingress, ManagedCertificate, BackendConfig, FrontendConfig).
- `environments/`
  - `staging/values.yaml` — Staging environment overrides and immutable image digest promoted by CI.
  - `production/values.yaml` — Production environment overrides, GCE Ingress, and Workload Identity settings.
- `edge/ingestion-service/` — Hybrid Edge Kubernetes manifests deployed to the Raspberry Pi CM5 K3s cluster (`edge-workloads` namespace) with ZFS `/srv/data/annotation` storage mount.
- `monitoring/`
  - `stack/` — Pinned `kube-prometheus-stack` values (`92.16.1`) and hybrid edge hardware scrape/alert templates.
  - `resources/` — Application `ServiceMonitor`, `PrometheusRule` alerts, and provisioned Grafana dashboard `ConfigMap`.
  - [`monitoring/README.md`](monitoring/README.md) — Operations guide, port-forward commands, and verification logs.
