"""Development-only SQL demo seed. Run: python seed.py --demo.

Requires APP_ENV=development/test and explicit demo password/PIN environment
variables. No MongoDB dependency, automatic seeding or production writes.
"""
from mysql.demo_seed import main

if __name__ == "__main__":
    raise SystemExit(main())
