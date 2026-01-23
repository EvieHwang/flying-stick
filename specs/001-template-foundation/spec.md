# Feature Specification: Template Foundation

**Feature Branch**: `001-template-foundation`
**Created**: 2026-01-22
**Status**: Ready for Implementation
**Input**: requirements.md in this directory

## Overview

Flying-stick is a GitHub template repository that enables laptop-free development with Claude Code. The core insight: by moving secrets to AWS Secrets Manager and providing comprehensive CLAUDE.md instructions, developers can build, test, and deploy features entirely from iOS/web Claude Code sessions.

Key insight: The template itself must be built using the spec-driven workflow it defines—this validates the process while creating the product.

---

## User Scenarios & Testing

### User Story 1 - Create New Project (Priority: P1)

A developer wants to start a new AI-powered application without manual setup. They use the template to create a fully-configured repository with CI/CD, secrets management, and frontend scaffolding already in place.

**Why this priority**: Foundation for all other workflows. Without easy project creation, no other features matter.

**Independent Test**: Create new repo from template, replace placeholders, verify all files are correctly templatized and GitHub Actions pass.

**Acceptance Scenarios**:

1. **Given** the flying-stick template exists on GitHub, **When** I click "Use this template" and create `my-new-project`, **Then** I receive a repository with complete directory structure matching the target state
2. **Given** a new repo created from template, **When** I search for `{{PROJECT_NAME}}` in the codebase, **Then** I find exactly the documented placeholders and can replace them
3. **Given** a new repo with placeholders replaced, **When** GitHub Actions run on push, **Then** CI workflow completes successfully (lint, security scan)

---

### User Story 2 - Mobile Development Workflow (Priority: P1)

A developer on their iPad opens Claude Code Cloud, describes a feature, and Claude writes specs, implements code, creates tests, and pushes to GitHub—all without any laptop involvement.

**Why this priority**: This is the core value proposition. Laptop-optional development.

**Independent Test**: On iPad, use Claude Code to implement a simple API endpoint. Verify push succeeds and GitHub Actions deploy.

**Acceptance Scenarios**:

1. **Given** a project created from the template with GitHub Secrets configured, **When** I describe a feature to Claude Code in Cloud mode, **Then** Claude can read CLAUDE.md and understand the full workflow
2. **Given** Claude Code implements a feature, **When** it runs `git push`, **Then** GitHub Actions deploy to AWS without manual intervention
3. **Given** CLAUDE.md in the repository (not `~/.claude/`), **When** Claude Code session starts, **Then** it has complete instructions for autonomous operation

---

### User Story 3 - Secrets Without Local Files (Priority: P1)

A developer needs their Lambda function to access the Anthropic API key. They store it in AWS Secrets Manager and the application fetches it at runtime—no `.env` file needed locally or in deployment.

**Why this priority**: Blocking issue for Cloud development. Local-only secrets prevent remote workflows.

**Independent Test**: Deploy Lambda, verify it retrieves secret from Secrets Manager at runtime, returns correct response.

**Acceptance Scenarios**:

1. **Given** a secret stored in AWS Secrets Manager named `{{PROJECT_NAME}}/prod`, **When** Lambda function cold starts, **Then** it fetches and caches the secret successfully
2. **Given** GitHub Secrets contain AWS credentials, **When** deploy workflow runs, **Then** SAM deploy succeeds without any local environment variables
3. **Given** a secret is rotated in Secrets Manager, **When** Lambda next cold starts, **Then** it retrieves the new value without redeployment

---

### User Story 4 - One-Click Rollback (Priority: P2)

After a deployment breaks production, a developer triggers the rollback workflow from GitHub mobile app and the previous working version is restored within minutes.

**Why this priority**: Important safety net, but not blocking for initial development workflow.

**Independent Test**: Deploy version A, deploy version B (broken), trigger rollback, verify version A is serving.

**Acceptance Scenarios**:

1. **Given** a broken deployment on main branch, **When** I trigger `rollback.yml` workflow manually, **Then** previous Lambda version is activated
2. **Given** rollback workflow, **When** I view its documentation, **Then** I understand exactly how to trigger and what it does
3. **Given** frontend deployed to S3, **When** rollback runs, **Then** previous frontend version is restored and CloudFront cache invalidated

---

### User Story 5 - Frontend Design System (Priority: P2)

A developer needs to build a dashboard UI. They use the pre-configured React/Tailwind/shadcn setup with information-dense design tokens already applied. Dark mode works out of the box.

**Why this priority**: High leverage for productivity, but backend functionality takes precedence.

**Independent Test**: Run `npm run dev`, verify components render, toggle dark mode, verify no theme flash on reload.

**Acceptance Scenarios**:

1. **Given** the frontend scaffold, **When** I run `npm install && npm run dev`, **Then** the app builds and renders without errors
2. **Given** the theme toggle component, **When** I switch to dark mode and reload, **Then** dark mode persists without flash of light mode
3. **Given** DESIGN.md documentation, **When** I read it, **Then** I understand the design philosophy, spacing/typography scales, and how to add components

---

### Edge Cases

- **Empty Secrets Manager**: If secret doesn't exist, Lambda should return clear error (not crash)
- **Partial placeholder replacement**: CI should fail with helpful message if `{{` patterns remain
- **Rate limiting on secrets fetch**: Use caching to avoid Secrets Manager rate limits
- **GitHub Actions timeout**: SAM deploy can be slow; ensure adequate timeout (15+ minutes)
- **CloudFront cache**: Invalidation takes time; document expected delay

---

## Requirements

### Functional Requirements

**Secrets Management**

- **FR-1.1**: Template MUST include `backend/src/utils/secrets.py` with Secrets Manager fetch function
- **FR-1.2**: Secrets module MUST cache fetched secrets for Lambda lifetime (warm start optimization)
- **FR-1.3**: Template MUST include `.env.example` listing all required secrets (values empty)
- **FR-1.4**: Secrets fetch MUST support JSON secrets with multiple key-value pairs
- **FR-1.5**: README MUST document Secrets Manager setup with AWS CLI commands

**GitHub Actions**

- **FR-2.1**: CI workflow MUST run: ruff lint, pytest with coverage, TruffleHog scan, pip-audit
- **FR-2.2**: Deploy workflow MUST trigger on push to main branch
- **FR-2.3**: Deploy workflow MUST run SAM build, SAM deploy, and CloudFront invalidation
- **FR-2.4**: Rollback workflow MUST be manually triggerable (workflow_dispatch)
- **FR-2.5**: Template MUST include `.github/dependabot.yml` for Python and npm updates
- **FR-2.6**: Deploy workflow MUST use GitHub Secrets for AWS credentials

**CLAUDE.md**

- **FR-3.1**: CLAUDE.md MUST be self-contained (no dependency on user's `~/.claude/`)
- **FR-3.2**: CLAUDE.md MUST list all pre-approved bash commands
- **FR-3.3**: CLAUDE.md MUST define autonomous operations vs. approval-required operations
- **FR-3.4**: CLAUDE.md MUST include AWS cost guardrails (no provisioned concurrency)
- **FR-3.5**: CLAUDE.md MUST document spec-driven workflow with when-to-use guidance
- **FR-3.6**: CLAUDE.md MUST require README updates after feature completion

**Spec Kit**

- **FR-4.1**: Template MUST include `specs/CONSTITUTION.md` with templatized values
- **FR-4.2**: Template MUST include `specs/000-example-feature/` with all spec files
- **FR-4.3**: Example spec files MUST use `{{PLACEHOLDERS}}` demonstrating templatization

**Frontend**

- **FR-5.1**: Frontend MUST use Vite + React + TypeScript
- **FR-5.2**: Frontend MUST include Tailwind CSS with custom design tokens
- **FR-5.3**: Frontend MUST include shadcn/ui base components (Button, Card, Input, Textarea)
- **FR-5.4**: Frontend MUST include ThemeProvider with localStorage persistence
- **FR-5.5**: Frontend MUST prevent theme flash on initial load (inline script in HTML head)
- **FR-5.6**: Frontend MUST include DESIGN.md documenting the design system
- **FR-5.7**: Design tokens MUST implement tight spacing (information-dense philosophy)

**Backend**

- **FR-6.1**: Backend MUST include Lambda handler with health check endpoint
- **FR-6.2**: Backend MUST include SAM `template.yaml` with API Gateway integration
- **FR-6.3**: Backend MUST include IAM role with Secrets Manager read access
- **FR-6.4**: Backend MUST include pytest test file with at least one test

**Repository Config**

- **FR-7.1**: Template MUST include comprehensive `.gitignore`
- **FR-7.2**: Template MUST include `Makefile` with build, test, deploy, lint commands
- **FR-7.3**: Template MUST include `pyproject.toml` with ruff and pytest config
- **FR-7.4**: Template MUST include `.github/pull_request_template.md`

---

### Non-Functional Requirements

- **NFR-1**: All project-specific values MUST use `{{PLACEHOLDER}}` format
- **NFR-2**: Cold start time SHOULD be under 3 seconds (standard Lambda, no provisioned concurrency)
- **NFR-3**: CI workflow SHOULD complete in under 5 minutes
- **NFR-4**: Deploy workflow SHOULD complete in under 15 minutes
- **NFR-5**: Template MUST NOT include any hardcoded secrets or credentials
- **NFR-6**: Documentation MUST be sufficient for first-time users

---

### Key Entities

**Template Placeholders**
- `{{PROJECT_NAME}}` (string, required) - Used in README, package.json, template.yaml
- `{{PROJECT_DESCRIPTION}}` (string, required) - README, CONSTITUTION.md
- `{{GITHUB_USER}}` (string, required) - README clone URLs
- `{{AWS_REGION}}` (string, default: us-west-2) - SAM config, GitHub Actions
- `{{S3_FRONTEND_BUCKET}}` (string, required) - Deploy workflow, README
- `{{CLOUDFRONT_DISTRIBUTION_ID}}` (string, required) - Deploy workflow
- `{{LAMBDA_FUNCTION_NAME}}` (string, required) - template.yaml, rollback workflow
- `{{PYTHON_VERSION}}` (string, default: 3.12) - CI workflow, pyproject.toml

**GitHub Secrets Required**
- `AWS_ACCESS_KEY_ID` (string) - IAM credentials for deployment
- `AWS_SECRET_ACCESS_KEY` (string) - IAM credentials for deployment
- `ANTHROPIC_API_KEY` (string, optional) - If using Claude API in deployed app

---

## Success Criteria

### Measurable Outcomes

- **SC-1**: New repo created from template has 0 CI errors after placeholder replacement
- **SC-2**: Feature implemented entirely from iPad Claude Code deploys successfully
- **SC-3**: Lambda retrieves Secrets Manager value on first invocation (verifiable in CloudWatch)
- **SC-4**: Rollback workflow restores previous version within 5 minutes
- **SC-5**: Frontend builds in under 60 seconds locally
- **SC-6**: DESIGN.md enables adding new shadcn component without external documentation

---

## Assumptions

- User has AWS account with appropriate permissions (Lambda, API Gateway, S3, CloudFront, Secrets Manager)
- User has GitHub account and can create repositories from templates
- User will configure GitHub Secrets before first deployment
- Claude Code Cloud mode has access to push to GitHub repositories
- Users accept cold start latency (no provisioned concurrency)
- TypeScript strict mode is desirable for frontend development

---

## Out of Scope (Future Considerations)

- Database integration (DynamoDB, RDS) - add when needed per-project
- Authentication system - varies too much between projects
- Data visualization library recommendation (FR-8) - evaluate separately
- Multi-environment deployment (staging, prod) - MVP is single environment
- Monorepo tooling - template assumes single-service architecture
- Custom domain configuration - manual setup per-project

---

## Dependencies

- **AWS Services**: Lambda, API Gateway, S3, CloudFront, Secrets Manager, IAM
- **GitHub Services**: Actions, Secrets, Templates
- **Frontend Stack**: Vite 5.x, React 18.x, TypeScript 5.x, Tailwind CSS 3.x, shadcn/ui
- **Backend Stack**: Python 3.12, AWS SAM CLI, boto3
- **Development Tools**: ruff, pytest, TruffleHog, pip-audit
