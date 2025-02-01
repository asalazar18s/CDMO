from z3 import *
from utils import *
import time

def run_model_2d(m, n, l, s, D_matrix, origin, symmetry, instance):
    start_time = time.time()
    model_name = f"SMT2D{'_symmetry' if symmetry else ''}"
    lower_bound, upper_bound = compute_bounds(D_matrix, m, n)
    print(lower_bound, upper_bound)

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

    # Courier Distance Variables
    distance_i = {}
    for i in range(m):
        distance_i[i] = Real(f"distance_{i}")
    
    # Global Maximum Distance
    D = Real("D")

    # MTZ Variables for subtour elimination
    u = {}
    for i in range(m):
        for j in range(n):
            u[i, j] = Int(f"u_{i}_{j}")

    # Constraints
    # 1. Each item is assigned exactly once
    for j in range(n):
        solver.add(PbEq([(x[i, j], 1) for i in range(m)], 1))

    # 2. Capacity constraints
    for i in range(m):
        solver.add(PbLe([(x[i, j], s[j]) for j in range(n)], l[i]))

    # 3. Symmetry Breaking
    if symmetry:
        for i in range(m - 1):
            lhs = Sum([If(x[i, j], j, 0) for j in range(n)])
            rhs = Sum([If(x[i + 1, j], j, 0) for j in range(n)])
            solver.add(lhs <= rhs)

    # 4. Route consistency constraints
    for i in range(m):
        for j in range(n):
            # In-degree for location j if assigned to courier i
            solver.add(Sum([If(y[i, u, j], 1, 0) for u in range(n+1)]) == If(x[i, j], 1, 0))
            # Out-degree for location j if assigned to courier i
            solver.add(Sum([If(y[i, j, v], 1, 0) for v in range(n+1)]) == If(x[i, j], 1, 0))
        
        # Ensure each courier starts and ends at the depot
        solver.add(Sum([If(y[i, origin, v], 1, 0) for v in range(n)]) == 1)  # Start from depot
        solver.add(Sum([If(y[i, u, origin], 1, 0) for u in range(n)]) == 1)  # Return to depot
        
        # Each courier should have at least one item
        solver.add(Sum([If(x[i, j], 1, 0) for j in range(n)]) >= 1)

    # 5. Distance calculation
    for i in range(m):
        solver.add(
            distance_i[i] == 
            Sum([
                If(y[i, u, v], D_matrix[u][v], 0)
                for u in range(n+1)
                for v in range(n+1)
            ])
        )

    # 6. Bound each courier's distance by D
    for i in range(m):
        solver.add(distance_i[i] <= D)

    # 7. MTZ for subtour elimination
    M = n
    for i in range(m):
        for j in range(n):
            solver.add(u[i, j] >= 1)
            solver.add(u[i, j] <= n)
            for k in range(n):
                if j != k:
                    solver.add(
                        u[i, k] >= u[i, j] + 1 - M * (1 - If(y[i, j, k], 1, 0))
                    )

    # 8. Integrate Lower and Upper Bounds
    solver.add(D >= lower_bound)
    solver.add(D <= upper_bound)

    # 9. Objective: minimize D
    solver.set(timeout=300000)
    objective = solver.minimize(D)

    # Solve
    result = solver.check()
    total_time = int(time.time() - start_time)
    assigned_matrix = []
    if result == sat:
        print(f"Instance {instance}: Solution is SAT. Optimal or near-optimal solution found.")
        model = solver.model()
        
        D_val = model.evaluate(D, model_completion=True)
        print(f"Instance {instance}: Minimum possible maximum distance (D) = {D_val}")
        
        for i in range(m):
            print(f"=== Courier {i} ===")
            arcs = [(u, v) for u in range(n+1) for v in range(n+1) if is_true(model.evaluate(y[i, u, v]))]
            
            if not arcs:
                print("No route (courier may have 0 items).")
                assigned_matrix.append([])
            else:
                loop = follow_loop(origin, set(arcs))
                route_str = " -> ".join(("origin" if node == origin else f"d{node}") for node in loop)
                print(f"Route: {route_str}")
                
                ordered_items = [node + 1 for node in loop if node != origin]
                print(f"Ordered items = {ordered_items}")
                load_i = sum(s[node - 1] for node in ordered_items)
                print(f"Total load = {load_i} (capacity = {l[i]})")
                assigned_matrix.append(ordered_items)

        print(f"Instance {instance}: Total Time = {total_time} seconds")
        
        final_dict = {
            "time": total_time,
            "optimal": True,
            "obj": int(D_val.as_string()),
            "sol": assigned_matrix
        }
        print(final_dict)
        save_json(final_dict, model_name, f"{int(instance)}.json", "res/SMT")
    else:
        print("No solution or UNSAT.")

    if result != sat:
        model = solver.model()
        if model:
            D_val = model.evaluate(D, model_completion=True)
            assigned_matrix = []
            for i in range(m):
                arcs = [(u, v) for u in range(n+1) for v in range(n+1) if is_true(model.evaluate(y[i, u, v]))]
                
                if not arcs:
                    print("No route found for this courier.")
                    assigned_matrix.append([])
                else:
                    # Reconstruct the route starting from origin
                    route = follow_loop(origin, set(arcs))
                    
                    # Print the reconstructed route
                    route_str = " -> ".join(
                        ("Origin" if node == origin else f"Item {node}") for node in route
                    )
                    print(f"Route: {route_str}")
                    
                    # Extract ordered items based on the route
                    # Exclude the origin from the items list
                    ordered_items = [node for node in route if node != origin]
                    print(f"Ordered Assigned Items: {ordered_items}")

                    # Compute the total load based on ordered items
                    load_i = sum(s[node - 1] for node in ordered_items)
                    print(f"Total Load = {load_i} (Capacity = {l[i]})")
                    
                    # Append the ordered list to assigned_matrix
                    assigned_matrix.append(ordered_items)

            final_dict = {
                "time": 300,  # Assuming a timeout of 5 minutes
                "optimal": False,
                "obj": int(D_val.as_string()),
                "sol": assigned_matrix
            }
            print(final_dict)
            save_json(final_dict, model_name, f"{int(instance)}.json", "res/SMT")

# Helper function for checking if a Boolean value is true
def is_true(val):
    return val is not None and val.is_true()

# Note: 'follow_loop' function is assumed to be defined elsewhere or in 'utils.py'