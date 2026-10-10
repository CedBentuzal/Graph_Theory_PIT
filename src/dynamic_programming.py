
import itertools
import math


def fmt(km):
    """Format a km value without trailing zeroes: 10.0 -> '10', 13.2999 -> '13.3'."""
    return f"{km:.3f}".rstrip("0").rstrip(".")


def dynamic_programming_tsp(matrix, labels=None, show_steps=False, max_set_size=None):
    """Find the shortest closed TSP tour using Dynamic Programming (Held-Karp).

    Parameters:
    -----------
    matrix        : matrix[i][j] = driving distance from vertex i to vertex j.
                    Vertex 0 is the starting origin (A).
    labels        : list of vertex label strings (e.g. ['A', 'B', 'C', 'D']).
    show_steps    : True to print memoized DP subproblem states C(S, k).
    max_set_size  : limit printed subsets to size <= max_set_size.

    Returns:
    --------
    (best_cost, tour, table_size)
      - best_cost  : optimal tour distance in km (float)
      - tour       : optimal sequence of vertex indices starting and ending at 0
      - table_size : number of subproblem entries stored in the DP table
    """
    d = matrix
    n = len(d)
    if n < 2:
        raise ValueError("Dynamic Programming TSP needs at least 2 places")
    if labels is None:
        labels = [chr(ord("A") + i) for i in range(n)]

    # Dynamic Programming Memoization Table:
    # Key: (S_bitmask, k) -> (min_cost, predecessor_m)
    C = {}

    # -------------------------------------------------------------------------
    # PART 1 - BASE CASES: Subsets with one place (size 1).
    #          C({k}, k) = d(A, k)
    # -------------------------------------------------------------------------
    for k in range(1, n):
        C[(1 << k, k)] = (d[0][k], 0)
        if show_steps:
            print(f"C({{{labels[k]}}}, {labels[k]}) = "
                  f"d({labels[0]},{labels[k]}) = {fmt(d[0][k])}")

    # -------------------------------------------------------------------------
    # PART 2 - DYNAMIC PROGRAMMING RECURRENCE: Subsets of size 2, 3, ..., n-1.
    #          C(S, k) = min_{m in S, m != k} [ C(S \ {k}, m) + d(m, k) ]
    # -------------------------------------------------------------------------
    hidden = 0
    for size in range(2, n):
        for places in itertools.combinations(range(1, n), size):
            S = sum(1 << p for p in places)  # Bitmask representing subset S

            for k in places:                 # Terminating vertex k in S
                S_without_k = S & ~(1 << k)  # Subset without k: S \ {k}
                best = math.inf
                parent = None

                for m in places:             # Predecessor m in S, m != k
                    if m == k:
                        continue
                    # Overlapping subproblem lookup: retrieve memoized cost for C(S \ {k}, m)
                    cost = C[(S_without_k, m)][0] + d[m][k]
                    if cost < best:
                        best = cost
                        parent = m

                # Store optimal subproblem solution in DP table
                C[(S, k)] = (best, parent)

                if show_steps:
                    if max_set_size is None or size <= max_set_size:
                        names = ",".join(labels[p] for p in places)
                        print(f"C({{{names}}}, {labels[k]}) = {fmt(best)} "
                              f"(came from {labels[parent]})")
                    else:
                        hidden += 1

    if show_steps and hidden:
        print(f"... ({hidden} more saved answers for bigger sets, not shown)")

    # -------------------------------------------------------------------------
    # PART 3 - TOUR CLOSURE: Return leg to origin vertex A.
    #          optimal_cost = min_{k} [ C(all_places, k) + d(k, A) ]
    # -------------------------------------------------------------------------
    ALL = (1 << n) - 2  # Bitmask of all places except A
    best_cost = math.inf
    last = None

    for k in range(1, n):
        cost = C[(ALL, k)][0] + d[k][0]
        if show_steps:
            print(f"Close: C(all, {labels[k]}) + d({labels[k]},{labels[0]}) = "
                  f"{fmt(C[(ALL, k)][0])} + {fmt(d[k][0])} = {fmt(cost)}")
        if cost < best_cost:
            best_cost = cost
            last = k

    # -------------------------------------------------------------------------
    # PART 4 - ROUTE RECONSTRUCTION: Backtrack through DP parent pointers.
    # -------------------------------------------------------------------------
    route = []
    S = ALL
    k = last
    while k != 0 and k is not None:
        route.append(k)
        parent = C[(S, k)][1]
        S = S & ~(1 << k)
        k = parent
    tour = [0] + route[::-1] + [0]

    return best_cost, tour, len(C)


# Aliases
held_karp = dynamic_programming_tsp
dynamic_programming = dynamic_programming_tsp
tsp_dynamic_programming = dynamic_programming_tsp
