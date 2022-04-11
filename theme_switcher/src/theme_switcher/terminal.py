from configparser import ConfigParser
import fire
import io
import subprocess
from typing import Any, Optional, Union
import yaml

import theme_switcher.config

PROFILE_ID_CONFIG_KEY = 'terminal.active_profile_id'

PROFILES_DCONF_KEY = r'/org/gnome/terminal/legacy/profiles:/'

PROFILE_ROOT_KEY = '/'

ACTIVE_NAME = 'active'

ConfigTypes = Union[bool, float, int]


def get_profiles() -> dict[dict]:
    dconf_out = subprocess.check_output(['dconf', 'dump', PROFILES_DCONF_KEY])

    buffer = io.StringIO(dconf_out.decode())
    config = ConfigParser()
    config.read_file(buffer)

    profile_list = yaml.safe_load(config['/']['list'])
    config_dict = dict(
        (pid, dict(config[f':{pid}'])) for pid in profile_list if f':{pid}' in config)

    return config_dict


def _get_dconf_profile_config(profile_id: str) -> ConfigParser:

    profile_key = f'{PROFILES_DCONF_KEY}:{profile_id}/'

    dconf_out = subprocess.check_output(['dconf', 'dump', profile_key])

    buffer = io.StringIO(dconf_out.decode())
    config = ConfigParser()
    config.read_file(buffer)


    return config


def _set_dconf_value(profile_id: str, key: str, value: ConfigTypes) -> None:
    dconf_key = f'{PROFILES_DCONF_KEY}:{profile_id}/{key}'

    if isinstance(value, str) and not (
            all(char == "'" for char in [value[0], value[-1]]) or
            (value[0] == '[' and value[-1] == ']')
            ):
        value = f"'{value}'"
    else:
        value = str(value)
    subprocess.check_call(['dconf', 'write', dconf_key, value])


def patch_console_profile(
        new_name: Optional[str] = ACTIVE_NAME,
        profile_id: Optional[str] = None,
        source_profile_id: Optional[str] = None,
        patch: Optional[dict[str, ConfigTypes]] = None) -> None:

    if profile_id is None:
        profile_id = theme_switcher.config.get(PROFILE_ID_CONFIG_KEY)

    config = _get_dconf_profile_config(profile_id)
    if source_profile_id is not None:
        patch_config = _get_dconf_profile_config(source_profile_id)
        for key, value in patch_config[PROFILE_ROOT_KEY].items():
            if key == 'visible-name':
                # gonna set this later
                continue
            _set_dconf_value(profile_id, key, value)
    if patch:
        for key, value in patch.items():
            _set_dconf_value(profile_id, key, value)


if __name__ == '__main__':
    # for testings

    fire.Fire(get_profiles)
