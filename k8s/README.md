# Kubernetes deployment guide

The team-facing Argo CD deployment guide, activation and verification
commands, feature-branch instructions, and Jira subtasks have moved to
[containerized-setup.md](../containerized-setup.md#gitops-deployment-management-with-argo-cd).

The production Argo CD Application manifest is
[argocd/application.yaml](argocd/application.yaml). It targets `main`; use
`<branch name>` only when testing a pushed feature branch in a local cluster.
