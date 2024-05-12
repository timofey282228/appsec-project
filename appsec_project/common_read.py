import logging

from typing import *
from numbers import Number

logger = logging.getLogger(__name__)


def get_readings_for[
    T: Number
](input_reader: Callable[[], Tuple[str, List[T]]], times, auth_phrase) -> Generator[
    List[T], None, None
]:
    for _ in range(times):
        while True:
            input_str, intervals = input_reader()
            if input_str == auth_phrase:
                break
            else:
                print("[!] Incorrect phrase")
                logger.debug(
                    "Incorrect auth phrase: '%s' != '%s'", input_str, auth_phrase
                )

        yield intervals
