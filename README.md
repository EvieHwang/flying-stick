# {{PROJECT_NAME}}

{{PROJECT_DESCRIPTION}}

## Using This Template

This is a GitHub template repository optimized for **laptop-free development** using Claude Code. It enables a complete workflow—from feature ideation to production deployment—without local development tools.

### Quick Start

1. **Create your repository:**
   ```bash
   gh repo create my-project --template {{GITHUB_USER}}/flying-stick
   cd my-project
   ```

2. **Replace all placeholders** (find and replace in your editor):

   | Placeholder | Description | Example |
   |-------------|-------------|---------|
   | `{{PROJECT_NAME}}` | Your project name | `my-app` |
   | `{{PROJECT_DESCRIPTION}}` | Brief description | `AI-powered task manager` |
   | `{{GITHUB_USER}}` | Your GitHub username | `evehwang` |
   | `{{AWS_REGION}}` | AWS region | `us-west-2` |
   | `{{PYTHON_VERSION}}` | Python version | `3.12` |

3. **Configure GitHub Secrets** (Settings → Secrets and variables → Actions):
   - `AWS_ACCESS_KEY_ID` - IAM user access key
   - `AWS_SECRET_ACCESS_KEY` - IAM user secret key
   - `ANTHROPIC_API_KEY` - (optional) If using Claude API

4. **Create AWS Secrets Manager secret:**
   ```bash
   aws secretsmanager create-secret \
     --name {{PROJECT_NAME}}/prod \
     --secret-string '{"ANTHROPIC_API_KEY": "sk-ant-..."}'
   ```

5. **Push changes and verify CI passes:**
   ```bash
   git add -A
   git commit -m "Initialize project from template"
   git push origin main
   ```
   Wait for the CI workflow to complete successfully. This is required before setting up branch protection.

   After first deployment, your app will be available at `https://{repo-name}.evehwang.com`.

6. **Configure branch protection** (Settings → Branches → Add rule):
   - Branch name pattern: `main`
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
     - Search and select: `lint`, `test`, `security` (the CI jobs)
   - ✅ Require branches to be up to date before merging
   
   This creates your **deploy gate**: Claude Code pushes to a branch → opens PR → CI runs → you approve and merge in GitHub app → deploy runs.

7. **Delete this "Using This Template" section** and update with your project's documentation.

---

## Development Workflow

This template is optimized for **cloud-based development** using Claude Code (CITA). Local development is optional.

### Cloud Workflow (Primary)

1. Open Claude Code on iOS/web, select your repo
2. Describe a feature or ask for changes
3. Claude Code creates a branch, implements, and opens a PR
4. CI runs automatically on the PR
5. Review and merge the PR in the GitHub app
6. Deploy runs automatically on merge to `main`

### Local Development (Optional)

If you need to run locally for debugging:

```bash
# Install dependencies
make install

# Run frontend dev server
make dev

# Run backend locally (requires SAM CLI)
make local

# Run tests
make test

# Run linter
make lint
```

---

## Features

- [ ] Feature 1
- [ ] Feature 2

## Tech Stack

- **Backend**: Python 3.12, AWS Lambda, API Gateway
- **Frontend**: React 18, TypeScript, Tailwind CSS, shadcn/ui
- **Infrastructure**: AWS SAM, CloudFront, S3
- **AI**: Claude API (Anthropic)
- **CI/CD**: GitHub Actions

## Project Structure

```
{{PROJECT_NAME}}/
├── .github/
│   ├── dependabot.yml          # Automated dependency updates
│   ├── pull_request_template.md
│   └── workflows/
│       ├── ci.yml              # Lint, test, security scan
│       ├── deploy.yml          # SAM deploy + frontend to S3
│       └── rollback.yml        # One-click rollback
├── backend/
│   ├── src/
│   │   ├── handler.py          # Lambda handler
│   │   └── utils/
│   │       └── secrets.py      # Secrets Manager helper
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── ui/            # shadcn/ui components
│   │   │   ├── ThemeProvider.tsx
│   │   │   └── ThemeToggle.tsx
│   │   └── lib/utils.ts       # Tailwind utilities
│   ├── DESIGN.md              # Design system docs
│   └── ...config files
├── specs/
│   ├── CONSTITUTION.md        # Project principles
│   └── 000-example-feature/   # Spec template
├── .env.example               # Required environment variables
├── CLAUDE.md                  # AI agent instructions
├── Makefile                   # Common commands
├── pyproject.toml             # Python config
└── template.yaml              # SAM template
```

## Deployment

### Automatic Deployment

Merging a PR to `main` triggers automatic deployment:

1. **CI** runs lint, tests, security scans (on PR)
2. **You approve and merge** the PR (your deploy gate)
3. **Deploy** runs SAM deploy and syncs frontend to S3
4. **CloudFront** cache is invalidated

### Rollback

If a deployment breaks:

1. Go to GitHub → Actions → Rollback
2. Click "Run workflow"
3. Select component (backend/frontend/both)
4. Type "ROLLBACK" to confirm
5. Click "Run workflow"

## Secrets Management

**No `.env` files in production!** Secrets are managed via AWS Secrets Manager.

### How It Works

1. Store secrets in AWS Secrets Manager
2. Lambda fetches secrets at runtime via `utils/secrets.py`
3. Secrets are cached for Lambda warm starts
4. No redeployment needed for secret rotation

### Adding a Secret

```bash
# Update the secret
aws secretsmanager update-secret \
  --secret-id {{PROJECT_NAME}}/prod \
  --secret-string '{"ANTHROPIC_API_KEY": "new-key", "OTHER_SECRET": "value"}'
```

### Using Secrets in Code

```python
from src.utils.secrets import get_secret_value

api_key = get_secret_value("{{PROJECT_NAME}}/prod", "ANTHROPIC_API_KEY")
```

## Spec-Driven Development

This project uses a spec-driven workflow. See [CLAUDE.md](./CLAUDE.md) for details.

### Workflow

1. **Spec**: Define requirements in `specs/XXX-feature/spec.md`
2. **Plan**: Design architecture in `plan.md`
3. **Tasks**: Break down into atomic tasks in `tasks.md`
4. **Implement**: Follow the plan
5. **PR**: Create pull request for review

### When to Use Full Spec Workflow

- Complex features with multiple approaches
- Architectural decisions needed
- Unclear requirements

### When to Skip Specs

- Bug fixes with clear solutions
- Documentation changes
- Small changes following existing patterns

## Design System

The frontend uses an **information-dense** design philosophy. See [frontend/DESIGN.md](./frontend/DESIGN.md) for:

- Typography and spacing scales
- Color system with CSS variables
- Component usage guidelines
- Dark mode implementation
- How to add new components

## Cost Guardrails

⚠️ **Never configure without explicit approval:**

- Lambda Provisioned Concurrency
- NAT Gateways
- Dedicated hosts
- Any "always-on" compute

Cold starts are acceptable. Pay-per-invocation only.

## Contributing

1. Create a feature branch: `git checkout -b 001-feature-name`
2. Follow the spec-driven workflow (if appropriate)
3. Ensure tests pass: `make test`
4. Ensure linting passes: `make lint`
5. Create a PR using the template

## License

[Choose a license]
