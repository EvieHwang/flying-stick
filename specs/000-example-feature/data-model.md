# Data Model: {{FEATURE_NAME}}

**Spec**: [Link to spec.md]
**Created**: {{DATE}}

## Overview

[Brief description of the data model and its purpose]

## Entities

### {{EntityName}}

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | Primary Key, UUID | Unique identifier |
| name | string | Required, max 255 | Display name |
| created_at | datetime | Required, auto | Creation timestamp |
| updated_at | datetime | Auto | Last modification timestamp |

**Relationships**:
- Has many [OtherEntity]
- Belongs to [ParentEntity]

### {{AnotherEntity}}

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | Primary Key | Unique identifier |
| {{entity}}_id | string | Foreign Key | Reference to {{EntityName}} |
| value | decimal | Required | [Description] |

---

## Database Schema

### SQLite Implementation

```sql
-- {{EntityName}} table
CREATE TABLE {{entity_name}} (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT
);

-- {{AnotherEntity}} table
CREATE TABLE {{another_entity}} (
    id TEXT PRIMARY KEY,
    {{entity}}_id TEXT NOT NULL,
    value REAL NOT NULL,
    FOREIGN KEY ({{entity}}_id) REFERENCES {{entity_name}}(id)
);

-- Indexes
CREATE INDEX idx_{{another_entity}}_{{entity}}_id ON {{another_entity}}({{entity}}_id);
```

### Views

```sql
-- Useful aggregation view
CREATE VIEW v_{{entity}}_summary AS
SELECT
    e.id,
    e.name,
    COUNT(a.id) as item_count,
    SUM(a.value) as total_value
FROM {{entity_name}} e
LEFT JOIN {{another_entity}} a ON e.id = a.{{entity}}_id
GROUP BY e.id, e.name;
```

---

## Python Dataclasses

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from decimal import Decimal

@dataclass
class {{EntityName}}:
    id: str
    name: str
    created_at: datetime
    updated_at: Optional[datetime] = None

@dataclass
class {{AnotherEntity}}:
    id: str
    {{entity}}_id: str
    value: Decimal
```

---

## Seed Data

### {{EntityName}} (initial data)

| id | name |
|----|------|
| example-1 | Example Item 1 |
| example-2 | Example Item 2 |

### {{AnotherEntity}} (initial data)

| id | {{entity}}_id | value |
|----|---------------|-------|
| item-1 | example-1 | 100.00 |
| item-2 | example-1 | 200.00 |

---

## Migration Notes

### From Previous Schema

If migrating from an existing schema:

1. [Migration step 1]
2. [Migration step 2]
3. [Verification step]

### Backward Compatibility

[Notes on maintaining compatibility with existing data]

---

## Data Validation Rules

- **{{EntityName}}.name**: Non-empty, max 255 characters
- **{{AnotherEntity}}.value**: Non-negative decimal
- **Foreign keys**: Must reference existing records

---

## Query Patterns

### Common Queries

```sql
-- Get all items for an entity
SELECT * FROM {{another_entity}} WHERE {{entity}}_id = ?;

-- Get summary statistics
SELECT * FROM v_{{entity}}_summary WHERE id = ?;
```

### Performance Considerations

- Index on `{{entity}}_id` for efficient lookups
- Consider pagination for large result sets
