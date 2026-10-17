"""Fail CI if user-specific deployment files or credential values are tracked."""
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
errors = []
for name in filter(None, paths):
    p = Path(name)
    if p.name == '.env' or name == 'nas-music/DEPLOYED.md' or name.startswith('nas-music/deps/'):
        errors.append(name + ': private deployment file')
    data = (root / name).read_bytes()
    if re.search(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)', data):
        errors.append(name + ': possible credential')
    for value in re.findall(rb'wss://[^\s<>"\x27]+[?&]token=([^\s<>"\x27]+)', data):
        if value != b'REPLACE_ME':
            errors.append(name + ': non-placeholder MCP token')
if errors:
    raise SystemExit('\n'.join(errors))
print('Publication checks passed')
