
# Kubernetes Deployment Validation, Versioning and Rollback

## 1. Overview

This document records deployment validation, container image versioning and rollback testing completed for the Control API in the DevOps Group Project.

**Jira Story:** SCRUM-185  
**Environment:** Windows Docker Desktop with a three-node KinD Kubernetes cluster  
**Namespace:** `devops`  
**Deployment:** `control-api`  
**GitHub PR:** https://github.com/D00281102/Devops_Group_Project/pull/40

## 2. Deployment Health Validation

The Control API deployment was checked using:

```cmd
kubectl get deployments -n devops
```

Result:

```text
NAME          READY   UP-TO-DATE   AVAILABLE
control-api   1/1     1            1
```

Deployment rollout was verified using:

```cmd
kubectl rollout status deployment/control-api -n devops
```

Result:

```text
deployment "control-api" successfully rolled out
```

**Result: PASS**

The Control API deployment was healthy with one ready and available replica.

## 3. Container Image Versioning

The deployment originally used:

```text
iot-control-api:local
```

A versioned Docker image tag was created using:

```cmd
docker tag iot-control-api:local iot-control-api:v1.0.0
```

The versioned image was loaded into all three local KinD nodes:

```cmd
kind load docker-image iot-control-api:v1.0.0 --name kind
```

The deployment was updated:

```cmd
kubectl set image deployment/control-api control-api=iot-control-api:v1.0.0 -n devops
```

Verification:

```cmd
kubectl get deployment control-api -n devops -o jsonpath="{.spec.template.spec.containers[0].image}"
```

Result:

```text
iot-control-api:v1.0.0
```

The image reference was also updated in `k8s/control-api.yaml` and committed to the SCRUM-185 feature branch.

**Result: PASS**

The local deployment successfully used the versioned Control API image.

**Limitation:** The `v1.0.0` image is currently a locally tagged image. It has not been verified as published to an external container registry. Other environments must have access to the image before deploying this configuration.

## 4. Deployment Rollout Validation

The versioned deployment was validated using:

```cmd
kubectl rollout status deployment/control-api -n devops --timeout=120s
```

Result:

```text
deployment "control-api" successfully rolled out
```

The Deployment reached the required available replica count.

Kubernetes deployment history was inspected using:

```cmd
kubectl rollout history deployment/control-api -n devops
```

The available revisions included:

```text
REVISION  CHANGE-CAUSE
2         <none>
3         <none>
4         <none>
```

Revision 4 used `iot-control-api:v1.0.0`.

Revision 3 used `iot-control-api:local`.

Both revisions contained startup, readiness and liveness probes.

**Result: PASS**

The deployment rollout completed successfully, and the available revision history was verified.

## 5. Controlled Rollback Test

A controlled rollback was performed on the local KinD cluster.

### Step 1 — Restore the Previous Revision

The deployment was rolled back to revision 3:

```cmd
kubectl rollout undo deployment/control-api -n devops --to-revision=3
```

Result:

```text
deployment.apps/control-api rolled back
```

### Step 2 — Verify the Rollback

The rollout status was checked:

```cmd
kubectl rollout status deployment/control-api -n devops --timeout=120s
```

Result:

```text
deployment "control-api" successfully rolled out
```

The deployed image was checked:

```cmd
kubectl get deployment control-api -n devops -o jsonpath="{.spec.template.spec.containers[0].image}"
```

Result:

```text
iot-control-api:local
```

**Rollback result: PASS**

The previous deployment configuration was restored successfully.

### Step 3 — Restore the Intended Version

The Control API was returned to `v1.0.0`:

```cmd
kubectl set image deployment/control-api control-api=iot-control-api:v1.0.0 -n devops
```

Result:

```text
deployment.apps/control-api image updated
```

The rollout was checked again:

```cmd
kubectl rollout status deployment/control-api -n devops --timeout=120s
```

Result:

```text
deployment "control-api" successfully rolled out
```

Final image verification returned:

```text
iot-control-api:v1.0.0
```

**Restoration result: PASS**

The deployment returned to the intended version after rollback testing.

## 6. Test Summary

| Test | Result |
|---|---|
| Deployment health validation | PASS |
| Initial rollout status | PASS |
| Versioned image loaded into KinD | PASS |
| Deployment updated to v1.0.0 | PASS |
| Versioned image verification | PASS |
| Revision history inspection | PASS |
| Rollback to previous revision | PASS |
| Previous image restored | PASS |
| Redeployment of v1.0.0 | PASS |
| Final rollout verification | PASS |

## 7. Scope and Limitations

The tests were performed on the local Windows KinD cluster and focused on the Control API.

The following were not demonstrated:

- Deployment validation across all project services.
- Rollback following an actual failed application release.
- Rollback on the XOA-hosted Kubernetes cluster.
- Image distribution through an external container registry.

The rollback test used two image tags referencing the same locally built image. Therefore, it verifies Kubernetes Deployment revision management and rollback behaviour, rather than recovery between different application builds.

## 8. GitHub and Jira Evidence

**Feature branch:** `feature/SCRUM-185-deployment-recovery`

**Image versioning commit:** `1a95e44`

**Pull Request:** https://github.com/D00281102/Devops_Group_Project/pull/40

**Jira:** SCRUM-185

Screenshots of deployment health, image versioning, rollout validation and rollback verification are attached to the relevant Jira subtasks.

## 9. Conclusion

Deployment health validation, container image versioning and controlled rollback testing were completed successfully for the Control API on the local KinD cluster.

Kubernetes successfully restored the previous deployment revision, and the Control API was subsequently returned to `iot-control-api:v1.0.0`.

The results demonstrate successful local Deployment revision management and recovery testing for the Control API.
