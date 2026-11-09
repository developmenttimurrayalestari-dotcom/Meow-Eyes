"""MySQL 5.7 DDL policy shared by models and Alembic.

5.7 does not enforce CHECK constraints and does not accept the named CHECK
syntax generated for MySQL 8. Keep the predicates in metadata for portable
tests/documentation; revision 0002 installs their actual MySQL validation
triggers. Production schema creation must use Alembic, never create_all().
"""
from sqlalchemy import CheckConstraint, Text, JSON, LargeBinary
from sqlalchemy.exc import CompileError
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import CreateTable, CreateColumn


@compiles(CheckConstraint, "mysql")
def omit_native_check(constraint, compiler, **kwargs):
    return None


@compiles(CreateColumn, "mysql")
def compile_mysql57_column(element, compiler, **kwargs):
    column = element.element
    if column.server_default is not None and isinstance(column.type, (Text, JSON, LargeBinary)):
        # The immutable 0001 snapshot contains the original MySQL8 TEXT default.
        # Preserve its history while emitting legal 5.7 DDL on a fresh replay.
        # The current ORM supplies this empty note as a Python scalar default.
        if (column.table is not None and column.table.name == "point_logs"
                and column.name == "note" and str(column.server_default.arg) == "('')"):
            compatible_column = column._copy()
            compatible_column.server_default = None
            return compiler.visit_create_column(CreateColumn(compatible_column), **kwargs)
        # Never silently erase an unrelated column's intended default semantics.
        raise CompileError("MySQL 5.7 forbids TEXT/BLOB/JSON defaults; supply values in application code")
    return compiler.visit_create_column(element, **kwargs)


@compiles(CreateTable, "mysql")
def compile_mysql57_table(element, compiler, **kwargs):
    # The already-delivered 0001 revision has no ROW_FORMAT option. Apply the
    # target policy without rewriting that immutable migration's source.
    row_format = element.element.dialect_options["mysql"].get("row_format")
    if row_format and str(row_format).upper() != "DYNAMIC":
        raise CompileError("This MySQL 5.7 schema requires ROW_FORMAT=DYNAMIC")
    rendered = compiler.visit_create_table(element, **kwargs)
    if not row_format:
        rendered = rendered.rstrip() + " ROW_FORMAT=DYNAMIC\n\n"
    return rendered
