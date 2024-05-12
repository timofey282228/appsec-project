import time
import msvcrt
import logging

logger = logging.getLogger(__name__)

# TODO uses OS-specific functionalit; breaks on invalid unicode (somehow gets some!)
def win_read_cli():
    phrase = b""
    intervals = []
    t = time.perf_counter_ns()

    while True:
        # c = sys.stdin.read(1)  # nah
        c = msvcrt.getch()
        if c == b"\r":
            break
        elif c == b"\x03":
            raise KeyboardInterrupt

        phrase += c

        new_t = time.perf_counter_ns()
        intervals.append(
            (new_t - t)
        )
        t = new_t
    
    if intervals:
        intervals.pop(0)  # interval before first char

    phrase = phrase.decode(errors="replace")
    logger.debug("Read phrase: %s (%s)", phrase, intervals)
    return phrase, intervals
