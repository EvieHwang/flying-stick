# {{PROJECT_NAME}}

{{PROJECT_DESCRIPTION}}

## Using This Template

This is a template repository. To create a new project from this template:

1. Click "Use this template" on GitHub, or run:
   ```bash
   gh repo create my-new-project --template evehwang/flying-stick
   ```

2. Replace all `{{PLACEHOLDER}}` values throughout the repository:
   - `{{PROJECT_NAME}}` - Your project name
   - `{{PROJECT_DESCRIPTION}}` - Brief project description
   - `{{ORGANIZATION_NAME}}` - Your team/organization name
   - `{{SOURCE_DIR}}` - Source code directory (default: `src/`)
   - `{{PYTHON_VERSION}}` - Python version (default: `3.12`)
   - `{{AWS_REGION}}` - AWS region (default: `us-west-2`)
   - `{{S3_BUCKET}}` - S3 bucket for artifacts
   - `{{CODEBUILD_PROJECT}}` - CodeBuild project name
   - `{{CLOUDFORMATION_STACK}}` - CloudFormation stack name
   - `{{ECR_REPOSITORY}}` - ECR repository URI
   - `{{API_ENDPOINT}}` - API Gateway endpoint URL

3. Set up GitHub repository secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `ANTHROPIC_API_KEY` (if using Claude API)

4. Update `specs/CONSTITUTION.md` with your project's principles

5. Delete this "Using This Template" section and update the README with your project's actual documentation

---

## Features

- [ ] Feature 1
- [ ] Feature 2

## Tech Stack

- **Runtime**: Python 3.12+
- **Cloud**: AWS (Lambda, API Gateway, S3, CloudFront)
- **AI**: Claude API (Anthropic)
- **Deployment**: AWS SAM, GitHub Actions

## Project Structure

```
{{PROJECT_NAME}}/
├── .github/
│   ├── pull_request_template.md
│   └── workflows/
│       ├── ci.yml          # Lint, test, security scan
│       └── deploy.yml      # AWS deployment
├── specs/
│   ├── CONSTITUTION.md     # Project principles
│   └── 001-feature-name/   # Feature specifications
│       ├── spec.md
│       ├── plan.md
│       ├── tasks.md
│       ├── data-model.md
│       └── contracts/
│           └── api.yaml
├── src/                    # Source code
├── tests/                  # Test files
├── CLAUDE.md               # AI agent guidelines
└── README.md
```

## Development

### Prerequisites

- Python 3.12+
- AWS CLI configured
- AWS SAM CLI
- GitHub CLI (`gh`)

### Setup

```bash
# Clone the repository
git clone https://github.com/{{GITHUB_USER}}/{{PROJECT_NAME}}.git
cd {{PROJECT_NAME}}

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running Tests

```bash
pytest tests/ -v --cov=src
```

### Linting

```bash
pip install ruff
ruff check src/
```

### Local Development

```bash
sam build
sam local start-api
```

## Deployment

Deployment is automatic via GitHub Actions when changes are pushed to `main`.

To deploy manually:

```bash
sam build
sam deploy --guided  # First time
sam deploy           # Subsequent deployments
```

## Spec-Driven Development

This project follows a spec-driven workflow. See [CLAUDE.md](./CLAUDE.md) for details.

1. Create a feature specification in `specs/XXX-feature-name/spec.md`
2. Plan the implementation in `plan.md`
3. Break down tasks in `tasks.md`
4. Implement following the plan
5. Create a PR for review

## Contributing

1. Create a feature branch: `git checkout -b 001-feature-name`
2. Follow the spec-driven workflow
3. Ensure tests pass: `pytest`
4. Create a PR using the template

## License

[Choose a license]
