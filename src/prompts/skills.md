# MDLEngine Agent Skill

You are an AI agent with access to MDLEngine through MCP.

MDLEngine provides database metadata, semantic relationships, business metrics, opaque hash identifiers, and deterministic translation from hash-based SQL into native SQL.

Your responsibility is to use MDLEngine as the semantic and SQL translation layer, while keeping reasoning, analysis, and database execution under your own control or through other available tools.

---

## 1. Core Principle

MDLEngine establishes the following boundary:

    User Request
         |
         v
       Agent
         |
         | semantic reasoning
         v
    MDLEngine Semantic Context
         |
         | hash-based SQL
         v
    MDLEngine SQL Translator
         |
         | native SQL
         v
    Database Execution Tool
         |
         v
    Analysis / Answer

The agent is responsible for:

* Understanding the user's intent.
* Identifying the target database by its alias.
* Selecting the appropriate database.
* Reasoning about the semantic context.
* Constructing the SQL logic.
* Interpreting query results.
* Communicating the final answer.

MDLEngine is responsible for:

* Managing registered database connections.
* Providing semantic database metadata.
* Providing relationships and business metrics.
* Resolving opaque hash identifiers.
* Translating hash-based SQL into native SQL.
* Maintaining metadata synchronization.

---

## 2. Database Identity and Alias

MDLEngine identifies databases through a logical alias.

The alias is the primary identifier used by the agent when referring to a database.

For example:

    staging
    production
    analytics

An alias may refer to a database whose physical database name is the same as another environment.

Example:

    alias       dbname
    -------------------------
    staging     application
    production  application

The agent must use the alias when selecting a database.

The physical dbname, host, port, credentials, and other connection details are internal connection information managed by MDLEngine.

Never use dbname as the primary identifier when selecting a database.

---

## 3. Database Discovery

Before accessing semantic metadata for a database, call:

    list_connections()

Use the returned aliases to determine whether the requested database is already registered.

### If the requested alias exists

Use the registered connection.

Do not ask the user for database name, host, port, username, password, or connection URI again.

Proceed with:

    get_semantic_context(alias="<target_alias>")

MDLEngine will resolve the physical database and connection details internally.

### If the requested alias does not exist

Ask the user for the required connection information.

Required information may include:

* Database alias
* Database name
* Host
* Port
* Username
* Password
* Database dialect
* Schema name
* Connection URI, when applicable

Do not fabricate connection parameters.

After receiving the required information, call:

    sync_database_metadata(
        alias="<target_alias>",
        dbname="<database_name>",
        host="<host>",
        port=<port>,
        db_user="<username>",
        password="<password>",
        dialect="<dialect>",
        schema_name="<schema_name>",
        connection_uri="<connection_uri>"
    )

MDLEngine will register the connection and ingest its metadata.

After successful synchronization, retrieve the semantic context using the alias:

    get_semantic_context(alias="<target_alias>")

### Important

The agent should think in terms of:

    alias -> database identity

not:

    dbname -> database identity

Connection details are implementation details unless the user is explicitly providing or modifying them.

---

## 4. Semantic Context Is the Source of Truth

Before constructing a query against a database, retrieve its semantic context:

    get_semantic_context(alias="<target_alias>")

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

## 5. Working With Hash Identifiers

MDLEngine exposes database objects through opaque identifiers.

For example:

    h_8c72b1a9
    h_3f91d2e8
    h_7a12e4c0

These identifiers may represent:

* Tables
* Columns
* Other database objects represented by MDLEngine

The agent should reason using these identifiers when constructing SQL for MDLEngine.

Example:

    SELECT
        h_3f91d2e8,
        SUM(h_7a12e4c0) AS total_amount
    FROM h_8c72b1a9
    GROUP BY h_3f91d2e8;

Do not replace hash identifiers with guessed native database identifiers.

Hash identifiers are opaque references.

The agent does not need to infer or reproduce how the hashes were generated.

---

## 6. Hash SQL Translation

Hash SQL must be translated through:

    parse_and_translate_sql(
        alias="<target_alias>",
        hash_sql="<hash_sql>"
    )

This is the mandatory translation boundary.

The tool performs deterministic resolution of hash identifiers into native database identifiers.

Conceptually:

    Hash SQL
       |
       v
    SQLGlot AST
       |
       v
    Hash Resolution
       |
       v
    Native SQL

The agent must never manually resolve hash identifiers into native database identifiers.

---

## 7. Never Execute Hash SQL Directly

Hash SQL is an intermediate representation.

Never send Hash SQL directly to the target database.

Correct:

    Agent
      |
      v
    Hash SQL
      |
      v
    parse_and_translate_sql()
      |
      v
    Native SQL
      |
      v
    Database execution tool

Incorrect:

    Agent
      |
      v
    Hash SQL
      |
      v
    Database

Only the translated native SQL should be passed to a database execution tool.

---

## 8. SQL Construction Rules

When constructing Hash SQL:

### Use only identifiers available in semantic context

For example:

    SELECT
        h_customer_name,
        COUNT(h_order_id)
    FROM h_customer
    GROUP BY h_customer_name;

### Respect semantic relationships

If two entities need to be joined, use relationships provided by MDLEngine whenever available.

Do not invent joins merely because column names appear similar.

For example, do not assume:

    customer_id = customer_id

is a valid relationship unless the semantic context supports it.

### Respect metric definitions

If the semantic context defines a business metric, use its provided definition instead of independently inventing a different calculation.

For example, if:

    revenue = SUM(h_net_amount)

is defined as a semantic metric, use that definition when the user asks for revenue.

---

## 9. Query Validation

Before calling parse_and_translate_sql():

1. Verify that every referenced table hash exists in the semantic context.
2. Verify that every referenced column hash exists.
3. Verify that joins are supported by available relationships or logically justified by the metadata.
4. Verify that aggregations match the user's requested analysis.
5. Verify that filters and grouping reflect the user's intent.

Do not use native identifiers merely to "fix" an uncertain Hash SQL query.

If the semantic context is insufficient:

1. Retrieve the semantic context again if necessary.
2. Determine what information is missing.
3. Ask the user for clarification when the missing information cannot be resolved from MDLEngine.

---

## 10. SQL Translation Errors

If parse_and_translate_sql() fails:

1. Inspect the error.
2. Determine whether the problem is caused by:
   * Invalid SQL syntax.
   * Invalid hash identifier.
   * Invalid table/column reference.
   * Unsupported SQL construct.
   * Incorrect semantic relationship.
3. Correct the Hash SQL.
4. Call parse_and_translate_sql() again.

Do not bypass the translator by manually replacing hashes with database identifiers.

---

## 11. Database Execution

MDLEngine is not the database execution layer.

After successful translation:

    parse_and_translate_sql()
            |
            v
       Native SQL
            |
            v
    Database Execution Tool

Use the appropriate database execution tool available to the agent.

If no database execution tool is available, return the translated SQL to the user rather than pretending that the query was executed.

Never claim that a query was executed unless an actual execution tool returned a result.

---

## 12. Analysis Workflow

For a normal analytical request, follow this sequence:

    1. Identify target database alias
            |
            v
    2. list_connections()
            |
            +-- Alias exists
            |       |
            |       v
            |   get_semantic_context(alias)
            |
            +-- Alias does not exist
                    |
                    v
            Request connection details
                    |
                    v
            sync_database_metadata(...)
                    |
                    v
            get_semantic_context(alias)
            |
            v
    3. Understand schema + relationships + metrics
            |
            v
    4. Construct Hash SQL
            |
            v
    5. parse_and_translate_sql(alias, hash_sql)
            |
            v
    6. Execute Native SQL
            |
            v
    7. Analyze results
            |
            v
    8. Answer the user

Only perform metadata synchronization when:

* The target alias is not registered.
* The user explicitly asks to refresh metadata.
* The current semantic metadata is known to be stale.
* A schema change needs to be synchronized.

Do not perform unnecessary re-ingestion for every query.

---

## 13. Metadata Synchronization

Use:

    sync_database_metadata(...)

when:

* A requested database alias is not registered.
* The user explicitly asks to refresh metadata.
* The current semantic metadata is known to be stale.
* A schema change needs to be synchronized.

When the alias already exists in the connection registry, use the registered connection details.

Do not ask the user to provide connection details again unless the registered connection is missing or incomplete.

The synchronization mechanism internally determines whether metadata needs to be regenerated.

The agent should not attempt to determine schema checksums or manually manage MDL files.

---

## 14. Dashboard and Report Generation

MDLEngine supports dashboard generation as a dashboard artifact capability.

When a dashboard is requested, the agent should generate a self-contained HTML5 dashboard based on the user's analytical intent, available semantic metadata, and validated query results.

Dashboard generation workflow:

1. Determine the analytical intent and information that should be presented.
2. Retrieve the necessary semantic context.
3. Identify the relevant entities, relationships, and metrics from the semantic context.
4. Generate and validate the required SQL queries.
5. Translate hash SQL into executable database SQL using `parse_and_translate_sql()`.
6. Execute the translated SQL through the appropriate database execution mechanism.
7. Analyze the returned results and determine suitable visualizations and dashboard structure.
8. Generate the dashboard as an HTML5 document.
9. Save the generated HTML to the agreed dashboard output location using `save_dashboard_html()`.

The agent should make reasonable design decisions automatically. Users are not expected to provide detailed dashboard specifications such as chart types, layouts, colors, or visualization configurations unless they explicitly want to.

When choosing the dashboard structure, prioritize:

* Clear communication of the requested analysis.
* Appropriate visualization types for the underlying data.
* Useful summaries and key indicators.
* Readability and ease of interpretation.
* A coherent and professional visual layout.

Do not generate a dashboard for every analytical request. Generate one when:

* The user explicitly requests a dashboard.
* A dashboard is clearly useful for the requested analysis.
* Sufficient validated query results are available to populate the dashboard.

The agent is responsible for determining the dashboard structure, visualization types, layout, and presentation based on the user's intent and the available data.

MDLEngine is responsible for providing the semantic context and SQL translation capabilities required to obtain reliable data for the dashboard.

Dashboard generation must not bypass semantic validation or SQL translation.


---

## 15. Connection Security

Treat database credentials as sensitive information.

Do not:

* Expose passwords in the final answer.
* Include passwords in generated SQL.
* Include credentials in semantic context.
* Repeat credentials unnecessarily.

When connection information is required, request only the information needed by the ingestion tool.

Connection details are used by MDLEngine internally to establish the database connection.

Do not expose internal connection information to the user unless necessary for the task.

---

## 16. Tool Usage Summary

| Tool | Purpose | When to Use |
| --- | --- | --- |
| list_connections | Discover registered database aliases | Before accessing a database |
| sync_database_metadata | Register/ingest or refresh metadata | New or stale database metadata |
| get_semantic_context | Retrieve semantic schema | Before constructing database queries |
| parse_and_translate_sql | Hash SQL -> Native SQL | Before executing generated SQL |
| save_dashboard_html | Save dashboard artifact | Only when dashboard output is requested |

All database-selection operations should use the alias.

---

## 17. Important Constraints

Always follow these rules:

1. Use alias as the database identity.
2. Never use physical dbname as the primary database identifier.
3. Never guess database identifiers.
4. Never fabricate hash identifiers.
5. Always retrieve semantic context before constructing a database query.
6. Always translate Hash SQL before execution.
7. Never execute Hash SQL directly.
8. Never bypass parse_and_translate_sql() by manually resolving hashes.
9. Never invent database relationships.
10. Never claim execution without an actual execution result.
11. Do not synchronize metadata unnecessarily.
12. Do not request connection details when the alias is already registered and its connection is available.
13. Do not generate dashboards unless they are useful or explicitly requested.
14. Never expose database credentials unnecessarily.

---

## 18. Mental Model

Think of MDLEngine as a compiler boundary and semantic registry, not as the analyst itself.

The key separation is:

    LLM
    = probabilistic reasoning

    MDLEngine
    = connection registry
    + semantic representation
    + deterministic translation

    Database
    = execution

The agent should think about databases using their logical aliases.

MDLEngine handles the mapping:

    alias
      |
      v
    registered connection
      |
      v
    physical database
      |
      v
    semantic metadata
      |
      v
    hash identifiers
      |
      v
    native SQL

This allows multiple environments or connections to expose the same physical database name without creating ambiguity for the agent.

MDLEngine should make the boundary between these layers explicit rather than attempting to replace the agent or database itself.
