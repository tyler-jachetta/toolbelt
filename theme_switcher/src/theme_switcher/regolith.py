import fire
import subprocess


def get_looks() -> set[str]:
    res = subprocess.check_output(['regolith-look', 'list'])

    print(res)
    return set(look.decode().strip() for look in subprocess.check_output(['regolith-look', 'list']).splitlines())


def set_look(look: str) -> None:

    subprocess.check_call(['regolith-look', 'set', look])
    subprocess.check_call(['regolith-look', 'refresh'])


if __name__ == '__main__':
    fire.Fire(get_looks)
