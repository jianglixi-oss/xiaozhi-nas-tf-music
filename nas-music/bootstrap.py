"""Runtime bootstrap for fnOS container API deployments using the stock Python image.

Application/music mounts are read-only; only /deps is writable. No Docker socket,
SSH account or privileged container is needed.
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

requirements = Path('/app/requirements.txt')
marker = Path('/deps/.requirements-sha256')
digest = hashlib.sha256(requirements.read_bytes()).hexdigest()
if not marker.exists() or marker.read_text().strip() != digest:
    print('Installing music MCP dependencies into /deps', flush=True)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-cache-dir',
                    '--disable-pip-version-check', '--no-warn-script-location',
                    '--timeout', '20', '--retries', '2', '--index-url',
                    os.environ.get('PIP_INDEX_URL', 'https://pypi.tuna.tsinghua.edu.cn/simple'),
                    '--upgrade', '--target', '/deps', '-r', str(requirements)], check=True)
    marker.write_text(digest)
os.chdir('/app')
os.execv(sys.executable, [sys.executable, '/app/mcp_pipe.py', '/app/server.py'])
