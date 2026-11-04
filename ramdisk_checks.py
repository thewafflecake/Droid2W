"""Validate KitKat init inputs without printing keys or property values."""
import gzip
import re
import stat
from pathlib import Path


def validate_init_files(files):
    for name, (mode, uid, gid, data) in files.items():
        if not name.endswith('.rc'):
            continue
        assert stat.S_ISREG(mode), (name, 'init input must be a regular file')
        assert uid == 0 and not mode & 0o022, (name, oct(mode), uid, gid)
        assert b'\r' not in data, (name, 'CRLF in init input')
        for service in re.findall(rb'^service[ \t]+(\S+)', data, re.M):
            # system/core/init/init_parser.c valid_name() in Android 4.4.4.
            assert 1 <= len(service) <= 16, (name, 'service name exceeds 16 bytes', service)
            assert re.fullmatch(rb'[A-Za-z0-9_-]+', service), (name, 'invalid service name', service)


def read_ramdisk(path):
    archive = gzip.decompress(Path(path).read_bytes())
    files = {}
    pos = 0
    while pos + 110 <= len(archive):
        assert archive[pos:pos+6] in (b'070701', b'070702'), 'Invalid newc header'
        fields = [int(archive[pos+6+i*8:pos+14+i*8], 16) for i in range(13)]
        size, namesize = fields[6], fields[11]
        pos += 110
        assert namesize >= 1 and pos + namesize <= len(archive)
        assert archive[pos+namesize-1] == 0
        name = archive[pos:pos+namesize-1].decode().removeprefix('./')
        pos = (pos+namesize+3)&~3
        assert pos+size <= len(archive)
        data = archive[pos:pos+size]
        pos = (pos+size+3)&~3
        if name == 'TRAILER!!!':
            return files
        assert name not in files, ('Duplicate archive path', name)
        files[name] = (fields[1], fields[2], fields[3], data)
    raise AssertionError('Missing newc trailer')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ramdisk', type=Path)
    args = parser.parse_args()
    validate_init_files(read_ramdisk(args.ramdisk))
    print('PASS: init file ownership, modes, line endings and KitKat service names')
