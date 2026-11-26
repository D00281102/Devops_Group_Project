
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

The liveness probe allows Kubernetes to detect an unhealthy API and restart its container after repeated probe failures.

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

The container was running, its readiness condition was true, and no warning events were recorded.

## 4. Automatic Recovery Test

To test recovery, the running Control API pod was deleted:

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

The deployment was also checked:

```cmd
kubectl get deployment control-api -n devops
```

Result:

```text
NAME          READY   UP-TO-DATE   AVAILABLE
control-api   1/1     1            1
```

**Result: PASS**

The Kubernetes Deployment successfully replaced the deleted pod and restored the desired replica count without manual intervention.

## 5. Validation and Limitations

The updated YAML passed a local syntax check:

```cmd
python -c "import yaml; list(yaml.safe_load_all(open('k8s/control-api.yaml'))); print('YAML syntax valid')"
```

Result:

```text
YAML syntax valid
```

The following checks were completed:

- Startup, readiness and liveness probes were confirmed in the running pod.
- The Control API reached `1/1 Running`.
- The readiness condition was `True`.
- Automatic pod replacement was successfully demonstrated.
- The Deployment returned to `1/1` available replicas.

### Outstanding Testing

A container termination test was attempted, but no increase in the restart count was observed.

Therefore, a restart triggered specifically by a failing liveness probe has not yet been demonstrated.

The successful recovery test verifies Deployment-level pod replacement rather than liveness-triggered container restart.

The tests were performed on the local Windows KinD cluster, not the XOA-hosted cluster.

## 6. GitHub Evidence

**Branch:** `feature/SCRUM-190-health-checks`

**Startup probe commit:** `ca5d94e`

**Pull Request:** [Improve Kubernetes Service Health Monitoring](https://github.com/D00281102/Devops_Group_Project/pull/39)

## 7. Conclusion

The Control API health probes were configured and verified on the local Kubernetes cluster.

The API reached a healthy and ready state, and Kubernetes successfully restored the Deployment after its pod was deleted.

Further testing is required to demonstrate a container restart caused specifically by liveness probe failure.
