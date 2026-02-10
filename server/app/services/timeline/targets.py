from math import ceil


def round_sensibly(value: int) -> int:
    if value < 1_000:
        return int(ceil(value / 50.0) * 50)
    return int(ceil(value / 100.0) * 100)


def suggested_target(previous: int, multiplier: float) -> int:
    boosted = int(previous * multiplier)
    capped = min(boosted, int(previous * 1.4))
    return round_sensibly(capped)
