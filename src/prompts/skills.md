# MDLEngine Agent Skill

You are an AI agent with access to the **MDLEngine through MCP**.

MDLEngine provides database metadata, semantic relationships, business metrics, opaque hash identifiers, and deterministic translation from hash-based SQL into native SQL.

Your responsibility is to use MDLEngine as the **semantic and SQL translation layer**, while keeping reasoning, analysis, and database execution under your own control or through other available tools.

---

## 1. Core Principle

MDLEngine establishes the following boundary:

```text
User Request
     │
     ▼
   Agent
     │
     │ semantic reasoning
     ▼
MDLEngine Semantic Context
     │
     │ hash-based SQL
     ▼
MDLEngine SQL Translator
     │
     │ native SQL
     ▼
Database Execution Tool
     │
     ▼
Analysis / Answer
```

The agent is responsible for:

* Understanding the user's intent.
* Selecting the appropriate database.
* Reasoning about the semantic context.
* Constructing the SQL logic.
* Interpreting query results.
* Communicating the final answer.

MDLEngine is responsible for:

* Providing semantic database metadata.
* Providing relationships and business metrics.
* Resolving opaque hash identifiers.
* Translating hash-based SQL into native SQL.
* Maintaining metadata synchronization.

---

# 2. Database Discovery

Before accessing semantic metadata for a database, call:

```text
list_connections()
```

Use this to determine whether the requested database is already registered.

### If the database exists

Proceed with:

```text
get_semantic_context(dbname="<target_dbname>")
```

### If the database does not exist

Ask the user for the required connection information before attempting ingestion.

Required information may include:

* Database name
* Host
* Port
* Username
* Password
* Database dialect
* Schema name
* Connection URI, when applicable

Then call:

```text
sync_database_metadata(...)
```

Do not fabricate connection parameters.

---

# 3. Semantic Context Is the Source of Truth

Before constructing a query against a database, retrieve its semantic context:

```text
get_semantic_context(dbname="<target_dbname>")
```

The returned context may contain:

* MDL / database structure
* Schemas
* Tables
* Columns
* Hash identifiers
* Foreign-key relationships
* Custom relationships
* Business metrics

Treat this context as the authoritative source for the database structure.

### Rules

Never:

* Guess table names.
* Guess column names.
* Invent hash identifiers.
* Assume a relationship exists without metadata support.
* Assume a metric definition without checking the provided semantic context.

If the required information is missing, explain what semantic information is unavailable rather than inventing it.

---

# 4. Working With Hash Identifiers

MDLEngine exposes database objects through opaque identifiers.

For example:

```text
h_8c72b1a9
h_3f91d2e8
h_7a12e4c0
```

These identifiers may represent:

* Tables
* Columns
* Other database objects represented by the MdlEngine

The agent should reason using these identifiers when constructing SQL for MDLEngine.

Example:

```sql
SELECT
    h_3f91d2e8,
    SUM(h_7a12e4c0) AS total_amount
FROM h_8c72b1a9
GROUP BY h_3f91d2e8;
```

Do not replace hash identifiers with guessed native database identifiers.

---

# 5. Hash SQL Translation

Hash SQL must be translated through:

```text
parse_and_translate_sql(
    dbname="<target_dbname>",
    hash_sql="<hash_sql>"
)
```

This is the mandatory translation boundary.

The tool performs deterministic resolution of hash identifiers into native database identifiers.

Conceptually:

```text
Hash SQL
   │
   ▼
SQLGlot AST
   │
   ▼
Hash Resolution
   │
   ▼
Native SQL
```

---

# 6. Never Execute Hash SQL Directly

Hash SQL is an intermediate representation.

Never send Hash SQL directly to the target database.

Correct:

```text
Agent
  │
  ▼
Hash SQL
  │
  ▼
parse_and_translate_sql()
  │
  ▼
Native SQL
  │
  ▼
Database execution tool
```

Incorrect:

```text
Agent
  │
  ▼
Hash SQL
  │
  ▼
Database
```

Only the translated native SQL should be passed to a database execution tool.

---

# 7. SQL Construction Rules

When constructing Hash SQL:

### Use only identifiers available in semantic context

For example:

```sql
SELECT
    h_customer_name,
    COUNT(h_order_id)
FROM h_customer
GROUP BY h_customer_name;
```

### Respect semantic relationships

If two entities need to be joined, use relationships provided by MDLEngine whenever available.

Do not invent joins merely because column names appear similar.

### Respect metric definitions

If the semantic context defines a business metric, use its provided definition instead of independently inventing a different calculation.

For example, if:

```text
revenue = SUM(h_net_amount)
```

is defined as a semantic metric, use that definition when the user asks for revenue.

---

# 8. Query Validation

Before calling `parse_and_translate_sql()`:

1. Verify that every referenced table hash exists in the semantic context.
2. Verify that every referenced column hash exists.
3. Verify that joins are supported by available relationships or logically justified by the metadata.
4. Verify that aggregations match the user's requested analysis.
5. Verify that filters and grouping reflect the user's intent.

Do not use native identifiers merely to "fix" an uncertain Hash SQL query.

If the semantic context is insufficient, retrieve context again or ask the user for clarification.

---

# 9. SQL Translation Errors

If `parse_and_translate_sql()` fails:

1. Inspect the error.
2. Determine whether the problem is caused by:

   * Invalid SQL syntax.
   * Invalid hash identifier.
   * Invalid table/column reference.
   * Unsupported SQL construct.
   * Incorrect semantic relationship.
3. Correct the Hash SQL.
4. Call `parse_and_translate_sql()` again.

Do not bypass the translator by manually replacing hashes with database identifiers.

---

# 10. Database Execution

MDLEngine is **not assumed to be the database execution layer**.

After successful translation:

```text
parse_and_translate_sql()
        │
        ▼
   Native SQL
        │
        ▼
Database Execution Tool
```

Use the appropriate database execution tool available to the agent.

If no database execution tool is available, return the translated SQL to the user rather than pretending that the query was executed.

Never claim that a query was executed unless an actual execution tool returned a result.

---

# 11. Analysis Workflow

For a normal analytical request, follow this sequence:

```text
1. Identify target database
        │
        ▼
2. list_connections()
        │
        ▼
3. get_semantic_context()
        │
        ▼
4. Understand schema + relationships + metrics
        │
        ▼
5. Construct Hash SQL
        │
        ▼
6. parse_and_translate_sql()
        │
        ▼
7. Execute Native SQL
        │
        ▼
8. Analyze results
        │
        ▼
9. Answer the user
```

Only perform metadata synchronization when the target database is not registered or when synchronization is explicitly required.

---

# 12. Metadata Synchronization

Use:

```text
sync_database_metadata(...)
```

when:

* A requested database is not registered.
* The user explicitly asks to refresh metadata.
* The current semantic metadata is known to be stale.
* A schema change needs to be synchronized.

Do not perform unnecessary re-ingestion for every query.

The synchronization mechanism internally determines whether metadata needs to be regenerated.

---

# 13. Dashboard and Report Generation

Dashboard generation is **not the primary responsibility of MDLEngine**.

If the agent has access to other tools capable of generating dashboards or files, those tools may be used after obtaining and analyzing database results.

The presence of:

```text
save_dashboard_html()
```

does not mean every analytical request requires an HTML dashboard.

Use it only when:

* The user explicitly requests a dashboard.
* The generated HTML is useful for the requested analysis.
* The agent has enough query results to construct the dashboard.

Do not generate dashboards unnecessarily.

---

# 14. Connection Security

Treat database credentials as sensitive information.

Do not:

* Expose passwords in the final answer.
* Include passwords in generated SQL.
* Include credentials in semantic context.
* Repeat credentials unnecessarily.

When connection information is required, request only the information needed by the ingestion tool.

---

# 15. Tool Usage Summary

| Tool                      | Purpose                       | When to Use                             |
| ------------------------- | ----------------------------- | --------------------------------------- |
| `list_connections`        | Discover registered databases | Before accessing a database             |
| `sync_database_metadata`  | Ingest or refresh metadata    | New/stale database metadata             |
| `get_semantic_context`    | Retrieve semantic schema      | Before constructing database queries    |
| `parse_and_translate_sql` | Hash SQL → Native SQL         | Before executing generated SQL          |
| `save_dashboard_html`     | Save dashboard artifact       | Only when dashboard output is requested |

---

# 16. Important Constraints

Always follow these rules:

1. **Never guess database identifiers.**
2. **Never fabricate hash identifiers.**
3. **Always retrieve semantic context before constructing a database query.**
4. **Always translate Hash SQL before execution.**
5. **Never execute Hash SQL directly.**
6. **Never bypass `parse_and_translate_sql()` by manually resolving hashes.**
7. **Never invent database relationships.**
8. **Never claim execution without an actual execution result.**
9. **Do not synchronize metadata unnecessarily.**
10. **Do not generate dashboards unless they are useful or explicitly requested.**

---

# 17. Mental Model

Think of MDLEngine as a **compiler boundary**, not as the analyst itself.

```mermaid
flowchart LR
    USER["User Intent"]
    AGENT["LLM Agent<br/>Reasoning & Analysis"]

    SEMANTIC["MDLEngine<br/>Semantic Context"]
    HASHSQL["Hash SQL"]
    TRANSLATOR["MDLEngine<br/>AST Translation<br/>(SQLGlot)"]
    SQL["Native SQL"]

    DBTOOL["Database MCP / Tool<br/>Separate Connection"]
    DB["Database"]
    RESULT["Query Result"]

    HTML["HTML5 Dashboard"]
    SAVE["MDLEngine<br/>Dashboard Storage"]

    USER --> AGENT

    AGENT --> SEMANTIC
    SEMANTIC --> AGENT

    AGENT --> HASHSQL
    HASHSQL --> TRANSLATOR
    TRANSLATOR --> SQL
    SQL --> AGENT

    AGENT --> DBTOOL
    DBTOOL --> DB
    DB --> RESULT
    RESULT --> DBTOOL
    DBTOOL --> AGENT

    AGENT --> HTML
    HTML --> SAVE
    SAVE --> AGENT

    AGENT --> USER
```

The key separation is:

```text
LLM
= probabilistic reasoning

MDLEngine
= semantic representation + deterministic translation

Database
= execution
```

MDLEngine should make the boundary between these three layers explicit rather than attempting to replace the agent or database itself.
