"""
TBH I forget why I started writing a caching module in this package. mostly
just playing at this point I guess?
"""

from enum import Enum
from pathlib import Path
import pickle
from tempfile import TemporaryFile
from typing import Any, Optional

# make `Path` a class
Path = Path('.').__class__

NO_DEFAULT = object()


class RunScopeMixin:

    def _read_cache(self):
        raise NotImplementedError()

    def _write_cache(self):
        raise NotImplementedError()

    def store(self, key, value, overwrite=True) -> bool:

        cache = self._read_cache()
        if key in cache and cache[key] == value:
            return False

        elif (not overwrite) and key in cache:
            raise NotOverwriting()

        cache[key] = value
        self._write_cache(cache)

    def retrieve(self, key: str, default: Optional[Any] = NO_DEFAULT):
        cache = self._read_cache()
        value = cache.get(key, default)

        if value is NO_DEFAULT:
            raise KeyError(f'No object in cache at {key}')

        return value


class RunScopeTemp(RunScopeMixin):
    """
    tempfile.TemporaryFile is a function, despite its CamelCase
    """

    def __init__(self, mode='ab+', **kwargs):
        self.file = TemporaryFile(mode, **kwargs)

    def _read_cache(self) -> dict:
        self.file.seek(0)
        pickled = self.file.read()
        if not pickled:
            return {}
        return pickle.loads(pickled)

    def _write_cache(self, cache) -> None:

        self.file.seek(0)
        self.file.truncate()
        self.file.write(pickle.dumps(cache))


class RunScopeFile(Path, RunScopeMixin):

    def _read_cache(self) -> str:
        try:
            cache = self.read_bytes()
        except FileNotFoundError:
            return {}
        return pickle.loads(cache)

    def _write_cache(self, cache: str) -> None:
        self.write_bytes(pickle.dumps(cache))


class Scope(Enum):
    GLOBAL = RunScopeFile('/var/cache/theme_switcher')
    USER = RunScopeFile.home().joinpath('.cache', 'theme_switcher')
    RUN = RunScopeTemp()


def store(
        key: str, value: Any,
        overwrite: Optional[bool] = True,
        scope: Optional[Scope] = Scope.RUN) -> None:

    return scope.value.store(key, value, overwrite=overwrite)


def retrieve(
        key: str, default: Optional[Any] = NO_DEFAULT,
        scope: Optional[Scope] = Scope.RUN) -> Any:
    return scope.value.retrieve(key, default=default)


class NotOverwriting(Exception):
    pass
