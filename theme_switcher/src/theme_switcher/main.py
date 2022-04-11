from dataclasses import dataclass

from theme_switcher import config, regolith, sublime, terminal

THEMES_KEY = 'themes'


@dataclass
class Theme:
    name: str
    sublime_theme: str
    regolith_look: str
    terminal_profile: str

    def save(self) -> None:
        config.set_user('.'.join([THEMES_KEY, self.name]), dict(self))

    def __iter__(self):
        yield ('sublime_theme', self.sublime_theme)
        yield ('regolith_look', self.regolith_look)
        yield ('terminal_profile', self.terminal_profile)

    @classmethod
    def load(cls, name):
        try:
            theme_conf = config.get('.'.join([THEMES_KEY, name]))
        except config.NoValue:
            raise NoSuchTheme(name)

        return cls(name, **theme_conf)

    def activate(self) -> None:
        regolith.set_look(self.regolith_look)
        sublime.set_theme(self.sublime_theme)
        active_term_theme_id = config.get(terminal.PROFILE_ID_CONFIG_KEY)
        terminal.patch_console_profile(
            profile_id=active_term_theme_id,
            source_profile_id=self.terminal_profile)


def get_themes() -> list[Theme]:
    # we don't want to get from all config, just from file config
    try:
        theme_dict = config.get_from_config_files(THEMES_KEY)
    except config.NoValue:
        theme_dict = {}

    return [Theme(name=key, **vals) for key, vals in theme_dict.items()]


class NoSuchTheme(Exception):
    def __init__(self, name: str):
        self.name = name
        msg = f'The theme {name} does not exist!'
        super().__init__(msg)


if __name__ == '__main__':
    import fire
    fire.Fire(get_themes)
