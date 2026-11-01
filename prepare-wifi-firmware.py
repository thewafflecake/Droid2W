from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parent
repo = root / 'research/rpi-wifi-firmware'
revision = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
assert revision == 'c91cd2804cf7463aab913e7247c176049f16bbd6'
source = repo / 'debian/config/brcm80211'
target = root / 'aosp/device/experimental/zero2w/firmware/brcm'
target.mkdir(parents=True, exist_ok=True)
for path in (source / 'brcm').glob('brcmfmac43436*'):
    if 'compute-module' in path.name:
        continue
    resolved = path.resolve()
    assert resolved.is_relative_to(repo.resolve())
    assert resolved.is_file(), path
    shutil.copyfile(resolved, target / path.name)
shutil.copyfile(repo / 'debian/copyright', target.parent / 'copyright')
(target.parent / 'source-revision.txt').write_text(revision + '\n')
print('Copied pinned Raspberry Pi Wi-Fi firmware and license information.')
