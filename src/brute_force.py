"""
brute_force.py - tries EVERY possible route and keeps the shortest.

    brute_force(matrix) -> (best_cost, tour, routes_checked)

This is slow for many places ((n-1)! routes), but for our 6 to 8 places it
finishes instantly. We use it as proof: if brute force gives the same total
as Held-Karp, then the Held-Karp route really is the shortest.
"""

import itertools
import math


def brute_force(matrix):
    """Check every ordering of the places and return the shortest tour.

    matrix[i][j] = distance FROM place i TO place j. Place 0 is A, the start.
    """
    n = len(matrix)
    best_cost = math.inf
    best_tour = None
    routes_checked = 0

    # Every ordering of places 1 .. n-1 (A is fixed at the start and the end).
    for order in itertools.permutations(range(1, n)):
        tour = [0] + list(order) + [0]

        # Add up the roads in the order we drive them: from tour[i] to tour[i+1].
        total = 0
        for i in range(len(tour) - 1):
            total += matrix[tour[i]][tour[i + 1]]

        routes_checked += 1
        if total < best_cost:           # keep the smallest total
            best_cost = total
            best_tour = tour

    return best_cost, best_tour, routes_checked
