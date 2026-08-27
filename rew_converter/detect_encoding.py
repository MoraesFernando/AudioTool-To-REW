"""Utilities for detecting the encoding of input files."""

import chardet
from chardet.resultdict import ResultDict


def detect_file_encoding(file_path: str) -> ResultDict:
    """Detect the encoding metadata for a file.

    Args:
        file_path: Path to the file to inspect.

    Returns:
        The metadata returned by ``chardet.detect``.

    Raises:
        OSError: If the file cannot be opened or read.
    """
    with open(file_path, "rb") as file:
        return chardet.detect(file.read())
