import os
from pathlib import Path

import django
import pdoc

MODULE_NAMES = [
    "accounts", "patients", "dashboard"
]
OUTPUT_DIR_NAME = "docs"

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    django.setup()

    module_paths = [Path("./" + name) for name in MODULE_NAMES]
    output_dir = Path("./" + OUTPUT_DIR_NAME)

    pdoc.render.configure(
        logo="https://lyprox.org/static/logo.svg",
        logo_link="https://lyprox.org"
    )
    pdoc.pdoc(*module_paths, output_directory=output_dir)
