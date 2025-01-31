from z3 import *
from utils import *
import time

def run_model_3d(m, n, l, s, D_matrix, ITEMS, origin):
    # Start timing
    start_time = time.time()
    capacity = l
    # Compute lower and upper bounds
    lower_bound, upper_bound = compute_bounds(D_matrix, ITEMS, m)
    print(f"Computed Lower Bound: {lower_bound}")
    print(f"Computed Upper Bound: {upper_bound}")

    # Create an Optimize object
    solver = Optimize()

    # Item-to-Courier Assignment Variables (3D)
    x = {}
    for i in range(m):
        for j in range(n):
            for k in range(n):
                x[i, j, k] = Bool(f"x_{i}_{j}_{k}")

    # Route/Arc Variables
    y = {}
    for i in range(m):
        for u in range(n + 1):
            for v in range(n + 1):
                y[i, u, v] = Bool(f"y_{i}_{u}_{v}")

    ####################################
    # Forbid self-loops
    ####################################
    for i in range(m):
        for j in range(n + 1):
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
        solver.add(Sum([If(x[i, j, k], 1, 0) for i in range(m) for k in range(n)]) == 1)

    ####################################
    # 2) Capacity constraints
    ####################################
    for i in range(m):
        solver.add(Sum([If(x[i, j, k], s[j], 0) for j in range(n) for k in range(n)]) <= l[i])

    ####################################
    # 3) Symmetry Breaking Constraints
    ####################################
    # Order couriers by the sum of their assigned item indices at position 0 to break symmetry
    # for i in range(m - 1):
    #     lhs = Sum([If(x[i, j, 0], j, 0) for j in range(n)])
    #     rhs = Sum([If(x[i + 1, j, 0], j, 0) for j in range(n)])
    #     solver.add(lhs <= rhs)
    #     # Explanation:
        # This ensures that the sum of item indices assigned to courier i
        # at position 0 is less than or equal to that of courier i+1,
        # preventing permutations of courier assignments that are symmetric.

    ####################################
    # 4) Sequence Constraints
    ####################################
    for i in range(m):
        for j in range(n):
            for k in range(n):
                if k < n - 1:
                    # If courier i delivers item j at position k, then they must deliver some item at position k+1
                    solver.add(Implies(x[i, j, k], Or([x[i, l, k + 1] for l in range(n)])))
                else:
                    # If delivered at last position, return to origin
                    solver.add(Implies(x[i, j, k], y[i, j, origin]))
        
        for j in range(n):
            for k in range(n):
                for l in range(n):
                    if k < n - 1 and j != l:
                        # If courier i delivers item j at position k and item l at position k+1, then y[i, j, l] must be True
                        solver.add(Implies(And(x[i, j, k], x[i, l, k + 1]), y[i, j, l]))

    ####################################
    # 5) Distance calculation
    ####################################
    for i in range(m):
        # Initialize distance terms
        distance_terms = []
        
        # Distance from origin to first item
        distance_terms += [If(x[i, j, 0], D_matrix[origin][j], 0) for j in range(n)]
        
        # Distance between consecutive items
        for k in range(n - 1):
            for j in range(n):
                for l in range(n):
                    distance_terms.append(If(And(x[i, j, k], x[i, l, k + 1]), D_matrix[j][l], 0))
        
        # Distance from last item to origin
        distance_terms += [If(x[i, j, n - 1], D_matrix[j][origin], 0) for j in range(n)]
        
        # Define distance_i[i]
        solver.add(distance_i[i] == Sum(distance_terms))

    ####################################
    # 6) Bound each courier's distance by D
    ####################################
    for i in range(m):
        solver.add(distance_i[i] <= D)

    ####################################
    # 7) Integrate Lower and Upper Bounds
    ####################################
    # Add lower bound constraint
    solver.add(D >= lower_bound)

    # Uncomment the following line if you want to enforce the upper bound
    # solver.add(D <= upper_bound)

    ####################################
    # 8) Objective: minimize D
    ####################################
    # Set a 5-minute timeout (300,000 milliseconds)
    # solver.set(timeout=300000)
    obj = solver.minimize(D)

    # We'll set M to n (the total number of items).
    M = n

    ####################################
    # 9) MTZ variables and constraints
    ####################################

    # 9a) Define u[i,j] for each courier i and item j
    u = {}
    for i in range(m):
        for j in range(n):  # for each item j
            u[i, j] = Int(f"u_{i}_{j}")
            # Bound them from 1..n
            solver.add(u[i, j] >= 1)
            solver.add(u[i, j] <= n)

    # 9b) Add the MTZ constraints:
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
    end_time = time.time()  # Move this outside the if-else block

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
                for k in range(n):
                    if model.evaluate(x[i, j, k], model_completion=True):
                        assigned_items.append((j, k))
            
            # Sort assigned items by position
            assigned_items_sorted = sorted(assigned_items, key=lambda x: x[1])
            sorted_items = [item for (item, pos) in assigned_items_sorted]
            
            # Compute the total load
            load_i = sum(s[j] for j in sorted_items)
            print(f"Assigned items (sorted by position) = {sorted_items}")
            print(f"Total load = {load_i} (capacity = {capacity[i]})")
            
            # ---- 2) Distance traveled
            dist_val = model.evaluate(distance_i[i], model_completion=True)
            print(f"Distance traveled = {dist_val}")
            
            # ---- 3) Reconstruct the route(s)
            # Gather all arcs y[i,u,v] that are True in the model
            arcs = []
            for u_node in range(n + 1):
                for v_node in range(n + 1):
                    if model.evaluate(y[i, u_node, v_node], model_completion=True):
                        arcs.append((u_node, v_node))
            
            # Convert to a set for efficient removal
            arcs_used = set(arcs)
            loops = []
            
            if sorted_items:
                # Construct the route based on sorted items
                route = ["origin"]
                for item, pos in assigned_items_sorted:
                    route.append(f"d{item}")
                route.append("origin")  # Return to origin
                
                # Convert list to string representation
                route_str = " -> ".join(route)
                print(f"Route: {route_str}")
            else:
                print("No route (courier may have 0 items).")
        
            print("")  # blank line
        
        # Print total time taken
        print(f"Total time taken: {end_time - start_time} seconds")
        
    else:
        print("No solution or UNSAT.")
        # Print total time taken even if no solution
        print(f"Total time taken: {end_time - start_time} seconds")
