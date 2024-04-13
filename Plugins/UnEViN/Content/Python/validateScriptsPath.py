import sys
from pathlib import Path

unevinScriptsFolderPath = Path(sys.argv[1])
if not unevinScriptsFolderPath.is_dir() and not unevinScriptsFolderPath.is_file():
    unevinScriptsFolderPath.mkdir()