# Template Setup Guide

This document explains how to create a new project from this template. **Delete this file after setup is complete.**

## Quick Start

1. **Create your repository:**
   ```bash
   gh repo create my-project --template EvieHwang/flying-stick --public --clone
   cd my-project
   ```

2. **Replace all placeholders** (find and replace in your editor or use sed):

   | Placeholder | Description | Example |
   |-------------|-------------|---------|
   | `{{PROJECT_NAME}}` | Your project name (use repo name) | `my-app` |
   | `{{PROJECT_DESCRIPTION}}` | Brief description | `AI-powered task manager` |
   | `{{AWS_REGION}}` | AWS region | `us-west-2` |
   | `{{PYTHON_VERSION}}` | Python version | `3.12` |
   | `{{DATE}}` | Today's date | `2024-01-15` |

   **Files containing placeholders:**
   - `template.yaml` - SAM template
   - `pyproject.toml` - Python config
   - `.github/workflows/*.yml` - CI/CD workflows
   - `backend/src/**/*.py` - Python source files
   - `frontend/package.json` - Frontend config
   - `frontend/index.html` - Page title
   - `specs/CONSTITUTION.md` - Project constitution
   - `README.md` - Documentation
   - `.env.example` - Environment template

3. **Configure GitHub Secrets** (Settings → Secrets and variables → Actions):
   - `AWS_ACCESS_KEY_ID` - IAM user access key
   - `AWS_SECRET_ACCESS_KEY` - IAM user secret key
   - `ANTHROPIC_API_KEY` - If using Claude API (auto-creates AWS Secrets Manager secret on first deploy)

   > **Note:** If you add `ANTHROPIC_API_KEY` to GitHub Secrets, the deploy workflow will automatically create the AWS Secrets Manager secret for you. No manual AWS CLI command needed!

4. **Push changes and deploy:**
   ```bash
   git add -A
   git commit -m "Initialize project from template"
   git push origin main
   ```

   The deploy workflow will:
   - Create the AWS Secrets Manager secret (if ANTHROPIC_API_KEY is set)
   - Deploy backend via SAM
   - Build and deploy frontend to S3/CloudFront

   After deployment, your app will be available at `https://{repo-name}.evehwang.com`.

5. **Configure branch protection** (Settings → Rules → Rulesets):
   - Create ruleset for `main` branch
   - ✅ Require status checks to pass before merging
     - Add: `Lint`, `Test`, `Security Scan`, `Frontend Lint & Build`
   - ✅ Optionally require pull request before merging

   This creates your **deploy gate**: push to branch → PR → CI runs → merge → deploy.

6. **Delete this file** and update README.md with your project's documentation.

## Post-Setup Checklist

- [ ] All `{{PLACEHOLDER}}` values replaced
- [ ] GitHub secrets configured (AWS keys + optional ANTHROPIC_API_KEY)
- [ ] First deploy successful
- [ ] Branch protection enabled
- [ ] This file deleted
- [ ] README.md updated with project description
