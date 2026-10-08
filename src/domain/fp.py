from functools import reduce
from typing import Callable, Any

def pipe(*funcs: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """Mengeksekusi rantai fungsi transformasi dari kiri ke kanan."""
    return lambda initial_value: reduce(lambda acc, f: f(acc), funcs, initial_value)