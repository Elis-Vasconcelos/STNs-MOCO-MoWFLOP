"""zipcheck.py ZIP DIR_PARENT: every regular file under the zip's top folder(s) in DIR_PARENT matches the zip by CRC and size, and nothing extra on disk."""
import sys, zipfile, zlib, os
from pathlib import Path
zp, parent = sys.argv[1], Path(sys.argv[2])
z = zipfile.ZipFile(zp)
entries = {i.filename: i for i in z.infolist() if not i.is_dir()}
tops = {n.split('/')[0] for n in entries}
disk = {str(p.relative_to(parent)) for t in tops for p in (parent / t).rglob('*') if p.is_file()}
bad = 0
for name, info in entries.items():
    p = parent / name
    if not p.is_file() or p.stat().st_size != info.file_size:
        bad += 1; continue
    crc = 0
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            crc = zlib.crc32(chunk, crc)
    bad += crc != info.CRC
extra = disk - set(entries)
print(f"{os.path.basename(zp)}: zip files={len(entries)} disk files={len(disk)} mismatched={bad} on_disk_not_in_zip={len(extra)} -> {'IDENTICAL' if bad == 0 and not extra else 'DIFFERENT'}")
