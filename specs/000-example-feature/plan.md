# Technical Plan: {{FEATURE_NAME}}

**Spec**: [Link to spec.md]
**Created**: {{DATE}}
**Status**: Draft | Approved | In Progress | Complete

## Architecture Overview

[High-level description of how this feature fits into the system]

```
[ASCII diagram or description of component relationships]
```

## Directory Structure

```
{{PROJECT_NAME}}/
├── src/
│   ├── [new-module]/
│   │   ├── __init__.py
│   │   ├── handler.py
│   │   └── models.py
│   └── ...
├── tests/
│   └── test_[module].py
└── ...
```

## Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| [Component] | [Technology] | [Why this choice] |

## Implementation Phases

### Phase 1: [Foundation]

**Goal**: [What this phase accomplishes]

- [ ] Task 1.1: [Description]
- [ ] Task 1.2: [Description]
- [ ] Task 1.3: [Description]

**Verification**: [How to know this phase is complete]

### Phase 2: [Core Feature]

**Goal**: [What this phase accomplishes]

- [ ] Task 2.1: [Description]
- [ ] Task 2.2: [Description]

**Verification**: [How to know this phase is complete]

### Phase 3: [Polish & Deploy]

**Goal**: [What this phase accomplishes]

- [ ] Task 3.1: [Description]
- [ ] Task 3.2: [Description]

**Verification**: [How to know this phase is complete]

## API Design

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/[resource] | Create a new [resource] |
| GET | /api/v1/[resource]/{id} | Get [resource] by ID |

### Request/Response Examples

```json
// POST /api/v1/[resource]
// Request
{
  "field": "value"
}

// Response
{
  "id": "123",
  "field": "value",
  "created_at": "2024-01-01T00:00:00Z"
}
```

## Data Flow

1. [Step 1: User action or trigger]
2. [Step 2: System processing]
3. [Step 3: Data transformation]
4. [Step 4: Response or output]

## Deployment Strategy

1. **Build**: [How to build]
2. **Test**: [How to test]
3. **Deploy**: [Deployment command or process]
4. **Verify**: [How to verify deployment]

## Rollback Points

Safe stopping points where the system remains functional:

1. **After Phase 1**: [What works at this point]
2. **After Phase 2**: [What works at this point]

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| [Risk description] | Low/Med/High | Low/Med/High | [How to address] |

## Open Questions

- [ ] [Question that needs to be resolved]
- [ ] [Another question]
