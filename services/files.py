from __future__ import annotations

import fcntl
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, IO


@contextmanager
def locked_file(path: Path, mode: str) -> Generator[IO[str], None, None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open(mode, encoding="utf-8") as file_obj:
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)
        try:
            yield file_obj
        finally:
            fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)


def read_json(path: Path, *, default):
    if not path.exists():
        return default
    with locked_file(path, "r") as file_obj:
        content = file_obj.read()
    if not content:
        return default
    import ujson

    return ujson.loads(content)


def write_json(path: Path, data) -> None:
    import ujson

    with locked_file(path, "w") as file_obj:
        file_obj.write(ujson.dumps(data, ensure_ascii=False, indent=2))
        file_obj.flush()


def append_jsonl(path: Path, data) -> None:
    import ujson

    with locked_file(path, "a") as file_obj:
        file_obj.write(ujson.dumps(data, ensure_ascii=False))
        file_obj.write("\n")
        file_obj.flush()


def tail(path: Path, lines: int) -> list[str]:
    if not path.exists():
        return []
    with locked_file(path, "r") as file_obj:
        content = file_obj.readlines()
    return content[-lines:]
