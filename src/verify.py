"""
verify.py - checks that a route is a valid closed tour and adds up the km again.

    verify_tour(tour, matrix, labels=None)
        -> (is_valid, recomputed_total, legs, messages)

This does NOT use any Held-Karp code. It is a separate check, so a bug in
the algorithm cannot hide here.
"""


def verify_tour(tour, matrix, labels=None):
    """Check a tour like [0, 2, 3, 1, 0].

    Returns (is_valid, recomputed_total, legs, messages):
        is_valid          True if both checks pass
        recomputed_total  the sum of the legs
        legs              the km of each road, in tour order
        messages          one printable line per check
    """
    n = len(matrix)
    if labels is None:
        labels = [chr(ord("A") + i) for i in range(n)]
    start = labels[0]

    # Check 1: the tour starts with 0 (A) and ends with 0 (A).
    starts_and_ends = len(tour) >= 2 and tour[0] == 0 and tour[-1] == 0

    # Check 2: the places between are exactly 1 .. n-1, each one once.
    middle = list(tour[1:-1])
    visits_once = sorted(middle) == list(range(1, n))

    is_valid = starts_and_ends and visits_once

    # Add the distances again: each leg goes FROM tour[i] TO tour[i+1].
    legs = []
    if all(isinstance(p, int) and 0 <= p < n for p in tour):
        for i in range(len(tour) - 1):
            legs.append(matrix[tour[i]][tour[i + 1]])
    recomputed_total = sum(legs)

    messages = [
        f"Starts and ends at {start} ............ " + ("OK" if starts_and_ends else "FAIL"),
        "Each place visited exactly once . " + ("OK" if visits_once else "FAIL"),
    ]
    return is_valid, recomputed_total, legs, messages
