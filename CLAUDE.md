# Claude Agent Autonomy Settings

This document defines the operational autonomy levels for the Claude agent working on this project.

## Allowed Commands

The following bash commands are pre-approved and should be run without prompting:

```bash
# Package management
pip install *
pip uninstall *
pip freeze *
npm install *
npm run *

# Python execution
python *
python3 *
pytest *

# AWS CLI
aws s3 *
aws lambda *
aws apigateway *
aws cloudformation *
aws cloudfront *
aws dynamodb *
aws sts *

# AWS SAM (build/validate only - deploy happens via GitHub Actions)
sam build *
sam local *
sam validate *

# Git operations
git add *
git commit *
git push *
git pull *
git fetch *
git checkout *
git branch *
git merge *
git status
git log *
git diff *
git stash *

# Directory and file operations
mkdir *
cp *
mv *
rm -rf node_modules
rm -rf __pycache__
rm -rf .pytest_cache
rm -rf dist
rm -rf build
rm *.pyc

# Development tools
curl *
wget *
zip *
unzip *
tar *
cat *
head *
tail *
grep *
find *
ls *
cd *
pwd
echo *
export *
source *
chmod *
```

## Git and Deployment Workflow

**CRITICAL: All deployments happen via GitHub Actions, not locally.**

### The Standard Workflow

1. **Make changes** - Edit files as needed
2. **Commit to main** - Create descriptive commits directly on main branch
3. **Push to remote** - Push commits to GitHub
4. **GitHub Actions deploys** - CI runs tests, then deploy workflow handles SAM deploy automatically

### Rules

- **NEVER run `sam deploy` locally** - GitHub Actions handles all deployments after push to main
- **NEVER deploy uncommitted changes** - All changes must be committed and pushed first
- **Commit directly to main** - No feature branches needed for personal projects (simpler workflow)
- **Push triggers deploy** - Once you push to main, deployment is automatic

### Why This Matters

Local `sam deploy` creates drift between git history and deployed state. By forcing all deploys through GitHub Actions:
- Git history always matches what's deployed
- No "I deployed but forgot to commit" situations
- Consistent deploy process regardless of which machine/terminal you're using

### Exceptions

Only run `sam deploy` locally if:
- Explicitly asked to debug a deployment issue
- GitHub Actions is broken and user requests manual deploy
- Initial project setup before GitHub Actions is configured

In these cases, always commit and push the changes BEFORE deploying.

## Autonomous Operations (No Approval Required)

### Git Operations
- **Commit to main**: Create commits with descriptive messages directly on main branch
- **Push to remote**: Push commits to GitHub (this triggers deployment)
- **Create branches**: Only if explicitly requested or for complex multi-step work

### Build and Test
- **Run builds**: Execute `sam build`, `npm run build`, etc. for validation
- **Run tests**: Execute test suites before committing
- **Install dependencies**: Add, update, or remove project dependencies as needed

### AWS Operations (Read/Validate Only)
- **SAM build**: Run `sam build` to validate templates
- **SAM validate**: Check template syntax
- **S3 sync**: Upload files to S3 buckets (for non-CloudFront static assets)

### GitHub Integration
- **Read issues**: Fetch issue details for implementation specs
- **Update issues**: Close issues, add comments, update labels

### File Operations
- **Create files**: Generate new source files, tests, documentation, or specs
- **Edit files**: Modify existing files to implement features or fix bugs
- **Move/rename files**: Reorganize project structure as needed
- **Create directories**: Add new folders for organizational purposes

## Operations Requiring Approval

Always ask before performing these operations:

### Destructive Operations
- **Delete tracked files**: Removing source files from the repository
- **Drop AWS resources**: Deleting S3 buckets, Lambda functions, API Gateways
- **Force push**: Rewriting git history that has been pushed to remote
- **Delete branches**: Removing branches from remote repository

### Major Architectural Changes
- **Change core architecture**: Switching deployment approach or major services
- **Replace major dependencies**: Swapping out Claude API, changing AWS services
- **Modify data schemas**: Changing data structures in breaking ways

## AWS Cost Guardrails

**NEVER configure these without explicit user approval:**
- Lambda Provisioned Concurrency
- Lambda Reserved Concurrency
- NAT Gateways
- Dedicated hosts
- Any "always-on" or "pre-warmed" compute resources

Cold starts are acceptable for most use cases. Pay-per-invocation only.

## DNS & Custom Domain Setup

Apps deploy to custom domains using the pattern: `{repo-name}.evehwang.com`

### Pre-configured Resources (Do Not Create)

These resources already exist and are configured in template.yaml defaults:

- **Wildcard Certificate ARN**: `arn:aws:acm:us-east-1:070840362692:certificate/7358ccd1-846d-4b50-9ccc-b511faa8a4b1`
- **Route 53 Hosted Zone ID**: `Z05581993IIU4AAT9GY4N`
- **Domain**: `evehwang.com`

### How It Works

1. The SAM template creates a CloudFront distribution with the custom domain alias
2. An ACM certificate (wildcard `*.evehwang.com`) provides SSL
3. A Route 53 A record points the domain to CloudFront

### Deployment

On first deployment (or to set a custom domain):

```bash
sam deploy --parameter-overrides DomainName=my-app.evehwang.com
```

The GitHub Actions workflow automatically sets `DomainName` to `{repo-name}.evehwang.com`.

### Important Notes

- The certificate must be in `us-east-1` for CloudFront (it already is)
- `Z2FDTNDATAQYW2` is CloudFront's global hosted zone ID (a constant, not ours)
- If `DomainName` is empty, the template falls back to the CloudFront domain (e.g., `d123.cloudfront.net`)
- Domain can be overridden if you want something other than the repo name

## Aerie Skills Integration

This project has access to shared skills hosted on Aerie (`https://aerie.evehwang.com/`). Skills provide reusable knowledge like design systems, evaluation frameworks, and architectural patterns.

### When to Check Aerie

**Fetch the skills manifest at the start of any planning session:**
- Beginning work on a new feature or spec
- Starting architectural or design decisions
- When the task could benefit from established patterns

### How to Use Aerie

1. **Fetch the manifest** to discover available skills:
   ```
   GET https://aerie.evehwang.com/manifest.json
   ```

2. **Assess relevance** by reading skill descriptions in the manifest. Determine which skills apply to the current task (e.g., `design-system` for UI work, `ai-evaluation` for AI features).

3. **Retrieve relevant skills** by fetching the full documentation:
   ```
   GET https://aerie.evehwang.com/skills/{skill-id}.md
   ```

4. **Apply the guidance** from retrieved skills throughout implementation.

### Skill Memory

After accessing skills, remember what was retrieved so you can:
- Reference the same guidance in subsequent iterations
- Maintain consistency across the implementation
- Avoid redundant fetches within the same work session

If a skill was accessed earlier in the conversation, use that cached knowledge rather than re-fetching.

### Available Skills

Skills are maintained centrally and may include:
- **design-system**: Information-dense UI patterns with React, Tailwind, shadcn/ui
- **ai-evaluation**: Tracing and evaluation patterns for AI agents

Check the manifest for the current list—new skills may be added over time.

---

## Spec-Driven Workflow

This project uses a specification-driven development approach. Features live in the `/specs` directory.

### Workflow Sequence

1. **Specification Phase**: Define feature in `spec.md` with user stories, acceptance scenarios, requirements
2. **Planning Phase**: Create `plan.md` with architecture, phases, deployment strategy
3. **Task Breakdown**: Generate `tasks.md` with detailed tasks, dependencies, parallelization opportunities
4. **Implementation Phase**: Execute tasks following the plan, with tests at each phase
5. **Commit and Push**: Commit changes to main and push to trigger deployment

### When to Use Full Spec Workflow

**Use the full spec workflow when:**
- Requirements are vague or open-ended
- Multiple valid approaches exist and architectural decisions are needed
- Complex features touching many files or systems
- New capabilities without clear implementation path

**Direct implementation is acceptable when:**
- Issue already contains detailed specs with code snippets
- Bug fixes with clear reproduction steps and obvious solutions
- Documentation-only changes
- Small changes following established patterns

### Feature Folder Structure

Each feature gets a numbered folder in `/specs`:

```
specs/
├── CONSTITUTION.md
├── 001-feature-name/
│   ├── spec.md          # Requirements and acceptance criteria
│   ├── plan.md          # Technical architecture and phases
│   ├── tasks.md         # Detailed task breakdown
│   ├── data-model.md    # Database schema and entities
│   └── contracts/
│       └── api.yaml     # OpenAPI specification
├── 002-another-feature/
│   └── ...
```

## Development Philosophy

- **Ship early, ship often**: Bias toward action and deployment
- **Prototype mindset**: Optimize for learning and iteration, not perfection
- **Descriptive commits**: Write clear commit messages that explain *why* not just *what*
- **Spec-driven**: Specifications guide implementation; diverge only with good reason
- **Cost-conscious**: Keep AWS costs minimal, use Claude Haiku where possible
- **Self-documenting**: Code and commits should tell the story
- **Run autonomously**: Don't stop to ask permission for routine operations

## Communication Style

- Be concise and action-oriented
- Explain decisions briefly in commit messages
- Report blockers or ambiguities immediately
- Summarize what was done after completing tasks
- Do not ask for permission on allowed operations - just execute

## Documentation Requirements

### Automatic README Updates

**After completing any feature or significant change, automatically update README.md** to reflect the current state of the project. Do not wait for a separate prompt - this is part of completing the feature.

The README must always include:

1. **Project Overview**: Brief description of what the app does
2. **Features List**: Current capabilities (keep updated as features are added/changed)
3. **Tech Stack**: Languages, frameworks, and services used
4. **Setup/Deployment Instructions**: How to install dependencies, build, and deploy
5. **Usage Guide**: How to use the main features

When updating README.md:
- Keep it concise but complete
- Update the features list if new capabilities were added
- Update usage instructions if UI/workflow changed
- Commit the README update as part of the feature commit or immediately after

## Active Technologies

- Python 3.12+ (Lambda runtime)
- Claude API (Anthropic SDK) for AI features
- AWS Lambda, API Gateway, S3, CloudFront
- AWS SAM for deployment
