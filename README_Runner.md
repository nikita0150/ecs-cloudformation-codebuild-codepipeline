# AWS CodeBuild as a Self-Hosted GitHub Actions Runner

This document explains the **CodeBuild Runner Project** setup used to let GitHub Actions
workflows execute on AWS CodeBuild-managed compute instead of GitHub-hosted runners
or self-managed EC2 runners.

---

## 1. Concept Overview

Normally, GitHub Actions jobs run on:
- **GitHub-hosted runners** (`ubuntu-latest`, etc.) — managed by GitHub, no AWS access without stored credentials.
- **Self-hosted runners** — EC2 instances you provision, patch, and maintain yourself.

With a **CodeBuild Runner Project**, AWS CodeBuild acts as the compute layer for GitHub
Actions jobs:

- **GitHub Actions remains the orchestrator** — the workflow YAML still defines triggers,
  jobs, and steps.
- **CodeBuild provides the execution environment** — an ephemeral container that runs the
  job's steps.
- **`buildspec.yml` is not used** for runner projects — job steps come entirely from the
  GitHub Actions workflow file.
- Native AWS integration is available inside the job (IAM role, VPC, Secrets Manager,
  CloudTrail) without storing long-lived AWS credentials as GitHub secrets.

```
GitHub push/event
      │
      ▼
GitHub Actions workflow triggered
      │
      ▼
Job specifies runs-on: codebuild-<project-name>-...
      │
      ▼
GitHub sends WORKFLOW_JOB_QUEUED webhook to CodeBuild
      │
      ▼
CodeBuild spins up an ephemeral container (the "runner")
      │
      ▼
Job steps execute inside CodeBuild, logs stream to:
   - GitHub Actions UI
   - CodeBuild Console (Build history)
   - CloudWatch Logs
```

---

## 2. Project Type: Default vs Runner

A CodeBuild project is created as **one type or the other** — it cannot serve both purposes.

| | Default Project | Runner Project |
|---|---|---|
| Trigger | Pipeline / webhook (PUSH, PR) / manual | GitHub Actions job queued (`WORKFLOW_JOB_QUEUED`) |
| Build definition | `buildspec.yml` | GitHub Actions workflow YAML |
| Source | GitHub repo via CodeStar Connection/OAuth | `NO_SOURCE`, or repo used only for webhook registration |
| Typical use | Traditional CI: build, test, push image, deploy | Replace GitHub-hosted/self-managed runners with AWS compute |

> If you already have a Default project (e.g. `ecs-cicd-app` building/pushing Docker
> images via buildspec), create a **separate** Runner project rather than converting it.

---

## 3. Setting Up the Runner Project

### Step 1 — Connect CodeBuild to GitHub
Reuse an existing connection (OAuth / GitHub App / CodeStar Connection) if already set up
for another project, or create one during project creation.

### Step 2 — Create the CodeBuild project

| Field | Example Value |
|---|---|
| Project name | `ecs-cicd-app-runner` |
| Project type | **Runner project** |
| Source provider | GitHub |
| Repository | `<your-username>/<repo-name>` |

### Step 3 — Configure the webhook (critical)

Under **Primary source webhook events**:
- Enable "Rebuild every time a code change is pushed to this repository"
- Filter Groups → Event type: **`WORKFLOW_JOB_QUEUED`**

> `PUSH` or `PULL_REQUEST` filters will **not** trigger runner jobs — it must be
> `WORKFLOW_JOB_QUEUED`.

### Step 4 — Environment settings

| Field | Example Value |
|---|---|
| Environment image | Managed image (Amazon Linux 2 / Ubuntu standard) |
| Compute type | `BUILD_GENERAL1_SMALL` (adjust for workload) |
| Service role | New service role (auto-created) |

The buildspec section can be left at default — it is overridden automatically for runner
jobs unless `buildspec-override: true` is explicitly set as a label in the workflow.

### Step 5 — Verify the webhook on GitHub

```
https://github.com/<your-username>/<repo>/settings/hooks
```
Confirm a webhook exists, pointing to AWS, subscribed to **Workflow jobs** events.

---

## 4. GitHub Actions Workflow

Create `.github/workflows/<name>.yml`:

```yaml
name: Hello CodeBuild Runner

on: [push]

jobs:
  hello-job:
    runs-on: codebuild-ecs-cicd-app-runner-${{ github.run_id }}-${{ github.run_attempt }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Say hello
        run: echo "Hello from AWS CodeBuild acting as a GitHub Actions runner!"

      - name: Show environment
        run: |
          uname -a
          whoami
          pwd
```

### `runs-on:` naming convention

```
codebuild-<project-name>-${{ github.run_id }}-${{ github.run_attempt }}
```

This string must exactly reference the CodeBuild **Runner project** name — a mismatch
here is the most common reason a job fails to pick up a runner.

---

## 5. Verifying a Run

After pushing a commit, check in this order:

1. **GitHub → Actions tab** — job should show as running/completed, with step-by-step logs.
2. **AWS CodeBuild Console → `ecs-cicd-app-runner` → Build history** — a new build
   triggered by the webhook, with the same logs plus infra-level detail (e.g. container
   startup time).
3. **CloudWatch Logs → `/aws/codebuild/ecs-cicd-app-runner`** — logs land here
   automatically, same as any CodeBuild build.

---

## 6. Extending to a Real Workflow (Docker Build → ECR Push)

Once the hello-world job succeeds, replace the steps with actual build/push logic:

```yaml
jobs:
  build-and-push:
    runs-on: codebuild-ecs-cicd-app-runner-${{ github.run_id }}-${{ github.run_attempt }}
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::<account-id>:role/<your-role>
          aws-region: us-east-1

      - name: Login to ECR
        run: |
          aws ecr get-login-password | \
          docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

      - name: Build and push image
        run: |
          docker build -t <repo>:${{ github.sha }} .
          docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/<repo>:${{ github.sha }}
```

Because the job executes inside CodeBuild's environment, AWS CLI/SDK calls use the
CodeBuild service role's permissions — no long-lived AWS keys need to be stored as
GitHub secrets.

---

## 7. Common Pitfalls

| Symptom | Likely Cause |
|---|---|
| Workflow job stays queued, never picks up a runner | `runs-on:` project name doesn't match an existing Runner project |
| No webhook triggered on push | Webhook filter set to `PUSH`/`PULL_REQUEST` instead of `WORKFLOW_JOB_QUEUED` |
| Webhook missing entirely on GitHub | GitHub connection (OAuth/App/PAT) lacks required repo permissions |
| AWS CLI calls fail inside job (AccessDenied) | CodeBuild service role's IAM trust policy or permissions not scoped correctly |
| buildspec commands seem ignored | Expected — runner projects ignore buildspec unless `buildspec-override: true` label is set |

---

## 8. When to Use This vs a Standard buildspec Pipeline

| Scenario | Recommended Approach |
|---|---|
| Team already invested in GitHub Actions YAML, wants AWS-native compute/IAM without managing EC2 runners | **CodeBuild Runner Project** |
| Standard CI/CD: build → push to ECR → deploy to ECS, using CodePipeline orchestration | **Default CodeBuild Project + `buildspec.yml` + CodePipeline** |

For this project's production pipeline (GitHub → Docker build → ECR push → ECS deploy),
the **Default Project + buildspec.yml + CodePipeline** route remains the primary path.
This Runner Project setup is documented as a proof-of-concept exploration of the
alternative mechanism.
