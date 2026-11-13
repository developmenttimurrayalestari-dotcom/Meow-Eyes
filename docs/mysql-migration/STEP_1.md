# Step 1 — MySQL 5.7.24-log schema and backend configuration

> Update 9 November 2026: current application head is `20261109_0003` and there are 79 application tables. The original 68-table foundation and its historical 0001/0002 migration notes remain below. Use [the Meowsurement runbook](../optifit/RUNBOOK.md) and [schema](../optifit/SCHEMA.md) for the 0003 upgrade.

## Delivery status and boundary

This document records the Step 1 schema foundation for the requested
**Oracle MySQL 5.7.24-log** server. The architecture and setup requirements below
remain valid. The package now also contains the approved Step 2 migration:
`server:app`, routes, scheduled jobs and seeders use MySQL. See
[STEP_2.md](STEP_2.md) for the current application entry point and importer.

`mysql_bootstrap:app` remains a separate **schema-only** diagnostic backend;
it does not mount the storefront routes. No live database has been imported
or deployed in this workspace.

The source archive contains no database export or connection configuration.
The schema is derived from all 37 collections used by the code, plus the new
feature requirements. Real data quality and record counts are not known.

The first Step 1 package targeted MySQL 8.4. Its initial Alembic revision is
retained, and a new compatibility revision is added. This package changes the
application/schema target; it does not downgrade an installed MySQL server.

## Target server and the `-log` suffix

The supported runtime family is **MySQL 5.7, patch 5.7.24 or later**. The exact
server string `5.7.24-log` is accepted. Older MySQL releases, MySQL 8.x and
MariaDB are rejected by this target's version gate.

The suffix `-log` indicates that at least one of general-query, slow-query or
binary logging is enabled. It does not change the SQL feature level and does
not establish that binary logging specifically is enabled. Source:
[MySQL 5.7 `version` variable](https://docs.oracle.com/cd/E17952_01/mysql-5.7-en/server-system-variables.html#sysvar_version).

## Architecture decisions

| Area | Decision and reason |
| --- | --- |
| Database | Oracle MySQL 5.7.24-log, using InnoDB, foreign keys and unique keys. The supported family is MySQL 5.7 patch 24 or later. |
| Row validation | MySQL 5.7 ignores native CHECK predicates. The 97 row predicates are enforced by 90 `BEFORE INSERT` / `BEFORE UPDATE` validation triggers across 45 tables. A false predicate raises SQLSTATE `45000`; nullable-field rules retain their SQL three-valued behavior. |
| Access layer | SQLAlchemy 2 asynchronous engine using `asyncmy`; one `AsyncSession` per request/job, explicit service-owned transaction boundaries. |
| Versioning | Initial history `20261106_0001` is retained; current head `20261106_0002` adds MySQL 5.7 compatibility and trigger enforcement. The initial revision body is not rewritten. |
| Character set | `utf8mb4`, table collation `utf8mb4_unicode_ci`; opaque IDs and token hashes have binary collation. Case/accent collisions in emails/slugs/SKUs must be checked before import. |
| InnoDB storage | Explicit `ROW_FORMAT=DYNAMIC`, with `innodb_large_prefix=ON` and an InnoDB page size of at least 16 KiB for the schema's wide utf8mb4 keys. The server preflight only reads these settings; it does not change server globals. |
| Identifiers | Existing application string IDs are retained in `VARCHAR(64)`. Users keep `user_id`; sessions keep `session_id`. MongoDB `_id` becomes provenance, not a replacement public key. |
| Money | `DECIMAL(18,2)` and Python `Decimal`. A documented rounding and reconciliation policy is required before converting old floating-point amounts. |
| Time | MySQL `DATETIME(6)` interpreted as UTC; the Python type rejects naive timestamps and returns aware UTC datetimes. Display conversions belong at the API/UI boundary. |
| Relations | Normalize product variants, category memberships, images, order items/components, reviews and campaign membership. Native JSON, available in this MySQL version, is reserved for variable attributes, provider envelopes, configuration, and explicitly documented snapshots. JSON columns have no non-NULL server defaults. |
| Deletion | Preserve orders and financial references; deactivate users/catalog entries rather than deleting referenced records. Only appropriate nonfinancial child records cascade. |
| Transactions | Stock, order creation, coupons, Flash Sale quotas, points, and payment transitions must share atomic service operations in Step 2 and later. Tables alone do not supply those business guarantees. |
| Privacy | Prescription media must be private and authorized by ownership. The existing public CMS upload/static-file endpoint must not be reused for prescription photos. Credentials stay outside database content and source control. |

Native CHECK clauses are omitted from generated/executed MySQL table DDL. The
logical predicates remain in SQLAlchemy metadata for the schema reference and
portable behavioral tests. The MySQL installation uses the validation triggers
for these rules. MySQL 5.7 CHECK behavior is documented in the
[CREATE TABLE manual](https://docs.oracle.com/cd/E17952_01/mysql-5.7-en/create-table.html).

The widest declared index needs 2,552 bytes. The local Compose configuration
chooses 16 KiB pages and also sets Barracuda/file-per-table preferences, but
those latter two settings are not hard runtime requirements when DYNAMIC row
format is explicitly requested. The operator integrity check verifies that
the actual application tables use InnoDB and DYNAMIC. Sources:
[MySQL 5.7 row formats](https://docs.oracle.com/cd/E17952_01/mysql-5.7-en/innodb-row-format.html)
and [file-format selection](https://docs.oracle.com/cd/E17952_01/mysql-5.7-en/innodb-file-format-enabling.html).

## What to review

- `backend/mysql/base.py`: metadata, identifiers and UTC conversion.
- `backend/mysql/models.py`: full typed relational model and constraints.
- `backend/migrations/versions/20261106_0001_initial_relational_schema.py`:
  immutable initial migration.
- The `20261106_0002` compatibility revision in `backend/migrations/versions/`:
  MySQL 5.7 storage and trigger enforcement.
- `backend/sql/001_initial_schema.sql`: full fresh-database SQL through `0002`.
- `backend/sql/002_mysql57_compatibility.sql`: incremental SQL for a target
  already recorded at `0001`.
- `SCHEMA_REFERENCE.md`: complete generated table/column/reference dictionary.
- `SOURCE_AUDIT.md`: exact source findings, 37-collection inventory and known
  import blockers.
- `IMPLEMENTATION_PLAN.md`: subsequent steps and acceptance criteria.
- `VALIDATION.md`: commands actually run and their limits.

## Run locally

Use a new Python 3.12 virtual environment. Since Step 2, `requirements.txt`
selects the same MySQL runtime as `requirements-mysql.txt`; no MongoDB driver
is required. Install Docker with Compose if using the provided
local database service, or supply an empty database on your existing MySQL
5.7.24-log server. Choose one of the two connection setups below.

From the extracted project root:

```bash
python -m venv .venv-mysql
```

Activate on Windows PowerShell:

```powershell
.\.venv-mysql\Scripts\Activate.ps1
Copy-Item backend/.env.mysql.example backend/.env.mysql
```

Activate on Linux/macOS:

```bash
source .venv-mysql/bin/activate
cp backend/.env.mysql.example backend/.env.mysql
```

Install the standalone foundation:

```bash
python -m pip install -r backend/requirements-mysql.txt
```

### Option A: use your existing MySQL 5.7.24-log server

Edit `backend/.env.mysql` to point to a new empty database on that server. The
port below is the common existing-server port; use its actual configured port.
For a local development connection, the essential settings are:

```dotenv
APP_ENV=development
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DATABASE=meow_eyes
MYSQL_USER=your-migration-user
MYSQL_PASSWORD='set-your-existing-server-password'
MYSQL_SSL_MODE=disabled
```

Use the production TLS settings below for production connections. The database
administrator must grant the migration account the required schema and trigger
privileges. The startup/migration preflight reports incompatible InnoDB
settings without altering them. `MYSQL_ROOT_PASSWORD` is a Compose initialization
variable and is not required to connect to an existing server.

### Option B: use a separate local MySQL 5.7.24 container

The supplied template uses port **3307** for this option. Set different, strong
values for `MYSQL_PASSWORD` and `MYSQL_ROOT_PASSWORD` in `backend/.env.mysql`.
Single-quote passwords so `$` and `#` are not interpreted by Compose. Do not
paste real credentials into the example file or documentation.

```dotenv
APP_ENV=development
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_DATABASE=meow_eyes
MYSQL_USER=meow_migrator
MYSQL_PASSWORD='replace-with-your-local-password'
MYSQL_ROOT_PASSWORD='replace-with-a-different-local-root-password'
MYSQL_SSL_MODE=disabled
```

Start the optional local database:

```bash
docker compose --env-file backend/.env.mysql -f compose.mysql.yml up -d --wait
```

Compose pins image `mysql:5.7.24`, binds only to local `127.0.0.1:3307`, and uses
project `meow-eyes-mysql57` with a new `mysql57_data` volume. It does not reuse or
delete the previous MySQL 8.4 volume. If an earlier local server occupies port
3307, stop that instance without deleting its volume, or choose another free
`MYSQL_PORT` for the new instance.

Never attach a MySQL 8.4 data directory to this 5.7 container. Existing 8.4 data
requires a separately reviewed logical export/import to a fresh 5.7 target.
Compose initialization variables are used only when its volume is first
initialized; editing the env file does not change credentials already stored
inside an existing database.

### Apply the schema and verify its revision

From the project root, apply both revisions to the new empty target database,
then start the independent health application:

```bash
cd backend
python -m alembic upgrade head
python -m alembic current
python -m mysql.check_integrity
python -m uvicorn mysql_bootstrap:app --host 127.0.0.1 --port 8001
```

Check:

- `http://127.0.0.1:8001/api/health/live`: process liveness.
- `http://127.0.0.1:8001/api/health/ready`: 200 only when MySQL is reachable,
  its version and InnoDB configuration are supported, and the installed revision
  equals `20261109_0003` after all current migrations (the original baseline was `20261106_0002`).
  Otherwise returns 503 with a safe reason code.
- `http://127.0.0.1:8001/docs`: health-only OpenAPI documentation.

Both health responses explicitly include `mode: "schema_only"` and
`commerce_routes_enabled: false`. A successful health check is not evidence of
a completed storefront migration.

Run `python -m mysql.check_integrity` using the migration/verifier account with
trigger metadata access. This operator check validates existing data, table
storage format, and the expected 90 validation-trigger definitions. Runtime
readiness deliberately does not inspect trigger metadata, so
the ordinary runtime account does not need the `TRIGGER` privilege. A healthy
HTTP readiness response does not detect a trigger that a privileged operator
has manually removed; use the integrity command after deployments or database
administration changes.

### Update a schema already recorded at `0001`

On a supported MySQL 5.7 target that already has the initial schema and revision
record, run the same `python -m alembic upgrade head` command. Alembic applies
only `20261106_0002`. The compatibility revision checks existing row data before
installing validation triggers, changes the required row format, and leaves the
application tables/data in place. If preflight reports an invalid row, resolve
the reported issue explicitly and rerun; do not stamp the head or suppress the
failure. Its own partially installed trigger set can be resumed without dropping
the application tables.

An actual MySQL 8.4 server is not a supported target of this configuration.
Changing a dependency, Docker tag or Alembic revision does not downgrade that
server. Keep its data intact and use a fresh 5.7 target with a reviewed logical
data migration if such a deployed instance exists.

### Inspect the schema without a MySQL server

From `backend/`:

```bash
python -m alembic upgrade head --sql
```

The provided SQL file is generated by the same command. Use Alembic as the
normal installation path. If a DBA applies the generated SQL directly to a
fresh database, it already includes Alembic's version-table entry; do not add a
second manual version record or reapply the entire script.

The full export contains MySQL-client `DELIMITER` directives around compound
trigger bodies. Use the `mysql` command-line client or a compatible script
runner such as MySQL Workbench. `DELIMITER` is a client directive, so it must
not be sent as server SQL through a generic driver. Online Alembic migration
sends complete trigger statements directly and does not send those directives.

For an existing target already at `0001`, the incremental export is
`backend/sql/002_mysql57_compatibility.sql`; do not apply the full installation
script to that database. Generate it from `backend/` with:

```bash
python -m alembic upgrade 20261106_0001:20261106_0002 --sql
```

**Direct SQL does not run the online migration's existing-row preflight.**
For a populated `0001` schema, pause application writers and scheduled jobs,
then run the preflight command with the target's migration credentials before
applying the incremental SQL:

```bash
python -m mysql.check_integrity --preflight-only
```

Resolve any reported violations first. Keep writers paused through installation
and the full `python -m mysql.check_integrity` verification. Execute the script
with stop-on-error behavior; do not use the MySQL client's `--force` option to
continue after a trigger error. Alembic is the preferred path for online data
preflight and resuming its own partial trigger installation. The full `001`
export is intended only for a fresh empty database.

With a SQL client configured with autocommit disabled, explicitly commit the
final version-table INSERT/UPDATE. DDL may already be persisted independently.

### Run the offline tests

```bash
python -m pip install -r requirements-mysql-test.txt
python -m pytest -c pytest-mysql.ini
```

This command selects only the new foundation tests. Existing `backend/tests`
contains opt-in legacy HTTP/demo tests and is not the MySQL acceptance suite.

### Optional real-MySQL acceptance check

`tests_mysql/test_mysql_integration.py` is skipped by default. To run it,
explicitly create a **new empty disposable database** whose name starts with
`test_meow_`, and grant a test migration account access to that database. Set
`APP_ENV=test`, `MYSQL_INTEGRATION_TESTS=1`, and every connection variable
(`MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`)
in the shell before running:

```bash
python -m pytest -c pytest-mysql.ini -m mysql_integration -v
```

This test refuses a populated target, applies the schema migrations, checks
readiness, UTF-8/Decimal behavior and actual MySQL trigger/FK enforcement, then
rolls back its data fixtures. It leaves the schema installed for inspection;
it never drops the database. Re-running requires another empty test target.
Never set the test variables to a live application database.

## Production configuration policy

Use a separate migration account for DDL and a runtime account with only the
data privileges the application needs. The Compose user is a local migration
account, not a production permission template. Supply production overrides via
deployment environment or secrets, including:

```dotenv
APP_ENV=production
MYSQL_HOST=your-mysql-host
MYSQL_PORT=3306
MYSQL_DATABASE=meow_eyes
MYSQL_USER=your-runtime-user
MYSQL_PASSWORD='set-outside-source-control'
MYSQL_SSL_MODE=verify_identity
MYSQL_SSL_CA=certificates/mysql-ca.pem
```

The driver verifies both the CA and hostname in production. If the service
uses a publicly trusted certificate, the system trust store may be sufficient.
Relative certificate paths resolve against the env file directory. Pool
settings, connect/read/health timeouts and optional mutual-TLS certificates are
documented in `.env.mysql.example`. URL construction handles reserved password
characters without string concatenation.

Connections use UTC, strict SQL mode, `REPEATABLE READ`, connection health checks,
and pool recycling. SQL parameters are hidden from engine error output. The
readiness endpoint returns no SQL text, connection password or driver traceback.

`REPEATABLE READ` matches MySQL 5.7's normal transaction isolation behavior and
avoids requiring a binary-log format change for this foundation. Later stock,
quota and payment services still need explicit row locks and atomic transaction
boundaries; the isolation setting does not implement them on its own.

### Trigger installation and the definer account

The operator audit verifies each guard's table, event, body, stored SQL mode and
execution order. Each validation guard must run last among BEFORE triggers for
its table/event, so a later trigger cannot change a value after validation.
The audit reports `definer_privileges_verified: false`: it does not inspect
privileged account/grant tables or certify that a definer account can execute.
Have the DBA retain and verify that account as described below.

The migration account needs the schema DDL privileges and `TRIGGER` privilege
required to create the validation triggers. It also needs the data/metadata
access used by preflight and the integrity-verification command. Triggers
execute with their definer's privileges; retain that account and its required
`TRIGGER`/table access after installation. Deleting the account or revoking the
privileges it needs can break later inserts and updates even if the runtime
user has normal DML access.

On a server with binary logging enabled, MySQL 5.7 policies can also require
administrator privileges for trigger creation. If the hosting account cannot
create triggers, ask the DBA to perform or authorize the installation under
the existing server policy. This package does not automatically change
`log_bin_trust_function_creators`, grant `SUPER`, or disable binary logging.
The `-log` version suffix alone is not enough to decide whether that policy
applies.

Sources: [MySQL 5.7 CREATE TRIGGER](https://docs.oracle.com/cd/E17952_01/mysql-5.7-en/create-trigger.html)
and [stored-program binary logging](https://docs.oracle.com/cd/E17952_01/mysql-5.7-en/stored-programs-logging.html).

## Data migration procedure for the next approved step

1. Obtain a consistent MongoDB export and copy uploaded files. Record source
   counts and checksums. Record the application's timestamp and currency rules.
2. Run preflight validation: duplicates under the target collation, missing
   references, category cycles, invalid stock, variant ownership, dates,
   numeric precision and order totals. Report issues without silently changing
   business identifiers.
3. Import parents before children with deterministic identity mappings. Preserve
   password/PIN hashes; hash existing session tokens with matching lookup logic.
   Flatten embedded arrays and record source-to-target provenance.
4. Preserve historical order snapshots exactly where present. Keep missing
   lens/prescription data unknown. Review the misleading legacy roulette field
   before mapping it to the spin/redemption relation.
5. Reconcile counts, financial totals, points, reservations, product stock, and
   orphan checks; verify rerunning an import does not duplicate rows.
6. Convert and test all application queries, serializers, scheduled jobs and
   exports against MySQL 5.7.24. Adapt legacy fixtures and seeders explicitly;
   use SQL supported by that version rather than MySQL 8-only CTEs, window
   functions or `SKIP LOCKED`.
7. Rehearse the import and backup restore in staging. At actual cutover, stop
   application writers/jobs for the final consistent snapshot or use a separately
   designed change-capture strategy; avoid untracked dual writes.
8. Switch application traffic only after reconciliation and acceptance. Keep the
   prior snapshot and deployment available for rollback; account for any writes
   accepted after cutover before switching back.

The supplied seed has three duplicate product-SKU pairs. Old order items lose
lens/prescription data, and seeded product rating/sales counters are synthetic.
These are source-derived findings, not a claim about the live database. Their
details and source references are in `SOURCE_AUDIT.md`.

## Rollback limits

MySQL DDL does not turn an entire migration sequence into a reversible data
transaction. If an initial schema deployment fails partway, inspect it and
recreate only the disposable empty target before retrying; do not stamp the
revision as successful. After real data is imported, use a verified backup and
the reviewed cutover procedure. A schema downgrade drops tables and is not a
data-recovery mechanism.

Removing compatibility triggers would remove the corresponding row-rule
enforcement on MySQL 5.7. Do not treat a successful application response as
evidence that a deliberately downgraded schema is safe for writes. Use the
reviewed backup/restore process for data recovery.

## Primary technical references

- [SQLAlchemy asynchronous sessions](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [SQLAlchemy MySQL and asyncmy dialect](https://docs.sqlalchemy.org/en/20/dialects/mysql.html)
- [Alembic offline SQL generation](https://alembic.sqlalchemy.org/en/latest/offline.html)
- [MySQL 5.7 CREATE TABLE and CHECK behavior](https://docs.oracle.com/cd/E17952_01/mysql-5.7-en/create-table.html)
- [MySQL 5.7 CREATE TRIGGER](https://docs.oracle.com/cd/E17952_01/mysql-5.7-en/create-trigger.html)
- [MySQL 5.7 generated columns](https://docs.oracle.com/cd/E17952_01/mysql-5.7-en/create-table-generated-columns.html)
- [MySQL 5.7 JSON](https://docs.oracle.com/cd/E17952_01/mysql-5.7-en/json.html)
- [MySQL 5.7 InnoDB row formats](https://docs.oracle.com/cd/E17952_01/mysql-5.7-en/innodb-row-format.html)
- [MySQL 5.7 stored-program binary logging](https://docs.oracle.com/cd/E17952_01/mysql-5.7-en/stored-programs-logging.html)

These references establish the underlying database/driver behavior. The schema
and application decisions above are specific to this source audit.
