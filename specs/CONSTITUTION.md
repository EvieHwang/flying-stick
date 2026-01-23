# {{PROJECT_NAME}} Constitution

This document establishes the foundational architectural principles, design philosophy, and decision-making framework for the {{PROJECT_NAME}} project.

## Project Mission

{{PROJECT_DESCRIPTION}}

## Architectural Principles

### 1. Simplicity First

**Rationale**: Complexity is the enemy of maintainability. Optimize for clarity and ease of understanding.

**Implementation**:
- File-based data storage (JSON/SQLite) over managed databases where appropriate
- Static hosting where possible (S3 + CloudFront)
- Minimal infrastructure to maintain
- No over-engineering for hypothetical scale

**Trade-offs Accepted**:
- Not designed for massive concurrent usage without explicit scaling work
- Manual backup responsibility for simple storage
- Limited to reasonable data volumes for the use case

### 2. Serverless When Dynamic

**Rationale**: Pay only for what you use, zero server maintenance.

**Implementation**:
- AWS Lambda for any server-side processing
- API Gateway for API endpoints
- S3 for static frontend hosting
- CloudFront for CDN and HTTPS

**Cost Guardrails**:
- No always-on compute
- No provisioned concurrency (unless explicitly needed)
- Cold starts are acceptable
- Target: reasonable AWS costs for the scale

### 3. Claude API for Intelligence

**Rationale**: Leverage AI for intelligent features without building complex rules.

**Implementation**:
- Claude API for AI-powered features
- Simple rules engine for obvious matches first (reduce API calls)
- Configurable prompts for domain-specific logic
- Human review queue for low-confidence items

**Cost Guardrails**:
- Use Claude Haiku for simple tasks (cheapest)
- Cache/remember patterns where possible
- Batch processing where applicable

### 4. Appropriate Access Control

**Rationale**: Security should match the risk profile of the application.

**Implementation**:
- Authentication method appropriate for the use case
- Role-based access where needed
- Secure credential storage

**Trade-offs Accepted**:
- Complexity should match the security requirements
- Not every app needs enterprise-grade auth

### 5. Output Formats as First-Class Citizens

**Rationale**: Users need data in formats they can use.

**Implementation**:
- PDF reports where printable output is needed
- CSV/Excel exports for data portability
- Clean, professional formatting

### 6. Data Portability

**Rationale**: Data belongs to the users; they should be able to take it anywhere.

**Implementation**:
- All data exportable in standard formats (CSV, JSON, etc.)
- No proprietary formats
- Clear documentation of data structure
- Easy to migrate to different system if needed

## Data Principles

### Data Integrity
- Data validation at boundaries (input/output)
- Consistent formats and schemas
- Clear error handling for invalid data

### Data Access
- Appropriate access controls
- Audit trails where required
- Clear data ownership

## Development Principles

### Specification-Driven
- Features start with specs in `/specs`
- Specs define requirements before implementation
- Implementation follows specs; deviations require spec updates

### Test Coverage
- Core business logic must have tests
- Critical calculations and transformations must be tested
- UI can have lighter test coverage

### Incremental Delivery
- Each user story is independently valuable
- MVP first, then iterate
- Do not build features "for later"

## Technology Constraints

### Must Use
- Python 3.12+ for backend
- AWS for hosting
- Claude API for AI features

### Prefer
- React or vanilla JS for frontend
- SQLite or JSON for simple data storage
- AWS SAM for deployment

### Avoid
- Heavy frameworks unless justified
- Managed databases for simple use cases
- Complex build systems
- Dependencies with large footprints

## Success Metrics

### MVP Success
- [ ] Core functionality works end-to-end
- [ ] Users can complete primary workflows
- [ ] Performance is acceptable
- [ ] AWS costs are reasonable

### Full Success
- [ ] Users can complete tasks efficiently
- [ ] Error handling is graceful
- [ ] Documentation is clear
- [ ] Handoff to new maintainers is straightforward

## Revision History

- **{{DATE}}**: Initial constitution established
