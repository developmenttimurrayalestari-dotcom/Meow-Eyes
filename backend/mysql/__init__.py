"""MySQL foundation for the staged Meow Eyes database migration.

This package never imports the legacy MongoDB client. Database connections are
created explicitly by the migration CLI or the schema-only FastAPI entry point.
"""
