
# Kubernetes Service Health Checks and Recovery

## 1. Overview

This document records the health checks and automatic recovery tests carried out for the Control API in the DevOps Group Project.

**Jira Story:** SCRUM-190  
**Environment:** Windows Docker Desktop with a local three-node KinD Kubernetes cluster  
**Namespace:** `devops`  
**Deployment:** `control-api`

## 2. Health Probe Configuration

The Control API deployment is configured with three Kubernetes health probes in `k8s/control-api.yaml`.

### Startup Probe

- Type: HTTP GET
- Endpoint: `/`
- Port: 8000 (`http`)
- Period: 10 seconds
- Failure threshold: 30

The startup probe allows up to approximately 300 seconds for the API to become healthy before liveness and readiness checks begin.

### Readiness Probe

- Type: HTTP GET
- Endpoint: `/`
- Port: 8000 (`http`)
- Initial delay: 10 seconds
- Period: 10 seconds

The readiness probe determines whether the pod is ready to receive traffic.

### Liveness Probe

- Type: HTTP GET
- Endpoint: `/`
- Port: 8000 (`http`)
- Initial delay: 30 seconds
- Period: 20 seconds
- Failure threshold: 3 (Kubernetes default)

The liveness probe detects unhealthy API containers and triggers a restart after repeated failures.

## 3. Deployment and Verification

The Control API Docker image was tagged as `iot-control-api:local` and loaded into the local KinD cluster.

The required Kubernetes namespace and environment Secret were created.

The deployment was applied using:

```cmd
kubectl apply -f k8s\control-api.yaml
```

Result:

```text
deployment.apps/control-api created
service/control-api created
```

Pod health was checked using:

```cmd
kubectl get pods -n devops
```

Result:

```text
control-api-64dbb6b7c8-6ftdz   1/1   Running   0
```

A pod description confirmed that the startup, readiness and liveness probes were configured.

The container was running, its readiness condition was true, and no warning events were recorded during the initial verification.

## 4. Automatic Recovery Tests

### Test 1 — Automatic Pod Replacement

To test Deployment-level recovery, the running Control API pod was deleted:

```cmd
kubectl delete pod -n devops -l app.kubernetes.io/name=control-api
```

Result:

```text
pod "control-api-64dbb6b7c8-6ftdz" deleted from devops namespace
```

Kubernetes automatically created a replacement pod.

Verification:

```cmd
kubectl get pods -n devops
```

Result:

```text
control-api-64dbb6b7c8-sjb22   1/1   Running   0
```

The Deployment was also checked:

```cmd
kubectl get deployment control-api -n devops
```

Result:

```text
NAME          READY   UP-TO-DATE   AVAILABLE
control-api   1/1     1            1
```

**Result: PASS**

Kubernetes restored the desired replica count without manual intervention.

### Test 2 — Liveness-Triggered Container Restart

To test the liveness probe, its HTTP path was temporarily changed from `/` to `/health-test-fail` on the local Deployment.

The temporary configuration was applied using:

```cmd
kubectl patch deployment control-api -n devops --type=json -p="[{\"op\":\"replace\",\"path\":\"/spec/template/spec/containers/0/livenessProbe/httpGet/path\",\"value\":\"/health-test-fail\"}]"
```

Result:

```text
deployment.apps/control-api patched
```

The new pod initially showed:

```text
control-api-747bcf5dc8-m6jrz   1/1   Running   0
```

A subsequent pod description recorded:

```text
Warning  Unhealthy  Liveness probe failed: HTTP probe failed with statuscode: 404
```

After repeated failed liveness checks, Kubernetes restarted the container:

```text
control-api-747bcf5dc8-m6jrz   0/1   Running   1 (15s ago)
```

The restart count increased from `0` to `1`.

**Result: PASS**

This demonstrated that Kubernetes detected repeated liveness probe failures and restarted the container automatically.

### Test 3 — Restore the Healthy Configuration

The original deployment configuration was restored:

```cmd
kubectl apply -f k8s\control-api.yaml
```

Result:

```text
deployment.apps/control-api configured
service/control-api unchanged
```

The final pod check showed:

```text
control-api-64dbb6b7c8-gzkr6   1/1   Running   0
```

**Result: PASS**

The Control API returned to a healthy state with the correct liveness endpoint restored.

The final pod's restart count is `0` because it is a newly created pod.

## 5. Validation and Test Summary

The updated YAML passed local syntax validation:

```cmd
python -c "import yaml; list(yaml.safe_load_all(open('k8s/control-api.yaml'))); print('YAML syntax valid')"
```

Result:

```text
YAML syntax valid
```

| Test | Result |
|---|---|
| YAML syntax validation | PASS |
| Startup probe configuration | PASS |
| Readiness probe verification | PASS |
| Liveness probe configuration | PASS |
| Automatic pod replacement | PASS |
| Liveness-triggered container restart | PASS |
| Restoration of healthy configuration | PASS |

### Scope and Limitations

Testing was performed on the local Windows KinD cluster rather than the XOA-hosted cluster.

The tests focused on the Control API. Other project services were not included in these recovery tests.

The results demonstrate successful local health monitoring and recovery, but they do not constitute full end-to-end system testing.

## 6. GitHub Evidence

**Branch:** `feature/SCRUM-190-health-checks`

**Startup probe commit:** `ca5d94e`

**Initial documentation commit:** `25e11b5`

**Pull Request:** [Improve Kubernetes Service Health Monitoring](https://github.com/D00281102/Devops_Group_Project/pull/39)

Additional screenshots of probe configuration, failed liveness checks, automatic restart and successful recovery are attached to the relevant Jira subtasks.

## 7. Conclusion

The Control API health checks were configured and verified successfully on the local Kubernetes cluster.

Kubernetes automatically replaced a deleted pod and restarted a container after repeated liveness probe failures.

After restoring the original configuration, the Control API returned to `1/1 Running`.

The Control API health monitoring and recovery tests for SCRUM-190 were completed successfully in the local test environment.
