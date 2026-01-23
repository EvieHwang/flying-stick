# Flying-Stick Template Repository: Requirements Document

## Executive Summary

**flying-stick** is a GitHub template repository optimized for laptop-free development using Claude Code in the cloud (iOS/web). The goal is to enable a complete development workflow—from feature ideation to production deployment—without requiring local development tools beyond initial repo setup.

The template consolidates best practices from two existing repositories (wm2 and dwcoa-financials) and adds infrastructure to support remote-first, AI-assisted development.

---

## Problem Statement

### Current Pain Points

1. **Local dependency**: Current workflow requires laptop access for many development tasks, limiting productivity when away from computer

2. **Secrets in .env files**: Apps depend on local environment variables, making cloud-based Claude Code sessions unable to run or deploy code

3. **Inconsistent setup**: Each new project requires manual setup of GitHub Actions, CLAUDE.md, specs structure, and frontend scaffolding

4. **No rollback capability**: Current GitHub Actions can deploy but cannot easily revert to previous versions

5. **Missing frontend foundation**: No standardized React/TypeScript/Tailwind setup with design system documentation

### Target State

A developer should be able to:
1. Create a new repo from the template (laptop, one-time)
2. Describe a feature in Claude Code on iPad/iPhone
3. Have Claude Code write specs, implement, test, and push
4. GitHub Actions deploy automatically
5. Review and merge from mobile GitHub app
6. App runs in production with secrets fetched from AWS Secrets Manager

**The laptop becomes optional for day-to-day development.**

---

## Stakeholder Context

- **Primary user**: Product manager / developer who wants to build and iterate on AI-powered applications
- **Development style**: Spec-driven development using GitHub Spec Kit pattern
- **Design philosophy**: Information-dense UI, "the UI should be invisible"
- **Infrastructure**: AWS (Lambda, API Gateway, S3, CloudFront, Secrets Manager)
- **AI integration**: Claude API (Anthropic) for intelligent features
- **Deployment**: GitHub Actions triggering AWS deployments

---

## Functional Requirements

### FR-1: Secrets Management Pattern

**FR-1.1**: Template must include boilerplate code for fetching secrets from AWS Secrets Manager at runtime

**FR-1.2**: Template must include `.env.example` documenting required secrets without values

**FR-1.3**: Apps created from template must work without local `.env` files

**FR-1.4**: GitHub Actions must use GitHub Secrets for deployment credentials (AWS keys, etc.)

**FR-1.5**: Documentation must explain how to:
- Create secrets in AWS Secrets Manager
- Configure GitHub Secrets for the repository
- Rotate secrets without redeployment

### FR-2: GitHub Actions Workflows

**FR-2.1**: CI workflow (`ci.yml`) must include:
- Python linting (ruff)
- Test execution with coverage
- Security scanning (TruffleHog)
- Dependency audit (pip-audit)

**FR-2.2**: Deploy workflow (`deploy.yml`) must include:
- Branch-based deployment triggers (e.g., push to `main` → production)
- SAM build and deploy
- Lambda function update
- CloudFront invalidation (for frontend)
- Deployment verification

**FR-2.3**: Rollback workflow (`rollback.yml`) must provide:
- One-click revert to previous deployment
- Clear documentation of how to trigger

**FR-2.4**: Dependabot configuration (`.github/dependabot.yml`) for automated security updates

**FR-2.5**: Branch protection rules documentation

### FR-3: CLAUDE.md (AI Agent Instructions)

**FR-3.1**: Must be comprehensive enough for Cloud mode (no `~/.claude/CLAUDE.md` dependency)

**FR-3.2**: Must include:
- Allowed commands (pre-approved bash operations)
- Autonomous operations (what Claude can do without asking)
- Operations requiring approval (destructive actions)
- AWS cost guardrails (no provisioned concurrency, etc.)
- Spec-driven workflow instructions
- Git workflow (branch naming, commit messages, PR conventions)
- Code review checklist
- Deployment instructions
- Testing requirements

**FR-3.3**: Must reference the spec kit structure and when to use full spec workflow vs. direct implementation

**FR-3.4**: Must include README auto-update requirement

### FR-4: Spec Kit Structure

**FR-4.1**: Template must include `specs/` directory with:
- `CONSTITUTION.md` - Project principles (templatized with `{{PLACEHOLDERS}}`)
- `000-example-feature/` - Example feature spec structure

**FR-4.2**: Feature spec structure must include:
- `spec.md` - Requirements and acceptance criteria
- `plan.md` - Technical architecture and phases
- `tasks.md` - Detailed task breakdown
- `data-model.md` - Database schema (when applicable)
- `contracts/` - API specifications (OpenAPI)

### FR-5: Frontend Toolkit (React + TypeScript + Tailwind + shadcn/ui)

**FR-5.1**: Template must include complete frontend scaffold:
```
frontend/
├── src/
│   ├── components/
│   │   └── ui/           # shadcn/ui components
│   ├── lib/
│   │   └── utils.ts      # cn() helper
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css         # Tailwind + CSS variables
├── public/
├── index.html            # With theme flash prevention script
├── package.json
├── tsconfig.json         # Strict mode, path aliases (@/)
├── tailwind.config.ts    # Custom design tokens
├── vite.config.ts        # Path resolution
└── DESIGN.md             # Portable design system documentation
```

**FR-5.2**: Design tokens must implement information-dense philosophy:
- Tighter spacing than Tailwind defaults
- Print-like typography (14px base, 1.4-1.5 line heights)
- CSS variables for light/dark theming

**FR-5.3**: Must include base shadcn/ui components:
- Button (with compact sizing variants)
- Card
- Input
- Textarea

**FR-5.4**: Must include theme system:
- `ThemeProvider.tsx` - Context with system preference detection
- `ThemeToggle.tsx` - Toggle component
- localStorage persistence
- No flash of wrong theme on load

**FR-5.5**: `DESIGN.md` must document:
- Design philosophy ("UI should be invisible")
- Typography scale with rationale
- Spacing scale with rationale
- Color system (semantic tokens)
- Component patterns
- Dark mode principles
- Accessibility requirements
- Technical reference (dependencies, file structure)
- Portability checklist for copying to new projects

**FR-5.6**: Frontend GitHub Actions must include:
- Build step (`npm run build`)
- S3 sync for deployment
- CloudFront invalidation

### FR-6: Backend Scaffold

**FR-6.1**: Template must include Python backend structure:
```
backend/
├── src/
│   ├── __init__.py
│   ├── handler.py        # Lambda handler
│   └── utils/
│       └── secrets.py    # Secrets Manager helper
├── tests/
│   └── test_handler.py
└── requirements.txt
```

**FR-6.2**: Must include `template.yaml` (SAM) with:
- Lambda function definition
- API Gateway configuration
- IAM roles with Secrets Manager access
- Templatized resource names

**FR-6.3**: Must include `pyproject.toml` with:
- Project metadata (templatized)
- Ruff configuration
- Pytest configuration

### FR-7: Repository Configuration

**FR-7.1**: Template must include:
- `.gitignore` (comprehensive, merged from wm2 + dwcoa-financials)
- `.env.example`
- `Makefile` with common commands (build, test, deploy, lint)
- `README.md` (templatized with setup instructions)
- `.github/pull_request_template.md`

**FR-7.2**: README must document:
- How to use the template
- All `{{PLACEHOLDER}}` values to replace
- Required GitHub Secrets to configure
- Setup steps
- Development workflow

### FR-8: Data Visualization (Future Consideration)

**FR-8.1**: Evaluate and document recommended data visualization library:
- Primary candidate: Tremor (React + Tailwind native)
- Alternatives: Recharts, Plotly React, D3
- Goal: Replace Streamlit dependency for dashboards

---

## Non-Functional Requirements

### NFR-1: Portability
- Template must work for any new project without modification to core patterns
- Project-specific values must be clearly marked as `{{PLACEHOLDERS}}`

### NFR-2: Cloud-First Compatibility
- All workflows must function in Claude Code Cloud mode
- No dependencies on local machine state beyond initial setup

### NFR-3: Cost Consciousness
- AWS resources must follow pay-per-use patterns
- No always-on compute (no provisioned concurrency, no NAT gateways)
- Cold starts are acceptable

### NFR-4: Security
- Secrets must never be committed to repository
- GitHub Actions must use GitHub Secrets
- Runtime secrets must come from AWS Secrets Manager

### NFR-5: Maintainability
- Template is the source of truth
- Older projects may drift; that's acceptable
- Documentation must be self-contained

---

## Placeholders to Define

The template must use these placeholders (to be replaced when creating a new project):

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{PROJECT_NAME}}` | Project name | `wm2` |
| `{{PROJECT_DESCRIPTION}}` | Brief description | `AI-powered product classifier` |
| `{{GITHUB_USER}}` | GitHub username | `EvieHwang` |
| `{{AWS_REGION}}` | AWS region | `us-west-2` |
| `{{S3_BUCKET}}` | S3 bucket for artifacts | `wm2-artifacts` |
| `{{S3_FRONTEND_BUCKET}}` | S3 bucket for frontend | `wm2-frontend` |
| `{{CLOUDFRONT_DISTRIBUTION_ID}}` | CloudFront distribution | `E1234567890` |
| `{{LAMBDA_FUNCTION_NAME}}` | Lambda function name | `wm2-classifier` |
| `{{API_ENDPOINT}}` | API Gateway endpoint | `https://xxx.execute-api.us-west-2.amazonaws.com/prod` |
| `{{PYTHON_VERSION}}` | Python version | `3.12` |
| `{{SOURCE_DIR}}` | Source code directory | `backend/src/` |

---

## Success Criteria

### Validation Tests

1. **Create new app from template**: Use GitHub "Use this template" button, replace placeholders, verify structure is correct

2. **Build feature from iPad**: In Claude Code Cloud mode, describe a simple feature, have Claude write spec and implement it, push to GitHub

3. **Automated deployment**: Merge PR, verify GitHub Actions deploy to AWS successfully

4. **Secrets rotation**: Change a secret in AWS Secrets Manager, verify app picks it up without redeployment

5. **Rollback**: Trigger rollback workflow, verify previous version is restored

6. **Frontend renders**: Build frontend, deploy to S3/CloudFront, verify dark/light mode and design system work

### Definition of Done

- [ ] All FR requirements implemented
- [ ] All files use appropriate placeholders
- [ ] README documents complete setup process
- [ ] CLAUDE.md comprehensive enough for Cloud mode
- [ ] GitHub Actions all pass on template repo
- [ ] At least one test project created from template successfully
- [ ] Feature built and deployed entirely from mobile device

---

## Reference Materials

### Source Repositories
- `EvieHwang/wm2` - GitHub Actions, CI/CD patterns
- `EvieHwang/dwcoa-financials` - Spec kit structure, CONSTITUTION.md

### WM2 Frontend Issues (Design System Reference)
- Issue #127: EPIC overview - React + TypeScript + Tailwind + shadcn/ui
- Issue #128: Vite + React + TypeScript initialization
- Issue #129: Tailwind CSS with design tokens
- Issue #130: shadcn/ui base components
- Issue #131: Dark/light mode with system preference
- Issue #135: DESIGN.md portable toolkit documentation

### Design Philosophy
- Information density of a well-designed newspaper
- Reference aesthetic: Linear, Bloomberg Terminal
- "The UI should be invisible" - serve content, not impress
- Both light and dark modes equally polished

---

## Appendix: File Tree (Target State)

```
flying-stick/
├── .github/
│   ├── dependabot.yml
│   ├── pull_request_template.md
│   └── workflows/
│       ├── ci.yml
│       ├── deploy.yml
│       └── rollback.yml
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── handler.py
│   │   └── utils/
│   │       └── secrets.py
│   ├── tests/
│   │   └── test_handler.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   └── textarea.tsx
│   │   │   ├── ThemeProvider.tsx
│   │   │   └── ThemeToggle.tsx
│   │   ├── lib/
│   │   │   └── utils.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── vite.config.ts
│   └── DESIGN.md
├── specs/
│   ├── CONSTITUTION.md
│   └── 000-example-feature/
│       ├── spec.md
│       ├── plan.md
│       ├── tasks.md
│       ├── data-model.md
│       └── contracts/
│           └── api.yaml
├── .env.example
├── .gitignore
├── CLAUDE.md
├── Makefile
├── README.md
├── pyproject.toml
└── template.yaml
```
