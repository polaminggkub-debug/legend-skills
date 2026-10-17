"""Extract a .NET single-file bundle (apphost) into a new directory.

Usage: python3 -I unbundle.py <bundle.exe> <new-out-dir>
"""
import os
import struct
import sys
import zlib

SIG = bytes([0x8b, 0x12, 0x02, 0xb9, 0x6a, 0x61, 0x20, 0x38, 0x72, 0x7b, 0x93, 0x02, 0x14, 0xd7,
             0xa0, 0x32, 0x13, 0xf5, 0xb9, 0xe6, 0xef, 0xae, 0x33, 0x18, 0xee, 0x3b, 0x2d, 0xce,
             0x24, 0xb3, 0x6a, 0xae])


def read_str(b, p):
    n, shift = 0, 0
    while True:
        c = b[p]; p += 1
        n |= (c & 0x7f) << shift; shift += 7
        if not c & 0x80:
            break
    return b[p:p + n].decode('utf-8'), p + n


def main(src, out):
    data = open(src, 'rb').read()
    i = data.find(SIG)
    if i < 8:
        sys.exit('bundle signature not found')
    hdr = struct.unpack_from('<q', data, i - 8)[0]
    major, minor, count = struct.unpack_from('<IIi', data, hdr)
    bundle_id, p = read_str(data, hdr + 12)
    if major >= 2:
        p += 8 * 4 + 8  # deps.json + runtimeconfig offsets/sizes, flags
    print(f'bundle v{major}.{minor} files={count} id={bundle_id}')
    os.makedirs(out)
    for _ in range(count):
        off, size = struct.unpack_from('<qq', data, p); p += 16
        csize = 0
        if major >= 6:
            csize = struct.unpack_from('<q', data, p)[0]; p += 8
        kind = data[p]; p += 1
        name, p = read_str(data, p)
        blob = data[off:off + (csize or size)]
        if csize:
            blob = zlib.decompress(blob, -15)
        dest = os.path.realpath(os.path.join(out, name))
        if not dest.startswith(os.path.realpath(out) + os.sep):
            sys.exit(f'unsafe path {name}')
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, 'wb').write(blob)
        print(f'{kind}\t{size}\t{name}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
