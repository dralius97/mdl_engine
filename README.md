# MDLEngine

**Hash-based Semantic Layer for LLM-driven SQL Generation**

MDLEngine is a lightweight MCP server that acts as a semantic translation layer between an LLM agent and a relational database.

It allows an LLM to reason about database structure using **stable hash identifiers** instead of relying on raw database identifiers throughout its working context. The generated hash-based SQL is then deterministically translated back into native SQL before execution.

The core idea:

```mermaid
flowchart TD
    DB["Database Schema"]
    INGEST["Metadata Ingestion"]
    HASH["Stable Hash Identifiers"]
    CONTEXT["Semantic Context"]
    LLM["LLM Agent"]
    HSQL["Hash-based SQL"]
    PARSER["AST Parsing & Hash Resolution"]
    NSQL["Native SQL"]
    TARGET["Target Database"]

    DB --> INGEST
    INGEST --> HASH
    HASH --> CONTEXT
    CONTEXT --> LLM
    LLM --> HSQL
    HSQL --> PARSER
    PARSER --> NSQL
    NSQL --> TARGET
```

---

## Why MDLEngine?

LLM-based SQL generation introduces several problems when the model interacts directly with a database:

* Large schemas are difficult to reason about consistently.
* Identifiers can become ambiguous when many databases and connections are involved.
* Generated SQL is probabilistic and should not directly become executable SQL.
* Business relationships and semantic definitions often exist outside the physical database schema.
* The database schema may change and the semantic context needs to remain synchronized.

MDLEngine separates these concerns.

The LLM works with a semantic representation of the database, while MDLEngine is responsible for deterministic identifier resolution and SQL translation.

The hash identifiers are **not intended as a security or privacy boundary**. Their primary purpose is to provide stable object identity and reduce identifier ambiguity, especially when an agent needs to reason across multiple connections.

---

## Core Concepts

### 1. Opaque Schema Representation

Database objects are converted into deterministic hash identifiers.

The canonical internal path includes the connection alias and physical database identity:

```text
<alias>::<dbname>::<schema>::<table>::<column>
```

For example:

```text
staging::application::sales::orders::customer_id
```

becomes a stable hash identifier such as:

```text
h_8f31c2...
```

The original identifier is stored in an internal hashmap:

```text
h_8f31c2... → staging::application::sales::orders::customer_id
```

The `::` delimiter is simply the canonical internal representation used to construct hierarchical database paths before hashing. It is not a core feature by itself.

---

### 2. Semantic Metadata

MDLEngine represents database metadata through several semantic layers:

```mermaid
flowchart TD
    MDL["MDL"]
    SCHEMA["Schemas"]
    TABLE["Tables"]
    COLUMN["Columns"]

    REL["Relations"]
    FK["Foreign Keys"]
    JOIN["Custom Relationships"]

    MET["Metrics"]
    BUSINESS["Business Definitions"]

    MDL --> SCHEMA
    SCHEMA --> TABLE
    TABLE --> COLUMN

    REL --> FK
    REL --> JOIN

    MET --> BUSINESS
```

This allows the LLM to reason about the database beyond raw table definitions.

For example, the model can receive:

```text
h_a12f... = customer table
h_71bc... = order table
h_99d1... = customer_id
h_42ce... = order.customer_id
```

together with their relationships and business metadata.

---

### 3. Hash-based SQL Translation

The LLM does not produce native database SQL directly.

Instead, it produces SQL referencing the opaque identifiers:

```sql
SELECT
    h_customer_name,
    COUNT(h_order_id)
FROM h_customer
JOIN h_order
    ON h_customer_id = h_order_customer_id
GROUP BY h_customer_name;
```

MDLEngine parses the SQL into an AST using `sqlglot`, resolves the hash identifiers, and produces native SQL.

The important boundary is:

```mermaid
flowchart LR
    LLM["LLM Agent"]
    HSQL["Hash SQL"]
    TRANSLATE["AST Translation<br/>+ Hash Resolution"]
    NSQL["Native SQL"]

    LLM -->|"Probabilistic reasoning"| HSQL
    HSQL -->|"Deterministic translation"| TRANSLATE
    TRANSLATE --> NSQL
```

The LLM is responsible for **reasoning**.

MDLEngine is responsible for **deterministic translation**.

---

### 4. AST-based SQL Processing

Generated SQL is parsed into an Abstract Syntax Tree before identifier translation.

This avoids treating SQL as plain text replacement.

```mermaid
flowchart TD
    HSQL["Hash SQL"]
    PARSER["SQLGlot Parser"]
    AST["SQL AST"]
    TABLE["Resolve Table Hashes"]
    COLUMN["Resolve Column Hashes"]
    STRUCTURE["Preserve SQL Structure"]
    NSQL["Native SQL"]

    HSQL --> PARSER
    PARSER --> AST
    AST --> TABLE
    AST --> COLUMN
    AST --> STRUCTURE

    TABLE --> NSQL
    COLUMN --> NSQL
    STRUCTURE --> NSQL
```

This also provides a controlled point where validation can be added before SQL reaches the target database.

---

### 5. MCP Interface

MDLEngine exposes its functionality through the Model Context Protocol (MCP), allowing an external agent such as Hermes to interact with the semantic layer as a collection of tools.

The MCP layer is an integration boundary; the semantic and translation logic remains independent from the agent itself.

---

## Architecture

MDLEngine follows a lightweight separation between domain logic, application services, infrastructure, and external interfaces.

```mermaid
flowchart TD
    AGENT["LLM Agent<br/>(Hermes)"]

    MCP["MCP Adapter"]

    APP["Application Layer"]
    INGEST["Ingestion Service"]
    ENGINE["MDL Engine Service"]

    DOMAIN["Domain / Core"]
    HASHING["Hashing"]
    SCHEMA["Schema Parsing"]
    SQL["SQL Translation"]
    RELATION["Relationship Logic"]

    INFRA["Infrastructure"]
    DB["Database Inspector"]
    YAML["YAML Storage"]
    SQLITE["SQLite"]

    AGENT -->|"MCP"| MCP
    MCP --> APP

    APP --> INGEST
    APP --> ENGINE

    INGEST --> DOMAIN
    ENGINE --> DOMAIN

    DOMAIN --> HASHING
    DOMAIN --> SCHEMA
    DOMAIN --> SQL
    DOMAIN --> RELATION

    INGEST --> INFRA
    ENGINE --> INFRA

    INFRA --> DB
    INFRA --> YAML
    INFRA --> SQLITE
```

The architecture is intentionally pragmatic. The purpose of the separation is to keep database access, persistence, MCP transport, and semantic transformations from being tightly coupled.

---

## Metadata Synchronization

MDLEngine can synchronize its metadata with the target database.

The synchronization flow is:

```mermaid
flowchart TD
    DB["Target Database"]
    INSPECT["Inspect Schema"]
    GENERATE["Generate Metadata"]
    FINGERPRINT["Calculate Schema Fingerprint"]
    COMPARE{"Schema Changed?"}
    SKIP["Skip Synchronization"]
    UPDATE["Regenerate Metadata"]

    DB --> INSPECT
    INSPECT --> GENERATE
    GENERATE --> FINGERPRINT
    FINGERPRINT --> COMPARE

    COMPARE -->|"No"| SKIP
    COMPARE -->|"Yes"| UPDATE
```

A schema fingerprint is used for change detection so that unchanged databases do not require unnecessary metadata regeneration.

The fingerprint is a synchronization mechanism and is separate from the hash identifiers used for database object identity.

---

## Metadata Storage

The current implementation stores generated MDL metadata as human-readable YAML files and internal state in SQLite.

Per-connection MDL files are stored under:

```text
~/.mdlEngine/
└── configs/
    └── local_mdl_<alias>.yaml
```

SQLite stores internal state in:

```text
~/.mdlEngine/
└── metadata.db
```

The SQLite database currently stores:

* Registered database connections
* Hash-to-canonical-path mappings
* Relationship metadata
* Schema fingerprints
* SQL translation audit logs

The alias is the logical identity used to address a connection. The physical `dbname` is connection metadata and does not need to be globally unique.

---

## MCP Tools

| Tool | Parameters | Description |
| --- | --- | --- |
| `list_connections` | None | Lists registered database connections. |
| `sync_database_metadata` | `alias`, connection information, `dialect`, `schema_name`, `force_reingest` | Inspects the target database and synchronizes semantic metadata. |
| `get_semantic_context` | `alias` | Returns the combined MDL, relations, and semantic metadata context for an LLM agent. |
| `parse_and_translate_sql` | `alias`, `hash_sql` | Parses hash-based SQL, resolves identifiers, and produces native SQL. |
| `save_dashboard_html` | `filename`, `html_content` | Saves generated dashboard/report artifacts. |

---

## Installation

### Prerequisites

- Python 3.11+ for local installation
- Docker Engine and Docker Compose plugin for containerized deployment

### Local installation

From the repository root:

```bash
pip install .
python -m src.main
```

The MCP server listens on port `38000` and exposes the SSE endpoint at:

```text
http://localhost:38000/sse
```

Keep the server running while an MCP client or agent connects to it.

### Docker Compose deployment

The repository includes `Dockerfile` and `compose.template.yaml`. From the repository root, build and start MDLEngine:

```bash
docker compose -f compose.template.yaml build mdl-engine
docker compose -f compose.template.yaml up -d
docker compose -f compose.template.yaml ps
docker compose -f compose.template.yaml logs --tail=100 mdl-engine
```

The service exposes port `38000` on the host. From the host machine, use:

```text
http://localhost:38000/sse
```

The Compose template persists data through these mounts:

| Container path | Host storage | Purpose |
| --- | --- | --- |
| `/root/.mdlEngine/configs` | `./data/configs` | Per-connection MDL configuration files |
| `/root/.mdlEngine/outputs` | `./data/outputs` | Generated HTML dashboards and reports |
| `/root/.mdlEngine/database` | Named volume `mdl_engine_metadata` | Internal SQLite metadata database |

The named volume is separate from the generated output directories. Do not use `docker compose down -v` if you want to preserve the metadata database.

To inspect the mounted paths and verify the effective database/output directories:

```bash
docker inspect mdl-engine --format '{{json .Mounts}}'
docker compose -f compose.template.yaml exec mdl-engine python -c "from src.config import Config; print('DB:', Config.get_db_path()); print('OUTPUT:', Config.get_output_dir())"
docker compose -f compose.template.yaml exec mdl-engine sh -c 'ls -lah /root/.mdlEngine/database /root/.mdlEngine/configs /root/.mdlEngine/outputs'
```

For a quick SSE connectivity check:

```bash
curl -i -N --max-time 5 http://localhost:38000/sse
```

An SSE connection may remain open until the timeout; check the server logs for startup or connection errors as well.

### PostgreSQL driver

MDLEngine currently declares `psycopg[binary]` in `requirements.txt`. This installs Psycopg 3 with its packaged binary implementation, avoiding a dependency on a system `libpq` installation in the container. The separate `psycopg2-binary` package provides the `psycopg2` module and does not satisfy imports of `psycopg`.

SQLAlchemy's PostgreSQL URL driver must match an installed driver. For Psycopg 3, use a URL such as `postgresql+psycopg://...`; a plain `postgresql://...` URL may select a different driver depending on the installed packages and SQLAlchemy configuration.

---

## Running with Hermes

MDLEngine runs as a separate service alongside an agent such as Hermes.

```text
Hermes Agent
    │
    │ MCP / SSE
    ▼
MDLEngine :38000
    │
    ▼
Target Database(s)
```

### 1. Install the MDLEngine skill

The source skill is maintained at `src/prompts/skills.md`. From the repository root, copy it to the lowercase Hermes skills directory:

```bash
mkdir -p ~/.hermes/skills/mdlEngine
cp src/prompts/skills.md ~/.hermes/skills/mdlEngine/SKILL.md
```

Ensure the destination is inside the Hermes home directory used by the running agent. If Hermes runs in a container with a mounted home directory, copy the file in that environment or into the corresponding host-mounted directory.

### 2. Configure the MCP server

Add this entry to `~/.hermes/config.yaml` and merge it with the existing configuration:

```yaml
mcp_servers:
  mdl-engine:
    url: http://mdl-engine:38000/sse
    enabled: true
```

The hostname `mdl-engine` works when Hermes and MDLEngine are attached to the same Docker network. In the tested local Compose setup, the network is `mdl-engine_default`. If Hermes runs in a separate container on the same Docker host, connect it to that network:

```bash
docker network connect mdl-engine_default <agent-container>
```

Replace `<agent-container>` with the actual Hermes container name or ID. If the Compose project or network has a different name, inspect available networks with `docker network ls` and use the actual network name.

If Hermes runs outside that Docker network, configure an address reachable from its environment instead.

### 3. Restart Hermes and verify tool execution

Restart Hermes after changing the skill or MCP configuration. Confirm more than tool discovery: ask Hermes to execute an actual MDLEngine tool and verify that the tool result is returned.

For an analytical request, the expected workflow is:

1. Discover or register the target connection using its logical alias.
2. Run `sync_database_metadata` when the connection is new or metadata needs refreshing.
3. Retrieve `get_semantic_context`.
4. Construct hash-based SQL and call `parse_and_translate_sql`.
5. Execute the translated native SQL using the available database execution tool.
6. Use the returned data to generate a dashboard and save it with `save_dashboard_html`.

MDLEngine translates SQL; database query execution is performed by the agent's available database execution tool.

---

## End-to-End Validation

The initial local Docker deployment was validated through the following path:

- Docker image built and the service started successfully.
- The MCP SSE endpoint connected and returned the registered tool list.
- Persistence paths were checked.
- Hermes discovered MDLEngine and invoked its tools.
- PostgreSQL metadata synchronization completed after the Psycopg 3 binary dependency was declared.
- Hermes retrieved semantic context, used hash identifiers for the required tables and columns, and translated hash SQL through `parse_and_translate_sql`.
- The translated SQL results were used to generate the patient demographics and payment dashboard.

The reported dashboard artifact was saved inside the container at:

```text
/root/.mdlEngine/outputs/patient_demographics_payment.html
```

Because `/root/.mdlEngine/outputs` is mounted to `./data/outputs` by the Compose template, the corresponding host path is:

```text
./data/outputs/patient_demographics_payment.html
```

This records the successful initial end-to-end test; it does not claim that automated integration tests currently cover every database dialect.

## Design Principles

### Deterministic Core, Probabilistic Interface

MDLEngine intentionally separates probabilistic reasoning from deterministic execution.

```mermaid
flowchart LR
    LLM["LLM Agent"]
    HSQL["Hash SQL"]

    subgraph MDL["MDLEngine"]
        AST["AST Translation"]
        RESOLVE["Hash Resolution"]
    end

    NSQL["Native SQL"]

    LLM -->|"Probabilistic reasoning"| HSQL
    HSQL --> AST
    AST --> RESOLVE
    RESOLVE -->|"Deterministic result"| NSQL
```

The goal is not to eliminate LLM uncertainty.

The goal is to **keep uncertainty on the reasoning side of the boundary and make identifier translation deterministic**.

---

## Current Scope

MDLEngine currently focuses on:

* Database schema ingestion
* Hash-based identifier abstraction
* Semantic metadata representation
* Relationship metadata
* Hash-based SQL translation
* AST-based SQL processing
* MCP integration
* Metadata synchronization
* SQL translation auditing

---

## License

MIT License.
