"""Paired bootstrap confidence intervals (deterministic: fixed seed)."""
import random


def paired_bootstrap_ci(pairs_a, pairs_b, n_boot=10000, seed=12345):
    """pairs_a, pairs_b: per-instance 0/1 outcomes for two arms, same order.
    Returns (mean_diff, lo, hi) for b - a, percentile 95% CI."""
    assert len(pairs_a) == len(pairs_b) and len(pairs_a) > 0
    n = len(pairs_a)
    rng = random.Random(seed)
    diffs = []
    for _ in range(n_boot):
        sa = sb = 0
        for _ in range(n):
            i = rng.randrange(n)
            sa += pairs_a[i]
            sb += pairs_b[i]
        diffs.append((sb - sa) / n)
    diffs.sort()
    mean = sum(pairs_b[i] - pairs_a[i] for i in range(n)) / n
    lo = diffs[int(0.025 * n_boot)]
    hi = diffs[int(0.975 * n_boot) - 1]
    return mean, lo, hi


def wilson_interval(k, n, z=1.96):
    """Wilson 95% interval for a binomial proportion."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))
