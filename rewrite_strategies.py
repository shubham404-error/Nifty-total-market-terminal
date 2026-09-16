with open("pages/strategies.py", "r", encoding="utf-8") as f:
    content = f.read()

import re

# We will just write a new strategies.py that only has pullback_page, using the logic from the old file.