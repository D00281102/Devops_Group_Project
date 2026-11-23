# GitOps deployment with Argo CD

## What this setup does

GitHub Actions runs the existing Python checks and builds the application
containers. On a push to `main`, it publishes the images to GHCR using the
source commit SHA as the image tag and refreshes the `latest` alias. After all
image builds succeed, a second job updates the two production image tags in
`k8s/kustomization.yaml` and pushes that GitOps change to `main`.

Argo CD watches the `k8s` directory on `main`. It notices the image-tag commit,
renders the Kustomize resources, and synchronizes them to the cluster. It also
detects manual drift and corrects it, removes resources that have been deleted
from the tracked manifests, and reports sync and workload health in its UI.
GitHub Actions does not connect to Kubernetes and does not need a cluster
kubeconfig.

The Argo CD Application is defined in `argocd/application.yaml`. Its sync
policy enables automatic sync, pruning, self-healing, namespace creation, and
retries. `kustomization.yaml` collects `namespace.yaml` and
`applications.yaml`; its image transformers replace the `latest` placeholder
with the commit-specific image tags written by CI. The `latest` tag is only a
bootstrap alias; deployments after the first successful CI run use the
immutable commit-specific tags recorded in Git. The Application manifest is
bootstrapped separately; it is not one of the resources managed by the
Application it creates.

The managed workloads are `control-api` and `control-logic`. CI also builds the
sensor and actuator simulator images, but those simulators are not production
workloads in this Kubernetes configuration.

## Cluster prerequisites

- A Kubernetes cluster and a working `kubectl` context.
- PostgreSQL, Kafka, and Mosquitto reachable from namespace `iot-app` as
  `postgres:5432`, `kafka:9093`, and `mosquitto:1883`. The database schemas
  must be initialized separately. The Compose services in this repository do
  not automatically become services inside a Kubernetes cluster.
- The `iot-app-secrets` secret with `DB_PASSWORD` and `AUTH_SECRET_KEY`.
- The `ghcr-pull-secret` secret with a GitHub identity that can read the
  published GHCR images. Create it even if the package is public, unless you
  remove the `imagePullSecrets` entries from the workload manifests.
- The repository must be readable by Argo CD. For a private repository,
  configure a read-only GitHub credential in Argo CD's **Settings >
  Repositories** before creating the Application. Do not put that credential
  in Git.
- The GitHub Actions token must be allowed to push the image-tag update commit
  to `main`. In **Settings > Actions > General**, allow workflow tokens read
  and write access. If branch protection blocks the bot, CI reports a failed
  `Update GitOps image tags` job; allow the GitHub Actions bot to update the
  GitOps file or change the workflow to open a reviewed pull request instead.

## Activate Argo CD (PowerShell)

Run these commands from the repository root. They install Argo CD into the
current Kubernetes context; check `kubectl config current-context` first to
avoid installing it in the wrong cluster.

```powershell
kubectl config current-context
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=Available deployment/argocd-server -n argocd --timeout=300s
kubectl wait --for=condition=Available deployment/argocd-repo-server -n argocd --timeout=300s
```

Prepare the namespace and runtime secrets before the first sync:

```powershell
kubectl apply -f k8s\namespace.yaml
kubectl create secret generic iot-app-secrets `
  --namespace iot-app `
  --from-literal=DB_PASSWORD='<database-password>' `
  --from-literal=AUTH_SECRET_KEY='<auth-signing-key>'
kubectl create secret docker-registry ghcr-pull-secret `
  --namespace iot-app `
  --docker-server=ghcr.io `
  --docker-username='<github-username>' `
  --docker-password='<read-packages-token>'
```

Use your own values for the placeholders. Avoid entering real credentials in
commands that are saved in shell history. These Secrets are deliberately
created outside Git and are not managed or overwritten by Argo CD.

If GitHub Actions is already publishing images, the manifests may reference a
newer commit-tagged image as soon as the workflow completes. Create the Argo CD
Application to start reconciliation:

```powershell
kubectl apply -f k8s\argocd\application.yaml
kubectl get applications.argoproj.io -n argocd
kubectl get deployments,pods,services -n iot-app
```

If the repository is private, also add its read-only credential in Argo CD
before applying the Application. The UI provides a repository connection check.

## Test a feature branch in the local kind cluster

The committed Application manifest targets `main` for the production GitOps
flow. To test feature-branch work locally without changing that production
configuration, update only the Application object in the local kind cluster.
Argo CD reads the branch from GitHub, so the branch must exist remotely and
your changes must be committed and pushed to that branch; uncommitted local
files are not visible to Argo CD.

Confirm the current branch and that GitHub has the remote branch:

```powershell
git branch --show-current
git ls-remote --heads origin Jo
```

After confirming the intended branch name, point the local Application at it
with `kubectl edit` (change `spec.source.targetRevision` to the exact remote
branch name, for example `Jo`), save, and request a refresh:

```powershell
kubectl edit application iot-app -n argocd
kubectl annotate application iot-app -n argocd `
  argocd.argoproj.io/refresh=hard --overwrite
kubectl get application iot-app -n argocd -o wide
kubectl describe application iot-app -n argocd
```

Replace `Jo` if the remote branch name differs. This edit changes only the
Application in the local kind cluster; do not commit a `targetRevision: Jo`
change to the production Application manifest. Once the branch has been merged
to `main`, point the local Application back to `main` by editing
`spec.source.targetRevision`:

```powershell
kubectl edit application iot-app -n argocd
kubectl annotate application iot-app -n argocd `
  argocd.argoproj.io/refresh=hard --overwrite
```

## Team workflow: merge changes to main and deploy with Argo CD

Argo CD's committed Application targets `main`. Each team member should work
on their own feature branch, push commits to that branch, and open a reviewed
pull request to `main`. Argo CD does not deploy everyone's feature branches
independently; each approved merge updates the shared desired state on `main`.

Before merging a deployment change, confirm that the required manifests and
their referenced files are included in the pull request under `k8s/`, and
that the Kustomize build is valid. Do not merge a personal `targetRevision`
such as `Jo` into the production Application manifest.

After the pull request is merged:

1. Confirm the remote `main` branch contains the merged commit and manifests.
2. If the local kind Application was pointed at a feature branch, run
   `kubectl edit application iot-app -n argocd` and set
   `spec.source.targetRevision` back to `main`. This only changes the local
   kind Application.
3. Trigger a refresh and check the Application status:

   ```powershell
   kubectl annotate application iot-app -n argocd `
     argocd.argoproj.io/refresh=hard --overwrite
   kubectl get application iot-app -n argocd -o wide
   kubectl describe application iot-app -n argocd
   ```

4. For application image changes, confirm the GitHub Actions build and
   `Update GitOps image tags` job succeeded. CI publishes commit-tagged
   images and records the production tags in `k8s/kustomization.yaml`.
   Argo CD then automatically reconciles the merged Git revision.

Because automated sync and pruning are enabled, Argo CD applies the desired
resources from `main` and removes managed resources no longer present there.
Review changes to the Kustomize resource list before merging.

## View deployment status

In one PowerShell window, forward the Argo CD UI port:

```powershell
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Open `https://localhost:8080` and sign in as `admin`. Retrieve the initial
password in another window:

```powershell
$encodedPassword = kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}"
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($encodedPassword))
```

The `iot-app` Application page shows the Git revision, sync state, health, and
each managed Kubernetes resource. For command-line status, use:

```powershell
kubectl get application iot-app -n argocd -o wide
kubectl describe application iot-app -n argocd
kubectl get deployments,pods,services -n iot-app
kubectl rollout status deployment/control-api -n iot-app --timeout=180s
kubectl rollout status deployment/control-logic -n iot-app --timeout=180s
```

Test the API from a second terminal:

```powershell
kubectl port-forward service/control-api -n iot-app 8000:8000
Invoke-WebRequest http://localhost:8000/telemetry/
```

The readiness endpoint also checks the API's telemetry/database path. The
service is `ClusterIP`; port-forwarding is for local testing, not public
exposure.

## Test an automatic GitOps deployment

After the prerequisites and Application are ready, merge an approved change
to `main`. For an image change, CI must pass and publish the image before it updates
`k8s/kustomization.yaml`. Argo CD then detects that Git revision and syncs it.
Watch the Actions run, the Application sync/health state, and the pod rollout
using the status commands above.

For a configuration-only Git commit, edit the manifests under `k8s` and push
the change to `main`; Argo CD syncs it without a Kubernetes credential in
GitHub Actions. Changes made directly with `kubectl` to managed resources are
reverted by `selfHeal`. To intentionally remove a managed resource, remove it
from Git; `prune` allows Argo CD to delete it from the cluster.

## Verification and evidence for Jira

### What has been verified so far

The reported local test output confirms that kind created the
`iot-gitops` cluster, `kubectl` switched to `kind-iot-gitops`, and all listed
Argo CD pods reached `1/1 Running`.

On 2026-11-23, the `iot-app` Application successfully read the public `Jo`
branch at revision `12af1a2d603a896b761370ed69cd0147ada1b83d` and completed an
automated sync. The Application reported `Synced` and `Healthy`. Its current
resource inventory contains only the `iot-app` Namespace; there are no
application Deployments, Pods, or Services in that namespace yet. Therefore
repository access and Argo CD synchronization are verified, but the
application workloads and API are not.

The Application has pruning enabled. When its target revision changed from
`main` to `Jo`, Argo CD pruned resources that existed only in the previous
revision from this local cluster. This is expected GitOps behavior; verify the
target branch's manifests before changing revisions.

### Commands to capture verification output

Run these from the repository root in PowerShell:

```powershell
kubectl config current-context
kind get clusters
kubectl get nodes -o wide
kubectl get pods -n argocd -o wide
```

Expected: context `kind-iot-gitops`, the `iot-gitops` cluster is listed, the
kind node is `Ready`, and Argo CD pods are `Running` with all containers
ready.

After repository access and application prerequisites are configured, apply
the Application and inspect its sync and health:

```powershell
kubectl apply -f k8s\argocd\application.yaml
kubectl get application iot-app -n argocd -o wide
kubectl describe application iot-app -n argocd
kubectl get deployments,pods,services -n iot-app
kubectl rollout status deployment/control-api -n iot-app --timeout=180s
kubectl rollout status deployment/control-logic -n iot-app --timeout=180s
```

For end-to-end evidence, both rollouts should complete, the Application should
show `Synced` and `Healthy`, and the API check should succeed:

```powershell
kubectl port-forward service/control-api -n iot-app 8000:8000
```

In another terminal:

```powershell
Invoke-WebRequest http://localhost:8000/telemetry/
```

Verify the GitOps automation separately: record a successful main-branch
Actions run, confirm that `k8s/kustomization.yaml` contains the published
commit SHA tags, and confirm the Application has reconciled that Git revision.
Do this with a normal team-approved change; do not make an unreviewed
production change just to create evidence.

### Screenshot placement in Jira

Attach actual screenshots to the Jira issue; these labels are suggested
captions, not screenshots already captured:

1. **Kind and Argo CD ready:** PowerShell output for the current context,
   `kubectl get nodes -o wide`, and `kubectl get pods -n argocd -o wide`.
2. **Application sync and health:** Argo CD Applications page showing
   `iot-app`, its sync status, health, and Git revision.
3. **Managed resources:** Argo CD application resource tree showing the API,
   control-logic, ConfigMap, and Service.
4. **CI to GitOps update:** GitHub Actions successful build/update jobs and
   the Git commit containing the image-tag change.
5. **Application check (after prerequisites):** successful rollout output and
   the API response from `/telemetry/`.

Do not include passwords, tokens, kubeconfig contents, or secret values in
screenshots or Jira comments. If an application check is blocked by missing
cluster dependencies, capture the status and record the blocker rather than
claiming the application is healthy.

## Jira-ready update

**Title:** Implement GitOps deployment management with Argo CD

**Update:** Argo CD has been installed in a local kind cluster. The reported
output shows the kind cluster was created and all listed Argo CD pods are
`1/1 Running`. The repository now contains an Argo CD Application configured
to watch `main` at `k8s/`, with automated sync, self-healing, pruning, and
retries. GitHub Actions is configured to publish commit-tagged GHCR images and
record production image tags in Kustomize.

**Current proof boundary:** The Argo CD control plane is verified. Application
sync, workload health, successful CI image publication, and API response are
not yet evidenced. Complete those checks after repository/GHCR access, runtime
secrets, and PostgreSQL/Kafka/Mosquitto connectivity are configured for the
kind cluster.

**Subtasks:**

1. **Provision local Kubernetes and Argo CD** — Create the `iot-gitops` kind
   cluster, select its kubectl context, install Argo CD, and verify all Argo CD
   pods are ready. **Evidence:** screenshot 1. **Status:** completed according
   to the reported terminal output.
2. **Configure the Argo CD Application and repository access** — Apply
   `k8s/argocd/application.yaml`, confirm Argo CD can read the repository, and
   verify the local Application tracks the intended branch at `k8s/`.
   Configure read-only repository credentials first if the repository is
   private. **Evidence:** screenshot 2. **Status:** completed for public
   branch `Jo`; Application reported `Synced`/`Healthy` at revision
   `12af1a2d603a896b761370ed69cd0147ada1b83d`. The current branch contains
   only the `iot-app` Namespace in the managed resource inventory.
3. **Automate image publishing and GitOps updates** — Verify the main-branch
   Actions workflow builds and publishes commit-tagged images, updates
   `k8s/kustomization.yaml`, and pushes the GitOps change. Confirm the
   workflow token and branch rules allow that update. **Evidence:** screenshot
   4. **Status:** the workflow is configured in the local worktree, but the
   remote `Jo` branch still has the previous workflow and `main` does not yet
   have this GitOps workflow. Push the reviewed changes to `Jo`, then merge
   them to `main`. Publishing and the image-tag commit only run on `main`, so
   verify those after the merge.
4. **Validate deployment health and visibility** — Configure GHCR pull access,
   application secrets, and PostgreSQL/Kafka/Mosquitto connectivity; verify
   `Synced`/`Healthy`, both Deployment rollouts, and the API endpoint.
   **Evidence:** screenshots 3 and 5. **Status:** pending these prerequisites
   and runtime checks.

**Acceptance checks:** the Application is `Synced` and `Healthy`; a successful
main-branch build updates the Git image tags and rolls out both Deployments;
the API endpoint responds; and the Argo CD UI and kubectl show matching
revision and workload health. Keep screenshots 1–5 with the Jira issue as
evidence for the checks completed.
