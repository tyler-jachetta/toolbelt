"""
Switch themes in sublime text and merge
"""

import fire
import pathlib
import subprocess
from zipfile import ZipFile

THEME_EXT = '.tmTheme'
USER_CONFIG_DIR = pathlib.Path().home().joinpath('.config', 'sublime-text-3')
USER_SETTINGS_PATH = USER_CONFIG_DIR.joinpath('Preferences.sublime-settings')


def set_theme(name):
    subprocess.check_call(['subl', '--command', '-b', f'select_color_scheme {{"name": "{name}"}}'])


def get_themes() -> set[str]:
    package_path = USER_CONFIG_DIR.joinpath('Installed Packages')
    themes = set()
    for package in package_path.glob('*.sublime-package'):
        zf = ZipFile(package)
        themes.update(name for name in zf.namelist() if name.endswith(THEME_EXT))

    return themes


if __name__ == '__main__':
    # testingz
    fire.Fire(get_themes)
