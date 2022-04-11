import argparse
import fire
import inquirer

from theme_switcher import (config, main, regolith, sublime, terminal)


def add(parsed) -> None:

    terminal_choices = [(profile['visible-name'], profile_id) for profile_id, profile in terminal.get_profiles().items()]
    inquiries = [
        inquirer.Text('name', message='Theme name', default=parsed.name),
        inquirer.List('sublime_theme', message="Choose a sublime text theme", choices=sublime.get_themes()),
        inquirer.List('regolith_look', message="Choose a Regolith Look", choices=regolith.get_looks()),
        inquirer.List('terminal_profile', message="Choose a Terminal profile", choices=terminal_choices)
    ]

    answers = inquirer.prompt(inquiries)

    theme = main.Theme(**answers)

    theme.save()

    return theme


def do_list(_parsed) -> None:
    # TODO: verbosities
    for theme in main.get_themes():
        print(theme.name)


def do_set(parsed) -> None:
    theme = main.Theme.load(parsed.theme)
    theme.activate()

    print(parsed)


def entrypoint() -> None:
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(required=True)

    add_parser = subparsers.add_parser('add')
    add_parser.set_defaults(function=add)

    add_parser.add_argument('name', type=str, default=None, nargs='?')

    list_parser = subparsers.add_parser('list', aliases=['ls'])
    list_parser.set_defaults(function=do_list)

    set_parser = subparsers.add_parser('set', aliases=['apply', 'use'])
    set_parser.set_defaults(function=do_set)

    set_parser.add_argument('theme', choices=list(theme.name for theme in main.get_themes()))
    parsed = parser.parse_args()

    parsed.function(parsed)


