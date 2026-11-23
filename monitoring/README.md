# Platform Monitoring & Observability Operations

## 1. Stack Overview & Sizing
- **Helm Chart:** `prometheus-community/kube-prometheus-stack` (pinned version: `92.16.1` in `monitoring/stack/chart-version.txt`)
- **Argo CD Applications:**
  - `platform-monitoring` (`AppProject: platform-system`) — deploys the core Prometheus Operator, Prometheus, Alertmanager, Grafana, `kube-state-metrics`, and `prometheus-node-exporter`.
  - `platform-observability` (`AppProject: platform-system`) — deploys application-level `ServiceMonitor`, `PrometheusRule`, and Grafana dashboard `ConfigMap` from `monitoring/resources/`.
- **Storage & Retention:**
  - Prometheus TSDB PVC: `5Gi` (`standard-rwo`, `ReadWriteOnce`)
  - Retention window: `24h` / `3GB` (`scrapeInterval: 30s`, application `ServiceMonitor` interval: `15s`, `evaluationInterval: 15s`)
  - Grafana storage: ephemeral in-cluster DB with declarative dashboard provisioning via sidecar (`grafana_dashboard: "1"`).

## 2. GKE-Specific Design Decisions
- **Managed Control Plane Endpoints Disabled:** In GKE, `kube-controller-manager`, `kube-scheduler`, `etcd`, and `kube-proxy` internal scrape endpoints are managed by Google and not exposed to tenant Prometheus pods. Their scrape targets and default alerting rules are explicitly disabled in `monitoring/stack/values.yaml` to avoid false-positive `TargetDown` alerts.
- **Operator Admission Webhooks Disabled:** `prometheusOperator.admissionWebhooks.enabled: false` and `tls.enabled: false` are set so the compact cluster does not require control-plane-to-pod webhook firewall rules or `cert-manager`. Manifests are validated via `kubectl apply --dry-run=server` and live Prometheus `/api/v1/rules` evaluation.
- **External Secrets (Out-of-Band from Git):**
  - `monitoring/grafana-admin` (`admin-user`, `admin-password`)

## 3. Local Access (Port-Forward Commands)
```bash
# Prometheus UI (http://localhost:9090)
kubectl port-forward -n monitoring svc/platform-monitoring-prometheus 9090:9090

# Grafana UI (http://localhost:3000)
kubectl port-forward -n monitoring svc/platform-monitoring-grafana 3000:80

# Alertmanager UI (http://localhost:9093)
kubectl port-forward -n monitoring svc/platform-monitoring-alertmanager 9093:9093

# Retrieve Grafana admin password locally
kubectl get secret grafana-admin -n monitoring -o jsonpath='{.data.admin-password}' | base64 -d && echo ""
```

## 4. Configured Dashboards & Alert Rules
### Dashboards
1. **Python GKE Platform (`uid: python-platform`):** 8 panels covering RPS, 5xx error percentage, p50/p95/p99 latency quantiles, CPU usage per pod, memory working set, CPU CFS throttling %, PVC usage %, and memory limit usage %.
2. **On-Prem Edge Infrastructure (`uid: on-prem-edge-cm5`):** 4 panels visualizing Raspberry Pi CM5 Broadcom BCM2712 SoC temperature, NVMe SMART temperature & wear level, 27W USB-C PD throttling bitmask, and ZFS `datapool` capacity.

### Alerting Rules
- **Application Rules (`monitoring/resources/alerts.yaml`):**
  - `HighErrorRate`: HTTP 5xx ratio (excluding `/healthz` and `/ready`) `> 2%` for `3m`.
  - `PodCrashLooping`: Container restarts `increase[10m] > 3` for `1m`.
  - `HighDiskUtilization`: PVC `python-platform-data` usage `> 85%` for `2m`.
- **Hybrid Edge Hardware Rules (`monitoring/stack/templates/edge-cm5-monitoring.yaml`):**
  - `RPiCM5HighSoCTemperature`: BCM2712 SoC temperature `> 75C` for `2m`.
  - `RPiCM5UnderVoltageDetected`: `rpi_cm5_under_voltage_active > 0` for `1m`.
  - `RPiCM5ZFSPoolDegraded`: `rpi_cm5_zfs_pool_online_status == 0` for `1m`.

## 5. Verification Summary
- **2026-11-17T05:00:00Z:** Verified WireGuard L3 scraping of `10.200.0.2:9100` (`rpi-cm5-edge-exporter`) and live rendering of the `On-Prem Edge Infrastructure` dashboard in Grafana.
- **2026-11-23T17:28:26Z:** Verified `up{service="python-platform"} == 1` across `platform-staging` and `platform-production`, live RPS/latency PromQL queries after 329-request HTTP load test, PVC volume capacity metrics, and active rule evaluation in Prometheus (`docs/evidence/app-observability-verification.txt`).
