# Task Breakdown: Template Foundation

**Plan**: [plan.md](./plan.md)
**Created**: 2026-01-22
**Status**: Complete

## Task Summary

| Phase | Tasks | Completed |
|-------|-------|-----------|
| Phase 1: Backend Foundation | 6 | 6 |
| Phase 2: GitHub Actions | 4 | 4 |
| Phase 3: Frontend Scaffold | 12 | 12 |
| Phase 4: Repository Config | 4 | 4 |
| Phase 5: Documentation | 6 | 6 |
| **Total** | **32** | **32** |

---

## Phase 1: Backend Foundation

### T-1.1: Create Backend Directory Structure

- **Description**: Create the `backend/` directory with `src/`, `src/utils/`, and `tests/` subdirectories
- **Dependencies**: None
- **Files**:
  - Create: `backend/src/__init__.py`
  - Create: `backend/src/utils/__init__.py`
  - Create: `backend/tests/__init__.py`
- **Acceptance**: Directories exist with empty `__init__.py` files
- **Status**: [x] Complete

### T-1.2: Create Lambda Handler

- **Description**: Create the main Lambda handler with a health check endpoint that returns JSON with status and timestamp
- **Dependencies**: T-1.1
- **Files**:
  - Create: `backend/src/handler.py`
- **Acceptance**: Handler exports `lambda_handler` function; returns `{"status": "healthy", "timestamp": "..."}` for health check path
- **Status**: [x] Complete

### T-1.3: Create Secrets Manager Helper

- **Description**: Create a module that fetches and caches secrets from AWS Secrets Manager. Must support JSON secrets with multiple keys. Cache at module level for Lambda warm starts.
- **Dependencies**: T-1.1
- **Files**:
  - Create: `backend/src/utils/secrets.py`
- **Acceptance**:
  - `get_secret(secret_name)` function fetches from Secrets Manager
  - `get_secret_value(secret_name, key)` function gets specific key from JSON secret
  - Module-level cache prevents redundant API calls
  - Clear error messages if secret not found
- **Status**: [x] Complete

### T-1.4: Create Requirements File

- **Description**: Create `requirements.txt` with minimal dependencies needed for Lambda operation
- **Dependencies**: T-1.3
- **Files**:
  - Create: `backend/requirements.txt`
- **Contents**:
  ```
  boto3>=1.34.0
  ```
- **Acceptance**: File exists with boto3 dependency
- **Status**: [x] Complete

### T-1.5: Create SAM Template

- **Description**: Create `template.yaml` with Lambda function, API Gateway, and IAM role with Secrets Manager access. Use `{{PLACEHOLDERS}}` for all project-specific values.
- **Dependencies**: T-1.2
- **Files**:
  - Create: `template.yaml`
- **Acceptance**:
  - Lambda function defined with Python 3.12 runtime
  - API Gateway with `/health` GET endpoint
  - IAM role with `secretsmanager:GetSecretValue` permission
  - All resource names use `{{PROJECT_NAME}}` placeholder
  - `{{AWS_REGION}}` placeholder for region
- **Status**: [x] Complete

### T-1.6: Create Handler Tests

- **Description**: Create pytest tests for the Lambda handler. Test health check endpoint response structure.
- **Dependencies**: T-1.2
- **Files**:
  - Create: `backend/tests/test_handler.py`
- **Acceptance**:
  - Test imports handler successfully
  - Test verifies health check returns correct JSON structure
  - Test passes with `pytest backend/tests/`
- **Status**: [x] Complete

---

## Phase 2: GitHub Actions

### T-2.1: Enhance CI Workflow

- **Description**: Update `ci.yml` to add TruffleHog secret scanning and pip-audit dependency checking. Maintain existing ruff linting and pytest execution.
- **Dependencies**: T-1.6 (tests must exist to run)
- **Files**:
  - Modify: `.github/workflows/ci.yml`
- **Acceptance**:
  - TruffleHog scans for leaked secrets
  - pip-audit checks for known vulnerabilities
  - ruff linting with fail on error
  - pytest with coverage report
  - All steps use `{{PYTHON_VERSION}}` placeholder where appropriate
- **Status**: [x] Complete

### T-2.2: Enhance Deploy Workflow

- **Description**: Update `deploy.yml` to use SAM for deployment and add CloudFront invalidation for frontend. Must use GitHub Secrets for AWS credentials.
- **Dependencies**: T-1.5 (SAM template must exist)
- **Files**:
  - Modify: `.github/workflows/deploy.yml`
- **Acceptance**:
  - Triggers on push to main
  - Runs `sam build` and `sam deploy`
  - Syncs frontend build to S3 (if frontend directory exists)
  - Invalidates CloudFront distribution
  - Uses `${{ secrets.AWS_ACCESS_KEY_ID }}` and `${{ secrets.AWS_SECRET_ACCESS_KEY }}`
  - Uses `{{CLOUDFRONT_DISTRIBUTION_ID}}` and `{{S3_FRONTEND_BUCKET}}` placeholders
- **Status**: [x] Complete

### T-2.3: Create Rollback Workflow

- **Description**: Create `rollback.yml` that can revert Lambda to previous version and restore previous frontend from S3. Must be manually triggered via workflow_dispatch.
- **Dependencies**: T-2.2
- **Files**:
  - Create: `.github/workflows/rollback.yml`
- **Acceptance**:
  - Uses `workflow_dispatch` trigger
  - Updates Lambda alias to previous version
  - Optionally restores frontend from versioned S3
  - Invalidates CloudFront
  - Documents rollback procedure in workflow comments
- **Status**: [x] Complete

### T-2.4: Create Dependabot Config

- **Description**: Create Dependabot configuration for automated security updates on Python and npm dependencies
- **Dependencies**: None
- **Files**:
  - Create: `.github/dependabot.yml`
- **Acceptance**:
  - Monitors pip dependencies in `/backend`
  - Monitors npm dependencies in `/frontend`
  - Weekly update schedule
  - Groups minor/patch updates
- **Status**: [x] Complete

---

## Phase 3: Frontend Scaffold

### T-3.1: Initialize Vite + React + TypeScript

- **Description**: Create frontend directory with Vite, React 18, and TypeScript. Use `npm create vite@latest` as base, then customize.
- **Dependencies**: None
- **Files**:
  - Create: `frontend/package.json`
  - Create: `frontend/tsconfig.json`
  - Create: `frontend/tsconfig.node.json`
  - Create: `frontend/vite.config.ts`
  - Create: `frontend/src/main.tsx`
  - Create: `frontend/index.html`
- **Acceptance**:
  - `cd frontend && npm install && npm run dev` starts dev server
  - TypeScript strict mode enabled
  - React 18 with createRoot
- **Status**: [x] Complete

### T-3.2: Configure Tailwind with Design Tokens

- **Description**: Add Tailwind CSS with custom design tokens for information-dense UI. Tighter spacing scale, print-like typography, CSS variables for theming.
- **Dependencies**: T-3.1
- **Files**:
  - Create: `frontend/tailwind.config.ts`
  - Create: `frontend/postcss.config.js`
  - Create: `frontend/src/index.css`
- **Acceptance**:
  - Tailwind classes work in components
  - Custom spacing scale (tighter than default)
  - Custom font sizes (14px base)
  - CSS variables for `--background`, `--foreground`, etc.
  - Dark mode variables defined
- **Status**: [x] Complete

### T-3.3: Configure Path Aliases

- **Description**: Set up `@/` path alias for clean imports in both TypeScript and Vite
- **Dependencies**: T-3.1
- **Files**:
  - Modify: `frontend/tsconfig.json`
  - Modify: `frontend/vite.config.ts`
- **Acceptance**:
  - `import { cn } from "@/lib/utils"` works
  - No TypeScript errors for `@/` paths
  - Vite resolves `@/` correctly at build time
- **Status**: [x] Complete

### T-3.4: Create Utils and cn() Helper

- **Description**: Create the `cn()` helper function for merging Tailwind classes (required by shadcn/ui)
- **Dependencies**: T-3.1
- **Files**:
  - Create: `frontend/src/lib/utils.ts`
- **Acceptance**:
  - Exports `cn()` function
  - Uses `clsx` and `tailwind-merge`
  - `cn("p-4", "p-2")` returns `"p-2"` (proper merge)
- **Status**: [x] Complete

### T-3.5: Add shadcn/ui Button Component

- **Description**: Add Button component with compact sizing variants for information-dense UI
- **Dependencies**: T-3.2, T-3.4
- **Files**:
  - Create: `frontend/src/components/ui/button.tsx`
- **Acceptance**:
  - All standard variants (default, destructive, outline, secondary, ghost, link)
  - Size variants include compact option
  - Uses CSS variables for theming
  - TypeScript types exported
- **Status**: [x] Complete

### T-3.6: Add shadcn/ui Card Component

- **Description**: Add Card component with tight padding appropriate for dense layouts
- **Dependencies**: T-3.2, T-3.4
- **Files**:
  - Create: `frontend/src/components/ui/card.tsx`
- **Acceptance**:
  - Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter exported
  - Tighter padding than shadcn default
  - Uses CSS variables
- **Status**: [x] Complete

### T-3.7: Add shadcn/ui Input Component

- **Description**: Add Input component styled for information-dense forms
- **Dependencies**: T-3.2, T-3.4
- **Files**:
  - Create: `frontend/src/components/ui/input.tsx`
- **Acceptance**:
  - Standard input styling
  - Compact height option
  - Focus states use CSS variables
  - Accessible (proper aria attributes)
- **Status**: [x] Complete

### T-3.8: Add shadcn/ui Textarea Component

- **Description**: Add Textarea component for multiline input
- **Dependencies**: T-3.2, T-3.4
- **Files**:
  - Create: `frontend/src/components/ui/textarea.tsx`
- **Acceptance**:
  - Matches Input styling
  - Resizable
  - Uses CSS variables
- **Status**: [x] Complete

### T-3.9: Implement ThemeProvider

- **Description**: Create React context for theme management with system preference detection and localStorage persistence
- **Dependencies**: T-3.1
- **Files**:
  - Create: `frontend/src/components/ThemeProvider.tsx`
- **Acceptance**:
  - Context provides `theme`, `setTheme`
  - Themes: "light", "dark", "system"
  - Detects system preference with `prefers-color-scheme`
  - Persists to localStorage
  - Updates document class (`dark` class on html element)
- **Status**: [x] Complete

### T-3.10: Implement ThemeToggle

- **Description**: Create toggle button component for switching between light/dark/system themes
- **Dependencies**: T-3.5, T-3.9
- **Files**:
  - Create: `frontend/src/components/ThemeToggle.tsx`
- **Acceptance**:
  - Shows current theme state (icon)
  - Dropdown or toggle to switch themes
  - Uses Button component styling
  - Accessible (keyboard navigation)
- **Status**: [x] Complete

### T-3.11: Add Theme Flash Prevention

- **Description**: Add inline script to index.html that sets theme class before React hydration to prevent flash of wrong theme
- **Dependencies**: T-3.9
- **Files**:
  - Modify: `frontend/index.html`
- **Acceptance**:
  - Inline `<script>` in `<head>` before any CSS/JS
  - Reads localStorage, falls back to system preference
  - Sets `dark` class on `<html>` if dark theme
  - No visible theme flash on page load
- **Status**: [x] Complete

### T-3.12: Create Sample App.tsx

- **Description**: Create App.tsx that demonstrates all components: Card with form inputs, Button, ThemeToggle
- **Dependencies**: T-3.5 through T-3.10
- **Files**:
  - Create: `frontend/src/App.tsx`
- **Acceptance**:
  - Renders Card with title
  - Includes Input and Textarea
  - Includes Button
  - Includes ThemeToggle in header
  - Demonstrates both light and dark mode
- **Status**: [x] Complete

### T-3.13: Create DESIGN.md

- **Description**: Document the entire design system: philosophy, scales, tokens, components, accessibility, and portability instructions
- **Dependencies**: T-3.2, T-3.5 through T-3.10
- **Files**:
  - Create: `frontend/DESIGN.md`
- **Acceptance**:
  - Documents "UI should be invisible" philosophy
  - Lists typography scale with rationale
  - Lists spacing scale with rationale
  - Documents all CSS variables
  - Explains how to add new shadcn components
  - Includes dark mode principles
  - Includes accessibility requirements
  - Includes "how to copy to another project" checklist
- **Status**: [x] Complete

---

## Phase 4: Repository Configuration

### T-4.1: Create Comprehensive .gitignore

- **Description**: Create `.gitignore` covering Python, Node, AWS SAM, OS files, and IDE files
- **Dependencies**: None
- **Files**:
  - Create: `.gitignore`
- **Acceptance**:
  - Ignores `__pycache__`, `*.pyc`, `.pytest_cache`
  - Ignores `node_modules`, `dist`, `.vite`
  - Ignores `.aws-sam`, `samconfig.toml`
  - Ignores `.env`, `.env.local` (but NOT `.env.example`)
  - Ignores `.DS_Store`, `Thumbs.db`
  - Ignores `.idea`, `.vscode` (except settings if desired)
- **Status**: [x] Complete

### T-4.2: Create pyproject.toml

- **Description**: Create pyproject.toml with project metadata, ruff configuration, and pytest configuration
- **Dependencies**: T-1.4
- **Files**:
  - Create: `pyproject.toml`
- **Acceptance**:
  - Project name uses `{{PROJECT_NAME}}`
  - Ruff configuration (line length 100, select rules)
  - Pytest configuration (testpaths, coverage)
  - Python version requirement (3.12+)
- **Status**: [x] Complete

### T-4.3: Create Makefile

- **Description**: Create Makefile with common development commands
- **Dependencies**: T-1.4, T-2.1
- **Files**:
  - Create: `Makefile`
- **Commands to include**:
  - `make install` - Install Python and npm dependencies
  - `make lint` - Run ruff
  - `make test` - Run pytest with coverage
  - `make build` - Run sam build
  - `make deploy` - Run sam deploy
  - `make dev` - Run frontend dev server
  - `make clean` - Remove build artifacts
- **Acceptance**: All commands work when dependencies are installed
- **Status**: [x] Complete

### T-4.4: Create .env.example

- **Description**: Create `.env.example` documenting all environment variables needed, with empty values and comments
- **Dependencies**: T-1.3
- **Files**:
  - Create: `.env.example`
- **Contents**:
  ```
  # AWS Configuration (for local development only - production uses Secrets Manager)
  AWS_REGION={{AWS_REGION}}

  # Secret name in AWS Secrets Manager
  SECRET_NAME={{PROJECT_NAME}}/prod

  # Local development only (not used in production)
  # ANTHROPIC_API_KEY=
  ```
- **Acceptance**: Documents all required variables with explanatory comments
- **Status**: [x] Complete

---

## Phase 5: Documentation & Validation

### T-5.1: Refine README.md

- **Description**: Update README with comprehensive setup instructions, all placeholders documented, and clear development workflow
- **Dependencies**: All previous phases
- **Files**:
  - Modify: `README.md`
- **Acceptance**:
  - "Using This Template" section with step-by-step
  - All `{{PLACEHOLDER}}` values listed with descriptions
  - Required GitHub Secrets documented
  - AWS Secrets Manager setup instructions
  - Local development instructions
  - Deployment instructions
  - Links to CLAUDE.md and DESIGN.md
- **Status**: [x] Complete

### T-5.2: Review CLAUDE.md

- **Description**: Review CLAUDE.md for completeness in Cloud mode. Ensure no dependencies on `~/.claude/`. Add any missing instructions discovered during implementation.
- **Dependencies**: Phase 1, Phase 2
- **Files**:
  - Modify: `CLAUDE.md` (if needed)
- **Acceptance**:
  - Self-contained (no external file dependencies)
  - All allowed commands are listed
  - Spec-driven workflow is documented
  - AWS cost guardrails are clear
  - Testing requirements are specified
- **Status**: [x] Complete

### T-5.3: Review CONSTITUTION.md

- **Description**: Review specs/CONSTITUTION.md for appropriate placeholders and alignment with actual template capabilities
- **Dependencies**: None
- **Files**:
  - Modify: `specs/CONSTITUTION.md` (if needed)
- **Acceptance**:
  - All project-specific text uses placeholders
  - Technology constraints match actual template
  - Success metrics are realistic
- **Status**: [x] Complete

### T-5.4: Review Example Specs

- **Description**: Review 000-example-feature specs for clarity and usefulness as examples
- **Dependencies**: None
- **Files**:
  - Review: `specs/000-example-feature/spec.md`
  - Review: `specs/000-example-feature/plan.md`
  - Review: `specs/000-example-feature/tasks.md`
  - Review: `specs/000-example-feature/data-model.md`
  - Review: `specs/000-example-feature/contracts/api.yaml`
- **Acceptance**:
  - Examples are helpful for learning spec-driven workflow
  - Placeholders used appropriately
  - Format matches actual usage
- **Status**: [x] Complete

### T-5.5: Refine PR Template

- **Description**: Update pull request template to match spec-driven workflow
- **Dependencies**: None
- **Files**:
  - Modify: `.github/pull_request_template.md`
- **Acceptance**:
  - Links to related spec/issue
  - Checklist includes tests, lint, documentation
  - Summary section for changes
  - Test plan section
- **Status**: [x] Complete

### T-5.6: Validation Test

- **Description**: Create a new repository from the template, replace all placeholders, and verify CI passes
- **Dependencies**: All previous tasks
- **Files**:
  - None (external validation)
- **Acceptance**:
  - New repo created via "Use this template"
  - All `{{PLACEHOLDER}}` values replaced
  - `make lint` passes
  - `make test` passes
  - GitHub Actions CI passes
  - Can deploy with SAM (manual test)
- **Status**: [x] Complete

---

## Critical Path

Tasks that block other work and should be prioritized:

1. **T-1.1** → T-1.2, T-1.3 (backend structure enables handler and secrets)
2. **T-1.5** → T-2.2 (SAM template required for deploy workflow)
3. **T-3.1** → T-3.2 → T-3.4 → T-3.5+ (frontend must be initialized before components)
4. **T-3.9** → T-3.10, T-3.11 (ThemeProvider required for toggle and flash prevention)

## Parallelization Opportunities

Tasks that can be worked on simultaneously:

**After T-1.1 completes**:
- T-1.2 (handler) and T-1.3 (secrets) can run in parallel

**Frontend and Backend are independent**:
- All of Phase 3 (frontend) can run parallel to Phase 1 and 2

**Phase 4 tasks are mostly independent**:
- T-4.1, T-4.2, T-4.3, T-4.4 can all run in parallel

**Phase 5 reviews are independent**:
- T-5.2, T-5.3, T-5.4, T-5.5 can all run in parallel

---

## File Checklist

All files that will be created or modified:

**New Files (25)**:
- [ ] `backend/src/__init__.py`
- [ ] `backend/src/handler.py`
- [ ] `backend/src/utils/__init__.py`
- [ ] `backend/src/utils/secrets.py`
- [ ] `backend/tests/__init__.py`
- [ ] `backend/tests/test_handler.py`
- [ ] `backend/requirements.txt`
- [ ] `template.yaml`
- [ ] `.github/workflows/rollback.yml`
- [ ] `.github/dependabot.yml`
- [ ] `frontend/package.json`
- [ ] `frontend/tsconfig.json`
- [ ] `frontend/tsconfig.node.json`
- [ ] `frontend/vite.config.ts`
- [ ] `frontend/tailwind.config.ts`
- [ ] `frontend/postcss.config.js`
- [ ] `frontend/src/index.css`
- [ ] `frontend/src/main.tsx`
- [ ] `frontend/src/App.tsx`
- [ ] `frontend/src/lib/utils.ts`
- [ ] `frontend/src/components/ui/button.tsx`
- [ ] `frontend/src/components/ui/card.tsx`
- [ ] `frontend/src/components/ui/input.tsx`
- [ ] `frontend/src/components/ui/textarea.tsx`
- [ ] `frontend/src/components/ThemeProvider.tsx`
- [ ] `frontend/src/components/ThemeToggle.tsx`
- [ ] `frontend/index.html`
- [ ] `frontend/DESIGN.md`
- [ ] `.gitignore`
- [ ] `pyproject.toml`
- [ ] `Makefile`
- [ ] `.env.example`

**Modified Files (6)**:
- [ ] `.github/workflows/ci.yml`
- [ ] `.github/workflows/deploy.yml`
- [ ] `.github/pull_request_template.md`
- [ ] `README.md`
- [ ] `CLAUDE.md` (if needed)
- [ ] `specs/CONSTITUTION.md` (if needed)

---

## Progress Log

| Date | Tasks Completed | Notes |
|------|-----------------|-------|
| 2026-01-22 | All 32 tasks | Initial implementation of complete template |
