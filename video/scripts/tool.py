#!/usr/bin/env python3
"""Use the repo's available Node/npm without requiring shell PATH changes."""
import argparse
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from web_tool import npm_command
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('command',choices=['install','studio','typecheck','render:preview','render:clips','render:final','render:submission'])
args=parser.parse_args()
command=npm_command()+(['ci','--no-audit','--no-fund'] if args.command=='install' else ['run',args.command])
raise SystemExit(subprocess.call(command,cwd=ROOT/'video'))
