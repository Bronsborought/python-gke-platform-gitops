# Python GKE Platform GitOps

ArgoCD configuration for staging and production.

## Repositories

- Application, Terraform and Helm:
  [https://github.com/Bronsborought/python-gke-platform](https://github.com/Bronsborought/python-gke-platform)
- Environment values and ArgoCD Applications:
  this repository.

## Layout

- bootstrap/argocd: pinned ArgoCD installation and configuration.
- bootstrap/projects: ArgoCD AppProjects.
- bootstrap/root-application.yaml: root Application.
- applications: child Applications.
- environments: environment-specific Helm values.

## Bootstrap

With the intended GKE context selected:

```bash
kubectl create namespace argocd --dry-run=client -o yaml |
  kubectl apply -f -

kubectl apply --server-side -k bootstrap/argocd
kubectl apply -f bootstrap/projects
kubectl apply -f bootstrap/root-application.yaml
```

The application namespaces and external Secrets must exist before sync.

Required Secrets in each application namespace:

- jfrog-registry
- python-platform-app

Secret values are not stored in this repository.

## ArgoCD access

```bash
kubectl port-forward -n argocd service/argocd-server 8080:443
```

Open https://localhost:8080.

Change the initial admin password after bootstrap.

## Ownership

ArgoCD manages the application resources.

Do not run manual Helm upgrade, rollback or uninstall against the
managed environments after handover.

Historical Helm release Secrets may remain from the initial deployment.

## Sources

The Helm chart is pinned to a commit in the application repository.
Values are read from the main branch of this repository.

Image digests identify the exact deployed image.

## Reconciliation

Applications use automated sync, prune and self-heal.
The root Application manages child Application definitions.

PVC deletion and pruning require explicit confirmation.

Do not force or replace persistent resources to resolve a sync problem.

## Verification

- Both application Applications report Synced and Healthy.
- Root Application reports Synced.
- A manual Deployment CPU-request change is restored from Git.
- Record the observed self-heal duration.
- An application pod can read the designated GCS object using
  Workload Identity without a service-account JSON key.

## Storage limitation

The current chart colocates replicas on one node for standard-rwo
storage. This does not provide application availability during a node
failure. The limitation remains until the storage architecture changes.

## Future system applications

The observability stage adds a Prometheus-stack Application.
GKE manages the existing GCE Ingress controller.

## Teardown

Do not destroy the cluster before removing managed Ingress resources
and allowing cloud load-balancer cleanup.

PVC deletion must be deliberate.

Stop automated reconciliation before manually removing resources
during final teardown; otherwise ArgoCD can recreate them.
