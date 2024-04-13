import sys, os
from pathlib import Path

scriptsFolder = Path(sys.argv[1])
if scriptsFolder.is_dir():
    os.startfile(scriptsFolder)