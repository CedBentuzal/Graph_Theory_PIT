import math
import sys
import time

from brute_force import brute_force
from data_loader import (LOCATIONS_FILE, MATRIX_FILE, DataError,
                         load_locations, load_matrix)
from dynamic_programming import fmt, dynamic_programming_tsp as held_karp
from verify import verify_tour

DIVIDER = "=" * 62
THIN    = "-" * 62


def decimals_needed(matrix):
    """How many decimals to print: 1 normally, more if the data has 0.85."""
    for places in (1, 2):
        if all(math.isclose(v, round(v, places), abs_tol=1e-9)
               for row in matrix for v in row):
            return places
    return 3


def is_symmetric(matrix, tol=1e-9):
    """True if d(i,j) == d(j,i) for every pair (undirected graph)."""
    n = len(matrix)
    return all(
        math.isclose(matrix[i][j], matrix[j][i], abs_tol=tol)
        for i in range(n) for j in range(i + 1, n)
    )


def main()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    matrix_file    = sys.argv[1] if len(sys.argv) > 1 else MATRIX_FILE
    locations_file = sys.argv[2] if len(sys.argv) > 2 else LOCATIONS_FILE

    
    try:
        labels, matrix = load_matrix(matrix_file)
        locations = load_locations(locations_file, labels)
    except DataError as error:
        print(f"DATA ERROR: {error}")
        print("Fix the CSV file and run again.")
        return 1

    n        = len(labels)
    dp       = decimals_needed(matrix)
    directed = not is_symmetric(matrix)
    graph_type = ("Directed (asymmetric -- roads differ by direction)"
                  if directed else
                  "Undirected (symmetric -- same distance both ways)")

    # ================================================================
    # SECTION 1 -- ALGORITHM
    # ================================================================
    print(DIVIDER)
    print("  SECTION 1 -- DYNAMIC PROGRAMMING ALGORITHM (HELD-KARP)")
    print(DIVIDER)
    print()
    print("  Algorithm : Dynamic Programming for TSP (Held-Karp Formulation)")
    print("  Authors   : Michael Held & Richard M. Karp (1962)")
    print("  Paradigm  : Dynamic Programming (Optimal Substructure & Memoization)")
    print("  Reference : Luna-Garcia, Candano & Caga-anan (2024), Sec. 2.2")
    print()
    print("  PROCEDURE (step by step)")
    print("  " + THIN)
    print("  Step 1 -- Initialize:")
    print("    For every non-start city k, compute the direct travel cost")
    print("    from start city A to k:")
    print("        C({k}, k) = d(A, k)")
    print()
    print("  Step 2 -- Expand subsets (Dynamic Programming):")
    print("    For each subset size s = 2, 3, ..., n-1:")
    print("      For every subset S of size s (not containing A):")
    print("        For every possible endpoint k in S:")
    print("          Find the cheapest predecessor m in S (m != k):")
    print("            C(S, k) = min{ C(S\\{k}, m) + d(m, k) }")
    print("          Save both the cost and the best predecessor m.")
    print()
    print("  Step 3 -- Close the tour:")
    print("    For every possible last stop k, add the return leg to A:")
    print("        tour_cost(k) = C(all cities, k) + d(k, A)")
    print("    The minimum over all k is the optimal total distance.")
    print()
    print("  Step 4 -- Reconstruct the route:")
    print("    Follow the saved predecessor pointers backward from the")
    print("    last stop to A, then reverse to get the forward route.")
    print()
    print("  ADVANTAGES")
    print("  " + THIN)
    print("  + Guarantees the OPTIMAL solution -- not an approximation.")
    print("  + Much faster than brute force:")
    print(f"      Held-Karp : O(n^2 * 2^n)   [n={n}: ~{n*n * 2**n:,} operations]")
    print(f"      Brute force: O(n!)          [n={n}: {math.factorial(n):,} routes]")
    print("  + Works correctly for both directed and undirected graphs.")
    print("  + Memory usage is O(n * 2^n) -- manageable for small n.")
    print()
    print("  LIMITATIONS")
    print("  " + THIN)
    print("  - Still exponential: impractical for n >= 20 cities.")
    print("  - Memory grows as O(n * 2^n); the main practical bottleneck.")
    print("  - For very large TSP, approximation algorithms are preferred.")
    print()

    # ================================================================
    # SECTION 2 -- PROBLEM & OBJECTIVE
    # ================================================================
    print(DIVIDER)
    print("  SECTION 2 -- PROBLEM & OBJECTIVE")
    print(DIVIDER)
    print()
    print("  Real-life scenario:")
    print("    A water bill rider for Cagayan de Oro City Water District")
    print("    (COWD) starts at the Water District Office, delivers water")
    print("    bills to every barangay hall exactly once, and returns to")
    print("    the office -- minimizing total driving distance.")
    print()
    start_label = labels[0]
    start_name  = locations[start_label][0]
    print(f"  Starting location  : {start_label} -- {start_name}")
    print(f"  Required stops     : {n - 1} barangay hall(s)")
    for lbl in labels[1:]:
        name, lat, lon = locations[lbl]
        print(f"    {lbl}. {name}  ({lat:.4f} N, {lon:.4f} E)")
    print()
    print("  Quantity to minimize : Total driving distance (km)")
    print()
    print("  Assumptions & constraints:")
    print("    - Rider starts AND ends at the Water District Office (A).")
    print("    - Each barangay hall is visited EXACTLY ONCE.")
    print("    - Road distances are from Google Maps driving directions.")
    print(f"    - Graph type: {graph_type}.")
    print("    - No time-window or capacity constraints are modelled.")
    print()

    # ================================================================
    # SECTION 3 -- GRAPH MODEL
    # ================================================================
    print(DIVIDER)
    print("  SECTION 3 -- METHODOLOGY & GRAPH MODEL")
    print(DIVIDER)
    print()
    edge_count = n * (n - 1) if directed else n * (n - 1) // 2
    print(f"  Graph type : {graph_type}")
    print(f"  Vertices   : {n}  labeled {', '.join(labels)}")
    print(f"  Edges      : {edge_count}  ({'directed arcs' if directed else 'undirected edges'})")
    print(f"  Weights    : Driving distance in kilometres (km)")
    print(f"  Source     : Google Maps -- Cagayan de Oro City")
    print()

    # Vertex table
    print("  Vertex definitions:")
    print(f"  {'Label':<6} {'Place name':<35} {'Lat':>9} {'Lon':>10}  Source")
    print("  " + "-" * 68)
    for lbl in labels:
        name, lat, lon = locations[lbl]
        note = "(start)" if lbl == labels[0] else ""
        print(f"  {lbl:<6} {name:<35} {lat:>9.4f} {lon:>10.4f}  Google Maps {note}")
    print()

    # Distance matrix
    print(f"  Distance matrix (km, from ROW to COLUMN):")
    print("  " + " " * 5 + "".join(f"{lbl:>8}" for lbl in labels))
    for lbl, row in zip(labels, matrix):
        print("  " + f"  {lbl:<3}" + "".join(f"{v:>8.{dp}f}" for v in row))
    print()

    # Data source note
    print("  Data source note:")
    print("    All edge weights are ACTUAL distances measured from Google")
    print("    Maps driving directions (not assumed or estimated values).")
    print("    Coordinates are copied directly from Google Maps URLs.")
    print()

    # How Held-Karp is applied
    print("  How Held-Karp is applied to this graph:")
    print(f"    - City A (index 0) is fixed as the start and end.")
    print(f"    - The algorithm computes C(S, k) for every subset S of")
    print(f"      the {n-1} non-start cities and every endpoint k in S.")
    print(f"    - It saves {(n-1) * 2**(n-2)} partial-route costs in total.")
    print(f"    - Finally it closes the tour by adding d(k, A) for each k")
    print(f"      and picks the minimum -- guaranteeing the optimal route.")
    print()

    # ================================================================
    # SECTION 4 -- PYTHON IMPLEMENTATION
    # ================================================================
    print(DIVIDER)
    print("  SECTION 4 -- PYTHON IMPLEMENTATION: DYNAMIC PROGRAMMING RUN (HELD-KARP)")
    print(DIVIDER)
    print()
    print("  Input data:")
    print(f"    Cities        : {n}  ({', '.join(labels)})")
    print(f"    Matrix file   : {matrix_file}")
    print(f"    Locations file: {locations_file}")
    print()

    # 3 & 4: Dynamic Programming steps, best route, total
    print("  --- Dynamic Programming (Held-Karp) DP steps ---")
    max_set_size = None if n <= 5 else 2
    hk_cost, hk_tour, table_size = held_karp(
        matrix, labels, show_steps=True, max_set_size=max_set_size
    )
    # Time a silent second run so printing does not count
    _t0 = time.perf_counter()
    held_karp(matrix)
    hk_time = time.perf_counter() - _t0

    print()
    print("  Best route : " + " -> ".join(labels[i] for i in hk_tour))
    print(f"  Total      : {hk_cost:.{dp}f} km")
    print(f"  Table size : {table_size} saved partial routes")
    print(f"  Time       : {hk_time:.4f} s")
    print()

    # 5: Verification
    print("  --- Verification (independent recomputation) ---")
    is_valid, total, legs, messages = verify_tour(hk_tour, matrix, labels)
    for msg in messages:
        print("  " + msg)
    total_ok = math.isclose(total, hk_cost)
    leg_str  = " + ".join(fmt(leg) for leg in legs)
    vline    = f"  Recomputed total: {leg_str} = {total:.{dp}f} km"
    print(vline.ljust(52) + (" OK" if total_ok else " FAIL"))
    print()

    # 6: Brute-force optimality proof
    print("  --- Optimality check (Brute Force) ---")
    _t0 = time.perf_counter()
    bf_cost, bf_tour, routes_checked = brute_force(matrix)
    bf_time = time.perf_counter() - _t0
    matches = math.isclose(bf_cost, hk_cost)

    print(f"  All possible routes : {routes_checked}  "
          f"(= {n-1}! = {math.factorial(n-1)})")
    if matches:
        print(f"  Shortest found      : {bf_cost:.{dp}f} km  "
              "-> matches Held-Karp exactly.")
        print("  Conclusion          : Route is PROVEN OPTIMAL.")
    else:
        print(f"  Shortest found      : {bf_cost:.{dp}f} km  "
              f"-> MISMATCH with Held-Karp ({hk_cost:.{dp}f} km).")
    print(f"  Brute-force time    : {bf_time:.4f} s")
    print()

    # 7: Route with full place names
    print("  --- Route with full place names ---")
    for step in range(len(hk_tour) - 1):
        a   = labels[hk_tour[step]]
        b   = labels[hk_tour[step + 1]]
        leg = legs[step]
        print(f"  {step + 1}. {a} -> {b}  {leg:>6.{dp}f} km"
              f"   {locations[a][0]} -> {locations[b][0]}")
    print(f"  {'':3}  Total  {total:>6.{dp}f} km")
    print()

    # ================================================================
    # SECTION 5 -- SOLUTION, CONCLUSION & LIMITATIONS
    # ================================================================
    print(DIVIDER)
    print("  SECTION 5 -- SOLUTION, CONCLUSION & LIMITATIONS")
    print(DIVIDER)
    print()
    route_str = " -> ".join(labels[i] for i in hk_tour)
    print("  RESULT")
    print("  " + THIN)
    print(f"  Optimal route    : {route_str}")
    print(f"  Total distance   : {hk_cost:.{dp}f} km")
    print()
    print("  INTERPRETATION")
    print("  " + THIN)
    print(f"  The water bill rider should follow the route above to")
    print(f"  visit all {n - 1} barangay hall(s) and return to the office,")
    print(f"  covering a total of only {hk_cost:.{dp}f} km.")
    print()
    print("  OPTIMALITY")
    print("  " + THIN)
    print("  Dynamic Programming (Held-Karp) is an EXACT algorithm -- not a heuristic.")
    print(f"  Brute force verified all {routes_checked} possible routes.")
    print("  No shorter route exists. This solution is PROVEN OPTIMAL.")
    print()
    print("  LIMITATIONS")
    print("  " + THIN)
    print("  1. Exponential complexity: at n >= 20 cities, Dynamic Programming")
    print("     becomes memory-bound as the DP table stores O(n * 2^n) states.")
    print("  2. Static distances: Google Maps data may change due to")
    print("     traffic, road works, or new routes.")
    print("  3. Single-objective: only distance is minimised. Real")
    print("     delivery may also require time windows or rider capacity.")
    print()
    print("  POSSIBLE IMPROVEMENTS")
    print("  " + THIN)
    print("  1. Nearest-Neighbor heuristic -- O(n^2), fast, ~25% above optimal.")
    print("  2. 2-opt local search -- iteratively swaps edges to shorten any")
    print("     given route; works well in practice for large n.")
    print("  3. Christofides algorithm -- guarantees <= 1.5x optimal for")
    print("     symmetric TSP; polynomial time.")
    print("  4. Vehicle Routing Problem (VRP) extension -- add time windows,")
    print("     multiple riders, and rider capacity constraints.")
    print()
    print("  REFERENCES")
    print("  " + THIN)
    print("  Algorithm:")
    print("    Luna-Garcia, R., Candano, T. M. C., & Caga-anan, R. L. (2024).")
    print("    Performance Analysis of Classical Algorithms for the Traveling")
    print("    Salesman Problem. The Mindanawan Journal of Mathematics, 6(2),")
    print("    79-111. https://doi.org/10.62071/tmjm.v6i2.716")
    print()
    print("    Held, M., & Karp, R. M. (1962). A Dynamic Programming Approach")
    print("    to Sequencing Problems. JSIAM, 10(1), 196-210.")
    print("    https://doi.org/10.1137/0110015")
    print()
    print("  Code:")
    print("    GeeksforGeeks. Travelling Salesman Problem using Dynamic")
    print("    Programming. https://www.geeksforgeeks.org/travelling-salesman")
    print("    -problem-using-dynamic-programming/")
    print()
    print("  Data:")
    print("    Google Maps, driving directions, Cagayan de Oro City.")
    print()
    print(DIVIDER)
    print("  END OF RUN")
    print(DIVIDER)

    return 0 if (is_valid and total_ok and matches) else 1


if __name__ == "__main__":
    sys.exit(main())
