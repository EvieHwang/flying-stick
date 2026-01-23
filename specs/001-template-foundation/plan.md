# Technical Plan: Template Foundation

**Spec**: [spec.md](./spec.md)
**Created**: 2026-01-22
**Status**: Draft

## Architecture Overview

Flying-stick is a template repository providing three main components that work together for laptop-free development:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Developer Workflow                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   iPad/iPhone          GitHub                   AWS                  │
│   ┌─────────┐         ┌─────────┐            ┌─────────┐            │
│   │ Claude  │  push   │ Actions │   deploy   │ Lambda  │            │
│   │  Code   │ ──────> │  CI/CD  │ ─────────> │ + API   │            │
│   └─────────┘         └─────────┘            │ Gateway │            │
│       │                    │                  └────┬────┘            │
│       │                    │                       │                 │
│       v                    v                       v                 │
│   CLAUDE.md           GitHub               AWS Secrets              │
│   (instructions)      Secrets              Manager                  │
│                       (deploy creds)       (runtime secrets)        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      Template Structure                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Backend               Frontend              Infrastructure         │
│   ┌─────────┐          ┌─────────┐          ┌─────────┐            │
│   │ Lambda  │          │  Vite   │          │   SAM   │            │
│   │ Handler │          │  React  │          │ Template│            │
│   │ + Tests │          │   TS    │          │  .yaml  │            │
│   └────┬────┘          │ Tailwind│          └────┬────┘            │
│        │               │ shadcn  │               │                  │
│        v               └────┬────┘               v                  │
│   Secrets.py                │               API Gateway            │
│   (runtime fetch)           v               + Lambda               │
│                         S3 + CDN            + IAM Roles            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
flying-stick/
├── .github/
│   ├── dependabot.yml              # NEW: Automated updates
│   ├── pull_request_template.md    # EXISTS: Refine
│   └── workflows/
│       ├── ci.yml                  # EXISTS: Refine (add security scans)
│       ├── deploy.yml              # EXISTS: Refine (add CloudFront)
│       └── rollback.yml            # NEW: Rollback workflow
├── backend/                         # NEW: Entire directory
│   ├── src/
│   │   ├── __init__.py
│   │   ├── handler.py              # Lambda entry point
│   │   └── utils/
│   │       └── secrets.py          # Secrets Manager helper
│   ├── tests/
│   │   └── test_handler.py
│   └── requirements.txt
├── frontend/                        # NEW: Entire directory
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                 # shadcn components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   └── textarea.tsx
│   │   │   ├── ThemeProvider.tsx
│   │   │   └── ThemeToggle.tsx
│   │   ├── lib/
│   │   │   └── utils.ts            # cn() helper
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css               # Tailwind + CSS vars
│   ├── public/
│   ├── index.html                  # Theme flash prevention
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── vite.config.ts
│   └── DESIGN.md                   # Design system docs
├── specs/
│   ├── CONSTITUTION.md             # EXISTS: Review
│   └── 000-example-feature/        # EXISTS: Review
├── .env.example                     # NEW
├── .gitignore                       # NEW (comprehensive)
├── CLAUDE.md                        # EXISTS: Review for completeness
├── Makefile                         # NEW
├── README.md                        # EXISTS: Refine
├── pyproject.toml                   # NEW
└── template.yaml                    # NEW: SAM template
```

## Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Backend Runtime | Python 3.12 | AWS Lambda native support, Claude SDK available |
| IaC | AWS SAM | Simpler than raw CloudFormation, Lambda-focused |
| Secrets | AWS Secrets Manager | Runtime access, no local files, easy rotation |
| Frontend Build | Vite | Fast builds, excellent TypeScript support |
| UI Framework | React 18 | Ecosystem, Claude familiarity, shadcn compatibility |
| Styling | Tailwind CSS | Utility-first, design token support, shadcn native |
| Components | shadcn/ui | Copy-paste components, Tailwind native, customizable |
| Linting | Ruff | Fast, replaces flake8+black+isort |
| Testing | Pytest | Python standard, good coverage tools |
| Security Scan | TruffleHog | Detects secrets in commits |
| Dependency Audit | pip-audit | Checks for known vulnerabilities |

## Implementation Phases

### Phase 1: Backend Foundation

**Goal**: Working Lambda function that can be deployed via SAM with Secrets Manager integration.

- [ ] Create `backend/` directory structure
- [ ] Implement `handler.py` with health check endpoint
- [ ] Implement `secrets.py` with caching Secrets Manager fetch
- [ ] Create `requirements.txt` with boto3, pytest
- [ ] Create `template.yaml` with Lambda + API Gateway + IAM
- [ ] Create basic `test_handler.py`

**Verification**: `sam build && sam local invoke` returns health check response

### Phase 2: GitHub Actions

**Goal**: Complete CI/CD pipeline that lints, tests, scans for secrets, and deploys on merge to main.

- [ ] Refine `ci.yml` to add TruffleHog, pip-audit
- [ ] Refine `deploy.yml` to use SAM deploy, add CloudFront invalidation
- [ ] Create `rollback.yml` with manual trigger
- [ ] Create `dependabot.yml` for Python and npm

**Verification**: Push to branch triggers CI; merge to main triggers deploy

### Phase 3: Frontend Scaffold

**Goal**: Complete React/TypeScript/Tailwind setup with shadcn components and working dark mode.

- [ ] Initialize Vite + React + TypeScript project
- [ ] Configure Tailwind with custom design tokens
- [ ] Configure path aliases in tsconfig and vite.config
- [ ] Add shadcn/ui base components (Button, Card, Input, Textarea)
- [ ] Implement ThemeProvider with localStorage persistence
- [ ] Implement ThemeToggle component
- [ ] Add theme flash prevention script to index.html
- [ ] Create sample App.tsx demonstrating components
- [ ] Create DESIGN.md with full documentation

**Verification**: `npm run dev` works; dark mode toggles without flash; DESIGN.md is comprehensive

### Phase 4: Repository Configuration

**Goal**: All configuration files in place with proper templatization.

- [ ] Create comprehensive `.gitignore`
- [ ] Create `pyproject.toml` with ruff, pytest config
- [ ] Create `Makefile` with common commands
- [ ] Create `.env.example` documenting required secrets
- [ ] Review and finalize placeholder usage across all files

**Verification**: `make lint && make test` work; no hardcoded values remain

### Phase 5: Documentation & Validation

**Goal**: README is complete, all placeholder documentation is clear, and template passes validation.

- [ ] Refine README with complete setup instructions
- [ ] Refine CLAUDE.md if gaps found
- [ ] Review CONSTITUTION.md and example specs
- [ ] Refine PR template
- [ ] Create validation test: new repo from template

**Verification**: New repo created from template, placeholders replaced, CI passes

## Data Flow

### Secrets Retrieval (Runtime)

1. Lambda cold starts
2. `handler.py` imports `secrets.py`
3. `get_secrets()` checks module-level cache
4. If cache miss, calls Secrets Manager API
5. Parses JSON response, stores in cache
6. Returns secret value to handler
7. Subsequent warm invocations use cache

### Deployment Flow

1. Developer pushes to `main` branch
2. GitHub Actions `deploy.yml` triggers
3. Checkout code, setup Python, setup SAM
4. `sam build` packages Lambda
5. `sam deploy` updates CloudFormation stack
6. If frontend changed: `npm run build`, S3 sync, CloudFront invalidate
7. Workflow completes, deployment live

### Rollback Flow

1. Developer triggers `rollback.yml` manually (workflow_dispatch)
2. Workflow queries Lambda for previous version
3. Updates alias to point to previous version
4. If frontend: S3 sync from previous deployment artifact
5. CloudFront invalidation
6. Rollback complete

## Deployment Strategy

1. **Build**: SAM build packages Lambda code
2. **Test**: CI runs full test suite before deploy is allowed
3. **Deploy**: SAM deploy with `--no-fail-on-empty-changeset`
4. **Frontend**: Vite build → S3 sync → CloudFront invalidate
5. **Verify**: Health check endpoint returns 200

## Rollback Points

Safe stopping points where the template remains functional:

1. **After Phase 1**: Backend works, can be deployed manually via SAM
2. **After Phase 2**: Full CI/CD works, automated deployment possible
3. **After Phase 3**: Frontend works but separate from backend
4. **After Phase 4**: All config in place, template usable for backend-only projects
5. **After Phase 5**: Complete template ready for production use

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SAM template complexity | Medium | Medium | Start minimal, add features incrementally |
| shadcn/ui version drift | Low | Low | Pin versions, document upgrade path |
| GitHub Actions rate limits | Low | Low | Use caching for dependencies |
| Secrets Manager cold-start latency | Medium | Low | Cache at module level, document behavior |
| Theme flash despite prevention | Medium | Medium | Test on multiple browsers, inline critical CSS |
| Placeholder replacement errors | Medium | High | Document all placeholders in README, consider init script |

## Open Questions

- [ ] Should template include a `scripts/init.sh` to automate placeholder replacement?
- [ ] Should DESIGN.md include guidance for adding more shadcn components?
- [ ] Should rollback preserve previous N versions or just latest?
- [ ] Should template include example Claude API integration?
