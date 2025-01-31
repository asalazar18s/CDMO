from z3 import *
from utils import *
import time

def run_model_2d(m, n, l, s, D_matrix, ITEMS, origin, symmetry):
    start_time = time.time() 

    lower_bound, upper_bound = compute_bounds(D_matrix, ITEMS, m)
    print(f"Computed Lower Bound: {lower_bound}")
    print(f"Computed Upper Bound: {upper_bound}")

    # Create an Optimize object
    solver = Optimize()

    # Item-to-Courier Assignment Variables
    x = {}
    for i in range(m):
        for j in range(n):
            x[i, j] = Bool(f"x_{i}_{j}")

    # Route/Arc Variables
    y = {}
    for i in range(m):
        for u in range(n+1):
            for v in range(n+1):
                y[i, u, v] = Bool(f"y_{i}_{u}_{v}")

    ####################################
    # Forbid self-loops
    ####################################
    for i in range(m):
        for j in range(n+1):
            solver.add(Not(y[i, j, j]))

    # Courier Distance Variables
    distance_i = {}
    for i in range(m):
        distance_i[i] = Real(f"distance_{i}")

    # Global Maximum Distance
    D = Real("D")

    # Constraints
    ####################################
    # 1) Each item is assigned exactly once
    ####################################
    for j in range(n):
        solver.add(PbEq([(x[i, j], 1) for i in range(m)], 1))

    ####################################
    # 2) Capacity constraints
    ####################################
    for i in range(m):
        solver.add(PbLe([(x[i, j], s[j]) for j in range(n)], l[i]))

    ####################################
    # 3) Symmetry Breaking Constraints
    ####################################
    # Order couriers by the sum of their assigned item indices to break symmetry
    if(symmetry):
        for i in range(m - 1):
            lhs = Sum([If(x[i, j], j, 0) for j in range(n)])
            rhs = Sum([If(x[i + 1, j], j, 0) for j in range(n)])
            solver.add(lhs <= rhs)
            # Explanation:
            # This ensures that the sum of item indices assigned to courier i
            # is less than or equal to that of courier i+1, preventing
            # permutations of courier assignments that are symmetric.

    ####################################
    # 3) Route consistency constraints (simple version)
    ####################################

    for i in range(m):
        for j in range(n):
            # In-degree for location j if assigned to courier i
            solver.add(
                Sum([If(y[i, u, j], 1, 0) for u in range(n+1)]) == If(x[i, j], 1, 0)
            )
            # Out-degree for location j if assigned to courier i
            solver.add(
                Sum([If(y[i, j, v], 1, 0) for v in range(n+1)]) == If(x[i, j], 1, 0)
            )

    for i in range(m):
        # Count how many items are assigned to courier i
        assigned_count_i = Sum([If(x[i, j], 1, 0) for j in range(n)])
        
        # If courier i has at least one assigned item, it leaves the origin exactly once...
        solver.add(
            Sum([If(y[i, origin, v], 1, 0) for v in range(n)]) ==
            If(assigned_count_i > 0, 1, 0)
        )
        # ...and returns exactly once
        solver.add(
            Sum([If(y[i, u, origin], 1, 0) for u in range(n)]) ==
            If(assigned_count_i > 0, 1, 0)
        )

    ####################################
    # 4) Distance calculation
    ####################################
    for i in range(m):
        solver.add(
            distance_i[i] == 
            Sum([
                If(y[i, u, v], D_matrix[u][v], 0)
                for u in range(n+1)
                for v in range(n+1)
            ])
        )

    ####################################
    # 5) Bound each courier's distance by D
    ####################################
    for i in range(m):
        solver.add(distance_i[i] <= D)

    ####################################
    # 6) Integrate Lower and Upper Bounds
    ####################################

    # Add lower bound constraint
    solver.add(D >= lower_bound)

    # Uncomment the following line if you want to enforce the upper bound
    # solver.add(D <= upper_bound)

    ####################################
    # 7) Objective: minimize D
    ####################################
    # Set a 5-minute timeout (300,000 milliseconds)
    # solver.set(timeout=300000)
    obj = solver.minimize(D)

    # We'll set M to n (the total number of items).
    M = n

    ####################################
    # 8) MTZ variables and constraints
    ####################################

    # 8a) Define u[i,j] for each courier i and item j
    u = {}
    for i in range(m):
        for j in range(n):  # for each item j
            u[i, j] = Int(f"u_{i}_{j}")
            # Bound them from 1..n
            solver.add(u[i, j] >= 1)
            solver.add(u[i, j] <= n)

    # 8b) Add the MTZ constraints:
    for i in range(m):
        for j in range(n):
            for k in range(n):
                if j != k:  # no self loops
                    # If courier i travels j->k, then:
                    # u[i, k] >= u[i, j] + 1 - M*(1 - y[i, j, k])
                    solver.add(
                        u[i, k] >= 
                        u[i, j] + 1 
                        - M * (1 - If(y[i, j, k], 1, 0))
                    )

    # Solve
    result = solver.check()
    if result == sat:
        print("Solution is SAT. Optimal or near-optimal solution found.")
        model = solver.model()
        
        # Retrieve the minimized D
        D_val = model.evaluate(D, model_completion=True)
        print(f"Minimum possible maximum distance (D) = {D_val}")
        print("")
        
        origin = n  # Recall we used 'n' as the origin index
        
        for i in range(m):
            print(f"=== Courier {i} ===")
            
            # ---- 1) Which items are assigned to courier i?
            assigned_items = []
            for j in range(n):
                if model.evaluate(x[i, j], model_completion=True):
                    assigned_items.append(j)
            
            # Compute the total load
            load_i = sum(s[j] for j in assigned_items)
            print(f"Assigned items = {assigned_items}")
            print(f"Total load = {load_i} (capacity = {l[i]})")
            
            # ---- 2) Distance traveled
            dist_val = model.evaluate(distance_i[i], model_completion=True)
            print(f"Distance traveled = {dist_val}")
            
            # ---- 3) Reconstruct the route(s)
            # Gather all arcs y[i,u,v] that are True in the model
            arcs = []
            for u_node in range(n+1):
                for v_node in range(n+1):
                    if model.evaluate(y[i, u_node, v_node], model_completion=True):
                        arcs.append((u_node, v_node))
            
            # We might have multiple loops if sub-tours exist. Let's find them all.
            arcs_used = set(arcs)
            
            # A function to follow arcs from a start until we return or run out
            def follow_loop(start, arcs_used):
                route = [start]
                current = start
                while True:
                    # Find next 'v' if (current, v) is in arcs_used
                    next_vs = [v for (u, v) in arcs_used if u == current]
                    if len(next_vs) == 0:
                        # no continuation from current
                        break
                    # pick the first arc (there should typically be exactly 1 if no sub-subtour branching)
                    v = next_vs[0]
                    route.append(v)
                    arcs_used.remove((current, v))
                    current = v
                    if current == start:
                        # loop closed
                        break
                return route
            
            # NEW: If assigned_items is empty => no route
            if len(assigned_items) == 0:
                print("No route (courier may have 0 items).")
            else:
                # Exactly one route from origin -> ... -> origin
                loop = follow_loop(origin, arcs_used)
                
                # Convert numeric indices to strings
                route_str = " -> ".join(
                    ("origin" if node == origin else f"d{node}")
                    for node in loop
                )
                print(f"Route: {route_str}")
        
            print("")  # blank line
            end_time = time.time()
            print(end_time-start_time)
    else:
        print("No solution or UNSAT.")