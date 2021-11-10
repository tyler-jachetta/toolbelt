#!/usr/bin/env python3

import argparse
import logging
import pathlib
import sys

import re

logger = logging.getLogger(__name__)
_handler = logging.StreamHandler()
logger.addHandler(_handler)

VTC_EXT = '.vtc'
TAVERN_EXT = '.tavern.yaml'

# GMXS
CLIENT_RE_STR = r'\s*varnishtest\s*"(?P<test_name>.*)"\s*\n\s*.*(?P<client>client\s\S*\s*{.*}\s*-run)'
# GMX
CASE_RE_STR = r'txreq\s+-req\s+(?P<method>[A-Z]+)\s+-url\s+(?P<url>[/a-z-A-Z_0-9\.]+)(?P<headers>(?:\s*\\\n\s*-hdr\s*".*?")*)\s*rxresp\s*\n(?P<response>(?:^\s*expect.*\n)*)'
HEADER_RE_STR = r'-hdr\s*"(?P<key>.*):\s*(:?<val>.*)"(:?\s*\\)?$'

CLIENT_RE = re.compile(CLIENT_RE_STR, re.M | re.X | re.S)
CASE_RE = re.compile(CASE_RE_STR, re.M | re.S)
HEADER_RE = re.compile(HEADER_RE_STR)

# for yaml keys
STAGES = 'stages'
NAME = 'name'
REQUEST = 'request'
URL = 'url'
METHOD = 'method'
HEADERS = 'headers'
RESPONSE = 'response'
STATUS_CODE = 'status_code'

LOTSA_ZEROS = "000000000000000000000000"


def _convert_header(key, val):
    """
    Handles edge cases
    """

    val = val.lstrip()

    if key == "X-IXSource-SourceID" and val == LOTSA_ZEROS:
        return (key, '{source_id:s}')

    elif key == "X-IXSource-AccountID" and val == LOTSA_ZEROS:
        return (key, '{account_id:s}')

    return key, val


def convert_vtc_to_tavern(source, dest):
    test_definition = {}
    source_content = source.read_text()

    client_match = CLIENT_RE.match(source_content)

    assert client_match is not None

    test_name = client_match.groupdict()['test_name']
    client_content = client_match.groupdict()['client']

    logger.debug('\nin convert_vtc_to_tavern:\n')
    logger.debug(test_name)
    logger.debug('\n')
    logger.debug(client_content)
    logger.debug('\n\n')

    # parse individual cases

    for match in CASE_RE.finditer(client_content):
        method = match.groupdict()['method']
        url_path = match.groupdict()['url']
        headers = match.groupdict()['headers']
        response = match.groupdict()['response']

        # Get headers for match

        for header_match in HEADER_RE.finditer(headers):
            header_dict = header_match.groupdict()
            key, val = _convert_header(header_dict['key'], header_dict['val'])




def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('source', type=pathlib.Path)
    parser.add_argument('dest', type=pathlib.Path, nargs='?')
    parser.add_argument('-r', '--recursive', action='store_true')
    parser.add_argument('--debug', action='store_true')

    args = parser.parse_args()

    if args.debug:
        _handler.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    source = args.source
    dest = args.dest or args.source
    sources = []

    if not source.exists():
        parser.error(f'`{source}` does not exist!')

    elif source.is_dir():
        logger.debug('converting from source dir')
        if not dest.is_dir():
            parser.error(f'if the source ({source}) is a directory, the dest ({dest}) must be, too. It is not!')
        # These get us an iterator, but that's okay
        if args.recursive:
            sources = source.rglob('*' + VTC_EXT)
        else:
            sources = source.glob('*' + VTC_EXT)
        logger.debug(f"sources is:\n{list(sources)}")
        for source in sources:
            dest_file = dest.joinpath(source.stem)

    else:
        logger.debug(f'attempting to convert single file {source} to {dest}')
        assert source.is_file()
        if dest.is_dir():
            dest = dest.joinpath(source.stem).with_suffix(TAVERN_EXT)

        logger.debug(f"Source and dest:\n\t{source}\n\t{dest}")
        convert_vtc_to_tavern(source, dest)
        sys.exit(1)


if __name__ == '__main__':
    main()
