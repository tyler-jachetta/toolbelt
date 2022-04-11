#!/usr/bin/env python3

import argparse
import pathlib
import re


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=pathlib.Path)
    parser.add_argument('dest', type=pathlib.Path)
    parser.add_argument('needs_server_dest', type=pathlib.Path, nargs='?')

    args = parser.parse_args()

    if args.needs_server_dest is None: args.needs_server_dest = args.dest

    for vtc_path in args.source.glob('*.vtc'):
        vtc_content = vtc_path.read_text()
        tav_content = '# ' + '\n# '.join(vtc_content.splitlines())
        if re.findall(r'^\s*server\s+\w+.*{', vtc_content, re.MULTILINE):
            dest = args.needs_server_dest
        elif 'server' in vtc_content:
            import pdb
            pdb.set_trace()
        else:
            dest = args.dest
        tav_path = dest.joinpath(vtc_path.with_suffix('.tavern.yaml.pre').name)

        if tav_path.exists():
            continue
        if not dest.exists():
            dest.mkdir()
        tav_path.write_text(tav_content)


if __name__ == '__main__':
    main()
