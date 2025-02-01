from z3 import *
from utils import *
import time

def run_model_2d(m, n, l, s, D_matrix, origin, symmetry, instance):
    
    start_time = time.time()
    items = list(range(n))
    model_name = f"SMT2D{'_symmetry' if symmetry else ''}"
    lower_bound, upper_bound = compute_bounds(D_matrix, items)
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
        
        solver.add(assigned_count_i >= 1)

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
    solver.add(D <= upper_bound)

    ####################################
    # 7) Objective: minimize D
    ####################################
    # Set a 5-minute timeout (300,000 milliseconds)
    solver.set(timeout=300000)
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
    end_time = time.time()
    time_total = int(end_time - start_time)
    assigned_matrix = []
    if result == sat:
        print(f"Instance {instance}: Solution is SAT. Optimal or near-optimal solution found.")
        model = solver.model()
        
        # Retrieve the minimized D
        D_val = model.evaluate(D, model_completion=True)
        print(f"Instance {instance}: Minimum possible maximum distance (D) = {D_val}")
        
        origin = n  # Recall we used 'n' as the origin index
        assigned_matrix = []
        for i in range(m):
            print(f"=== Courier {i} ===")
            
            # ---- Reconstruct the route(s)
            # Gather all arcs y[i,u,v] that are True in the model
            arcs = []
            for u_node in range(n+1):
                for v_node in range(n+1):
                    if model.evaluate(y[i, u_node, v_node], model_completion=True):
                        arcs.append((u_node, v_node))
            
            arcs_used = set(arcs)
            
            if len(arcs) == 0:
                print("No route (courier may have 0 items).")
                # Since all couriers must have at least one item, this should not occur
                assigned_matrix.append([])
            else:
                # Reconstruct the route
                loop = follow_loop(origin, arcs_used)
                
                # Print the route
                route_str = " -> ".join(
                    ("origin" if node == origin else f"d{node}")
                    for node in loop
                )
                print(f"Route: {route_str}")
                
                # ---- 1) Extract ordered items based on the route
                # Exclude the origin (assuming origin is 'n')
                # Items are numbered from 0 to n-1, origin is n
                ordered_items = []
                for node in loop:
                    if node != origin:
                        ordered_items.append(node + 1)  # Adjust if you want 1-based indexing
                print(f"Ordered items = {ordered_items}")
                
                # ---- 2) Compute the total load based on ordered items
                # Note: ordered_items contains 1-based indices, so subtract 1 for 0-based access
                load_i = sum(s[node - 1] for node in ordered_items)
                print(f"Total load = {load_i} (capacity = {l[i]})")
                
                # ---- 3) Append the ordered list to assigned_matrix
                assigned_matrix.append(ordered_items)
            
        
        print(f"Instance {instance}: Total Time = {time_total} seconds")
        
        print("")  # blank line
        final_dict = {
                "time": time_total,
                "optimal": True,
                "obj": int(D_val.as_string()),
                "sol": assigned_matrix
            }
        
        print(final_dict)
        save_json(final_dict, f"SMT2D{'_symmetry' if symmetry else ''}", f"{int(instance)}.json", "res/SMT")
    else:
        print("No solution or UNSAT.")

        model = solver.model()
        D_val = model.evaluate(D, model_completion=True)
    # ---- Reconstruct the route using y variables
        arcs = []
        for u_node in range(n + 1):
            for v_node in range(n + 1):
                if model.evaluate(y[i, u_node, v_node], model_completion=True):
                    arcs.append((u_node, v_node))
        
        arcs_used = set(arcs)
        
        if not arcs:
            print("No route found for this courier.")
            assigned_matrix.append([])
        else:
            # Reconstruct the route starting from origin
            route = follow_loop(origin, arcs_used)
            
            # Print the reconstructed route
            route_str = " -> ".join(
                ("Origin" if node == origin else f"Item {node}") for node in route
            )
            print(f"Route: {route_str}")
            
            # ---- Extract ordered items based on the route
            # Exclude the origin from the items list
            ordered_items = [node for node in route if node != origin]
            print(f"Ordered Assigned Items: {ordered_items}")

            # ---- Compute the total load based on ordered items
            # Assuming items are 1-based in 'ordered_items' and 0-based in 's'
            load_i = sum(s[node - 1] for node in ordered_items)
            print(f"Total Load = {load_i} (Capacity = {l[i]})")
            
            # ---- Append the ordered list to assigned_matrix
            assigned_matrix.append(ordered_items)

        final_dict = {
                "time": 300,
                "optimal": False,
                "obj": int(D_val.as_string()),
                "sol": assigned_matrix
            }
        print(final_dict)
        save_json(final_dict, f"SMT2D{'_symmetry' if symmetry else ''}", f"{int(instance)}.json", "res/SMT")
        
        