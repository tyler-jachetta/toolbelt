# argparse is used for typing.
from argparse import Namespace
from fire import Fire
import os
from pathlib import Path
from typing import Any, Optional, Union
import yaml

LOCAL_CONFIG = Path('.theme_switcher').absolute()
USER_CONFIG = Path('~/.theme_switcher').expanduser()
GLOBAL_CONFIG = Path('/etc/theme_switcher/config.yml')

CONFIG_FILES = [
    LOCAL_CONFIG, USER_CONFIG, GLOBAL_CONFIG
]


class NoValue(Exception):
    pass


"""
Config hierarchy:
    - cmdline args
    - environment variables
    - configuration files
    - caller provided defaults (wrapped or with functools, not directly provided here)
    - built in defaults

Any level[s] of this hierarchy may be absent for a given value, KeyError will
be raised when no value can be found. This means that, for example, not every
value need have a built in default.
"""


def get(key: str, default: Optional[Any] = NoValue, parsed_args: Optional[Namespace] = None) -> Any:
    if parsed_args is not None:
        # This one's simple enough I'm not wrapping it in its own function.
        try:
            return getattr(parsed_args, key)
        except AttributeError:
            # not in parsed args
            pass

    try:
        return _get_env(key)
    except NoValue:
        pass

    try:
        return get_from_config_files(key)
    except NoValue:
        pass

    if default is not NoValue:
        try:
            raise default
        except TypeError:
            return default

    raise NoValue()


def get_from_config_files(key):

    for conf_file in CONFIG_FILES:
        # TODO: probably should wrap this, but eh?
        try:
            return _get_from_conf_file(key, conf_file)
        except NoValue:
            pass

    raise NoValue


def _get_from_conf_file(key, conf_file):
    try:
        conf = yaml.safe_load(conf_file.read_text())
    except FileNotFoundError:
        raise NoValue

    keys = key.split('.')

    for this_key in keys[:-1]:
        conf = conf.setdefault(this_key, {})

    try:
        return conf[keys[-1]]
    except KeyError:
        raise NoValue


def _set_config(key: str, value: Any, path: Path) -> bool:

    try:
        conf = yaml.safe_load(path.read_text()) or {}
    except FileNotFoundError:
        conf = {}
    conf_root = conf

    keys = key.split('.')

    for this_key in keys[:-1]:
        conf = conf.setdefault(this_key, {})

    if keys[-1] in conf and conf[keys[-1]] == value:
        return False

    conf[keys[-1]] = value
    with path.open('w') as fh:
        yaml.safe_dump(conf_root, fh)

    return True


def set_local(key: str, value: Any) -> bool:

    return _set_config(key, value, LOCAL_CONFIG)


def set_user(key: str, value: Any) -> bool:

    return _set_config(key, value, USER_CONFIG)


def _get_env(key) -> str:
    for key_option in [key, key.upper(), key.lower()]:
        try:
            return os.environ[key_option]
        except KeyError:
            pass

    raise NoValue


# Testing
if __name__ == '__main__':
    #Fire(set_user)
    Fire(get)
