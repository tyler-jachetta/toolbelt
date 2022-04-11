#!/usr/bin/env python3

import argparse
import collections
import logging
import pathlib
import yaml

import re

logger = logging.getLogger(__name__)
_handler = logging.StreamHandler()
logger.addHandler(_handler)

VTC_EXT = '.vtc'
TAVERN_EXT = '.tavern.yaml'

# GMXS
TEST_RE_STR = r'^\s*varnishtest\s*"(?P<test_name>.*?)"\n(?P<test_content>.*)$'

# GMXS
CLIENT_RE_STR = r'^(?:#(?P<above_comment>[^\n]*)\n)?client\s(?P<client_name>\S*?)\s*{\s*(?:#\s*(?P<below_comment>.*?)$)?(?P<body>.*?)^}\s*(?:-run)?'
# GMX
CASE_RE_STR = r'txreq\s+-req\s+"(?P<method>[A-Z]+)"\s+-url\s+"(?P<url>[/a-z-A-Z_0-9\.]+)"(?P<headers>(?:\s*\\\n\s*-hdr\s*".*?")*)\s*rxresp\s*\n(?P<response>(?:^\s*expect.*?$)*)\s*\Z'
#CASE_RE_STR = r'txreq\s.*?
TX_RE_STR = r'txreq\s+-req\s+(")?(?P<method>[A-Z]+"?)(?(1)\1)\s+-url\s+(")?(?P<url>[/a-z-A-Z_0-9\.]+)(?(3)\3)'

# GM
HEADER_RE_STR = r'-hdr\s*"(?P<key>.*?):\s*(?P<val>.*?)"(:?\s*\\)?$'

EXPECTATION_RE_STR = r'^\s*expect resp\.(?P<param>[a-z]+)\s*(?P<operator>[=!><]{2})\s*(?P<value>.*?)\s*$'

TEST_RE = re.compile(TEST_RE_STR, re.M | re.X | re.S)
CLIENT_RE = re.compile(CLIENT_RE_STR, re.M | re.S)
CASE_RE = re.compile(CASE_RE_STR, re.M | re.S)
HEADER_RE = re.compile(HEADER_RE_STR, re.M)
EXPECTATION_RE = re.compile(EXPECTATION_RE_STR, re.M)
TX_RE = re.compile(TX_RE_STR)

CURLY_BRACKET_ESC_RES = [
    ('{{', re.compile(r'(?<!\{)\{(?!\{)')),
    ('}}', re.compile(r'(?<!\})\}(?!\})'))]

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


ResponseExpectation = collections.namedtuple('ResponseExpectation', ['param', 'operator', 'value'])
Request = collections.namedtuple('Request', ['url', 'method', 'headers'])
Stage = collections.namedtuple('Stage', ['name', 'request', 'response'])


def represent(dumper, data):
    return dumper.represent_dict(data._asdict())


yaml.SafeDumper.add_representer(ResponseExpectation, represent)
yaml.SafeDumper.add_representer(Request, represent)
yaml.SafeDumper.add_representer(Stage, represent)


def _convert_header(key, val):
    """
    Handles edge cases
    """

    val = val.lstrip()

    if key == "X-IXSource-SourceID" and val == LOTSA_ZEROS:
        return (key, '{source_id:s}')

    elif key == "X-IXSource-AccountID" and val == LOTSA_ZEROS:
        return (key, '{account_id:s}')

    if '{' in val:
        print("FOUND IT")

    for replacement, esc_re in CURLY_BRACKET_ESC_RES:
        match = esc_re.search(val)
        if match is None:
            continue

        val = esc_re.sub(replacement, val)

    return key, val


def _join_split_lines(in_text):
    return in_text.replace('\\\n', '')


def _string_stripped(inval):
    outval = str(inval)
    if len(outval) > 1 and outval[-1] == outval[0] and outval[0] in ['"', "'"]:
        outval = outval[1:-1]
    return outval


def _convert_response(response_vtc):
    response = {}
    # TODO const
    param_mutations = {
        'status': ('status_code', int),
        'body': (('json', 'body'), _string_stripped)
    }
    for expectation_match in re.finditer(EXPECTATION_RE, response_vtc):
        expectation = ResponseExpectation(**expectation_match.groupdict())
        if expectation.param in param_mutations:
            param_name, val_type = param_mutations[expectation.param]
            if param_name is not None:
                param = param_name
            else:
                param = expectation.param

            if val_type is not None:
                value = val_type(expectation.value)
            else:
                value = expectation.value
        else:
            param = expectation.param
            value = expectation.value

        assert param not in response
        if not isinstance(param, str):
            rdict = response
            keys, last_key = param[:-1], param[-1]
            for key in keys:
                rdict = rdict.setdefault(key, {})
            rdict[last_key] = value
        else:
            response[param] = value

        if not expectation.operator == '==':
            raise ValueError(f'operator {expectation.operator} is not handled (yet?)')

    return response


def _convert_request(case_match):
    """
    Args:
        * case_match (`re.match`)
    """

    req = Request(
        url=f'{{protocol:s}}://{{deployed_domain:s}}:{{port:s}}{case_match.groupdict()["url"]}',
        method=case_match.groupdict()['method'],
        headers=dict(_convert_header(**match.groupdict()) for match in HEADER_RE.finditer(case_match.groupdict()['headers'])),
    )

    return req


def convert_vtc_to_tavern(source, dest):
    """
    test_name: "Get webproxy assets - basic auth"

stages:
  - name: "test auth"
    request:
      url: "{protocol:s}://{deployed_domain:s}/basic-auth/testusername/testpassword"
      method: GET
      headers:
        "Host": "httpbin.imgix.com"
        "X-Forwarded-Proto": "http"
        "Authorization": "Basic dGVzdHVzZXJuYW1lOnRlc3RwYXNzd29yZA=="
        "X-IXSource-SourceID": "{source_id:s}"
        "X-IXSource-Epoch": "0"
        "X-IXSource-AccountID": "{account_id:s}"
        "X-Imgix-Purge-ID": "0"
        "X-IXSource-Cache-Behavior": "default"
        "X-IXSource-Cache-Value": "60"
        "X-IXSource-Type": "webproxy"
        "X-IXSource-WF-Prefix-JSON": "{{\"path\": \"\",\"host\": \"httpbin.imgix.com\",\"scheme\": \"{protocol:s}\",\"port\": \"\",\"auth\": \"testusername:testpassword\"}}"
    response:
      status_code: 200

    """

    source_content = source.read_text()

    test_match = TEST_RE.match(source_content)

    assert test_match is not None
    test_name = test_match.groupdict()['test_name']

    test_content = test_match.groupdict()['test_content']

    # 'stages' is the tavern term for this. roughly, stage == case
    stages = []

    # dict to dump to yaml
    test_definition = {'test_name': test_name, 'stages': stages}

    # parse individual cases
    for client in CLIENT_RE.finditer(test_content):
        this_iter = 0
        client_case_name = None
        gd = client.groupdict()
        # the comments fight it out
        if gd.get('above_comment') and gd.get('below_comment'):
            import pdb
            pdb.set_trace()
            raise ValueError("I'm just not built for this")
        elif gd.get('above_comment') or gd.get('below_comment'):
            client_case_name = gd.get('below_comment', gd.get('above_comment'))
        else:
            client_case_name = f'{test_name}-{client.groupdict()["client_name"]}'

        if not CASE_RE.search(client.groupdict()['body']):
            import pdb
            pdb.set_trace()
        for case in CASE_RE.finditer(client.groupdict()['body']):
            case_name = client_case_name
            if this_iter:
                case_name = f'{case_name}-{this_iter}'

            request = _convert_request(case)
            response = _convert_response(case.groupdict()['response'])

            stages.append(Stage(name=case_name, request=request, response=response))
            this_iter += 1
    if not stages:
        import pdb
        pdb.set_trace()
    with dest.open('w') as dest_fh:
        yaml.safe_dump(test_definition, dest_fh, sort_keys=False)


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

        for source in sources:
            dest_file = dest.joinpath(source.stem).with_suffix(TAVERN_EXT)
            logger.debug(f'converting file {source} to {dest_file}')
            convert_vtc_to_tavern(source, dest_file)

    else:
        logger.debug(f'converting single file {source} to {dest}')
        assert source.is_file()
        if dest.is_dir():
            dest = dest.joinpath(source.stem).with_suffix(TAVERN_EXT)

        logger.debug(f"Source and dest:\n\t{source}\n\t{dest}")
        convert_vtc_to_tavern(source, dest)


class UnhandledExpectation(Exception):
    pass


if __name__ == '__main__':
    main()
