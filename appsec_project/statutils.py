import logging

from numbers import Number
from math import sqrt
from scipy.stats import t, f
from typing import List


logger = logging.getLogger(__name__)


def significant[T: Number](intervals: List[T], a=0.05) -> list[T]:
    if len(intervals) < 2:
        return intervals
    
    intervals = intervals.copy()
    significant = []

    i = 0
    while i < len(intervals):
        sum_of_all = sum(intervals)
        n_considered = len(intervals) - 1

        partial_expectile = (sum_of_all - intervals[i]) / n_considered
        partial_dispersion = (
            sum(
                (
                    (interval - partial_expectile) ** 2
                    for interval in (intervals[:i] + intervals[i + 1 :])
                )
            )
            / n_considered
        )

        meanqv = sqrt(partial_dispersion)

        try:
            tp = abs((intervals[i] - partial_expectile) / meanqv)

        # special case
        except ZeroDivisionError:
            # outlier
            i += 1
            continue

        if tp > t(n_considered).ppf(1 - a):
            # outlier
            i += 1
            continue

        significant.append(intervals[i])
        i += 1

    logger.debug(
        "Throwing away %d of %d measurements",
        len(intervals) - len(significant),
        len(intervals),
    )

    return significant


def are_dispersions_homogeneous(s1, s2, n, a=0.05):
    variance_max = max(s1, s2)
    variance_min = min(s1, s2)
    try:
        fisher_co_p = variance_max / variance_min
    except ZeroDivisionError:
        return False
    
    fisher_co_t = f.ppf(1 - a, n - 1, n - 1)

    return not fisher_co_p > fisher_co_t


def are_centers_equal(ref: tuple, sample: tuple, n, a=0.05) -> bool:
    ref_expectile = ref[0]
    sample_expectile = sample[0]

    n = len(ref)

    ref_var = ref[1]
    sample_var = sample[1]

    S = sqrt((ref_var**2 + sample_var**2) * (n - 1) / (2 * n - 1))
    tp = abs(ref_expectile - sample_expectile) / (S * sqrt(2 / n))

    return not tp > t.pdf(1 - a, n - 1)


def expectile(array):
    if len(array) == 0:
        return 0
    
    return sum(array) / len(array)


def dispersion(array):
    if len(array) == 1:
        return 0
    
    e = expectile(array)
    return sum(((xi - e) ** 2 for xi in array)) / (len(array) - 1)
