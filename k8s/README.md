# Kubernetes deployment

The GitHub Actions workflow builds all four application images for pushes and
pull requests. It publishes images to GHCR only for pushes to this repository's
`main` branch. After a successful publish, it deploys the commit-tagged images
only when the repository variable `K8S_DEPLOY_ENABLED` is set to `true`.

The workflow deploys application workloads into the `iot-app` namespace. It
does not provision PostgreSQL, Kafka, or Mosquitto. Those services must already
be reachable inside the cluster using the service names and ports in
`applications.yaml.tmpl`, and the telemetry and control/authentication
databases and schemas must be initialized before deployment.

## One-time setup

1. Provide the cluster with PostgreSQL, Kafka, and Mosquitto services reachable
   as `postgres:5432`, `kafka:9093`, and `mosquitto:1883` from the `iot-app`
   namespace. If your service names or ports differ, update
   `applications.yaml.tmpl`.
2. Create the `iot-app` namespace and the application Secret. The Secret must
   contain `DB_PASSWORD` and `AUTH_SECRET_KEY`:

   ```sh
   kubectl apply -f k8s/namespace.yaml
   kubectl create secret generic iot-app-secrets \
     --namespace iot-app \
     --from-literal=DB_PASSWORD='<database-password>' \
     --from-literal=AUTH_SECRET_KEY='<auth-signing-key>'
   ```

3. Create an image-pull secret named `ghcr-pull-secret` in `iot-app` using a
   GitHub identity with read-only access to the GHCR packages:

   ```sh
   kubectl create secret docker-registry ghcr-pull-secret \
     --namespace iot-app \
     --docker-server=ghcr.io \
     --docker-username='<github-username>' \
     --docker-password='<read-packages-token>'
   ```

   Keep credentials out of shell history where possible and never commit them.
4. In GitHub, create the `production` environment, add a `KUBE_CONFIG` secret
   containing the kubeconfig file contents, and configure required reviewers
   if deployments should be approved. Use a Kubernetes identity scoped to the
   `iot-app` namespace rather than a cluster-admin identity.
5. Add the repository Actions variable `K8S_DEPLOY_ENABLED` with value `true`.
   Leave it unset or set to another value to keep automatic deployment disabled.

The deployment workflow applies the namespace and application manifests,
substitutes the commit SHA into each GHCR image reference, and waits for all
application Deployments to complete their rollouts. The API readiness probe checks
the telemetry endpoint, which also verifies its database connection. The API
Service is `ClusterIP`; use a cluster Ingress or `kubectl port-forward` to
access it from outside the cluster.

The Sensor Simulator and Actuator Simulator images are built and published by
CI but are not deployed as production workloads. The sensor simulator requires
a CSV dataset that is not included in the repository; the actuator simulator
is a local test substitute for physical actuators.

The workflow does not run database-backed tests, migrate an existing database,
or deploy the PostgreSQL/Kafka/MQTT infrastructure. Those need separate
cluster provisioning and backup/migration plans.
