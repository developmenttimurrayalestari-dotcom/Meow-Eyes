"""Development-only SQL CMS fixture seed: python seed_content.py --demo.

The main seed.py already includes content. This command requires empty CMS
tables and never replaces existing content.
"""
from mysql.demo_seed import main

if __name__ == "__main__":
    raise SystemExit(main(content_only=True))
