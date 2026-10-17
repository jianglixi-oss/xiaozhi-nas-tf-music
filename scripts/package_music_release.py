"""Package v0.1.0 from an already built board ZIP, with an explicit NAS allowlist."""
import hashlib
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
out = root / 'releases'
firmware = out / 'v2.5.2_waveshare-esp32-s3-audio-board-music.zip'
fw_out = out / 'xiaozhi-nas-tf-music-v0.1.0-waveshare-jd9853.zip'
nas_out = out / 'xiaozhi-nas-tf-music-v0.1.0-nas.zip'
notices = ['LICENSE', 'THIRD_PARTY_NOTICES.md', 'README.md', 'MUSIC_SETUP.md', 'RELEASE_NOTES.md']
with zipfile.ZipFile(firmware) as src, zipfile.ZipFile(fw_out, 'w', zipfile.ZIP_DEFLATED) as dst:
    assert src.testzip() is None
    assert 'merged-binary.bin' in src.namelist()
    for name in src.namelist():
        dst.writestr(name, src.read(name))
    for name in notices:
        dst.write(root / name, name)
files = ['.env.example', 'Dockerfile', 'compose.yaml', 'bootstrap.py', 'library.py',
         'server.py', 'mcp_pipe.py', 'requirements.txt', 'README.md',
         'test_library.py', 'test_mcp_integration.py']
with zipfile.ZipFile(nas_out, 'w', zipfile.ZIP_DEFLATED) as dst:
    for name in files:
        dst.write(root / 'nas-music' / name, 'nas-music/' + name)
    for name in notices:
        dst.write(root / name, name)
lines = []
for path in [fw_out, nas_out]:
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
    lines.append(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name)
(out / 'SHA256SUMS.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('Packaged and verified firmware/NAS ZIPs; wrote SHA256SUMS.txt')
