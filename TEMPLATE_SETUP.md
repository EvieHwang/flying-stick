# Template Setup Guide

This document explains how to create a new project from this template. **Delete this file after setup is complete.**

## Quick Start

1. **Create your repository:**
   ```bash
   gh repo create my-project --template YOUR_GITHUB_USER/YOUR_TEMPLATE_REPO
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

7. **Delete this file** and update README.md with your project's documentation.

## Post-Setup Checklist

- [ ] All `{{PLACEHOLDER}}` values replaced
- [ ] GitHub secrets configured
- [ ] AWS Secrets Manager secret created
- [ ] CI workflow passes
- [ ] Branch protection enabled
- [ ] This file deleted
- [ ] README.md updated with project description
