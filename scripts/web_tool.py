"""Locate Node/npm for local dev. Standard Node installs work without fallbacks."""
from pathlib import Path
import os
import shutil

ROOT=Path(__file__).resolve().parents[1]

def npm_command():
    node=shutil.which('node')
    if not node:
        # Optional fallback for this workstation's installed Playwright runtime.
        try:
            import playwright
            candidate=Path(playwright.__file__).parent/'driver/node'
            if candidate.is_file():
                node=str(candidate)
        except ImportError:
            pass
    if not node:
        raise RuntimeError('Install Node.js 20.19+ (or 22.12+) and npm before running the web app.')
    os.environ['PATH']=str(Path(node).parent)+os.pathsep+os.environ.get('PATH','')
    npm=shutil.which('npm')
    if npm:
        return [npm]
    cached=ROOT/'cache/tools/npm/package/bin/npm-cli.js'
    if cached.is_file():
        return [node,str(cached)]
    raise RuntimeError('npm is missing. Install a standard Node.js distribution with npm.')
