from z3 import *
from utils import *
import time

def extract_solution(model, x, y, distance_i, D, m, n, s, capacities):
    assigned_matrix = []
    D_val = model.evaluate(D, model_completion=True)
    print(f"Minimum possible maximum distance (D) = {D_val}")
    print("")
    try:
        for i in range(m):
            print(f"=== Courier {i} ===")
            assigned_items = []
            for j in range(n):
                for k in range(n):
                    if is_true(model.evaluate(x[i, j, k], model_completion=True)):
                        assigned_items.append((j, k))
            assigned_items_sorted = sorted(assigned_items, key=lambda tup: tup[1])
            sorted_items = [item for (item, pos) in assigned_items_sorted]
            load_i = sum(s[j] for j in sorted_items)
            print(f"Assigned items (sorted by position) = {sorted_items}")
            print(f"Total load = {load_i} (capacity = {capacities[i]})")  # use capacities[i] here
            dist_val = model.evaluate(distance_i[i], model_completion=True)
            print(f"Distance traveled = {dist_val}")
            # (Route reconstruction code follows here...)
            # [Route reconstruction code omitted for brevity]
            print("")
            for idx, item in enumerate(sorted_items):
                sorted_items[idx] = item+1
            assigned_matrix.append(sorted_items)
        return assigned_matrix, D_val
    except e:
        print(e)
        return [], D_val



def run_model_3d(m, n, l, s, D_matrix, origin, symmetry, instance):
    start_time = time.time()
    model_name = f"SMT3D{'_symmetry' if symmetry else ''}"
    capacities = l.copy()
    lower_bound, upper_bound = compute_bounds(D_matrix, m, n)
    print(lower_bound, upper_bound)
    
    # Create an Optimize object
    solver = Optimize()

    # x[i, j, k] is True if courier i delivers item j in position k
    # Item-to-Courier Assignment Variables to position
    x = {}
    for i in range(m):
        for j in range(n):
            for k in range(n):
                x[i, j, k] = Bool(f"x_{i}_{j}_{k}")

    # Route/Arc Variables
    y = {}
    for i in range(m):
        for u in range(n + 1):  # nodes: items and origin
            for v in range(n + 1):
                y[i, u, v] = Bool(f"y_{i}_{u}_{v}")
    
    # Courier Distance Variables
    distance_i = {}
    for i in range(m):
        distance_i[i] = Real(f"distance_{i}")
        
    # Global Maximum Distance
    D = Real("D")
    
    # Constraints 
    # 1. Each item is assigned exactly once
    # Sum over all couriers and positions and delivery positions for each item equals 1.
    for j in range(n):
        solver.add(Sum([If(x[i, j, k], 1, 0) for i in range(m) for k in range(n)]) == 1)

    # 2 Capacity Constraints:
    # Total load delivered by courier i (summing each item only once) must be within its capacity.
    for i in range(m):
        solver.add(Sum([If(x[i, j, k], s[j], 0) for j in range(n) for k in range(n)]) <= l[i])

    # 2.1. Capacity constraint
    # At most one item is delivered per courier at each delivery position.
    # this is due to the nature of the 3D matrix so that they dont overlap
    for i in range(m):
        for k in range(n):
            solver.add(Sum([If(x[i, j, k], 1, 0) for j in range(n)]) <= 1)

    # 3. Symmetry Breaking
    # Order couriers by the sum of their assigned item indices to break symmetry
    if symmetry:
        for i in range(m - 1):
            sum_first_i   = Sum([If(x[i, j, 0], j, 0) for j in range(n)])
            sum_first_ip1 = Sum([If(x[i+1, j, 0], j, 0) for j in range(n)])
            solver.add(sum_first_i <= sum_first_ip1)

    # 4. Route consistency constraints
    # make sure that courier must take its next item in the order they are assigned
    # simplifies model
    for i in range(m):
        for k in range(n - 1):
            # If no item is assigned at position k, then none should be assigned at k+1.
            solver.add(Implies(Sum([If(x[i, j, k], 1, 0) for j in range(n)]) == 0,
                               Sum([If(x[i, j, k+1], 1, 0) for j in range(n)]) == 0))

    # 5. Enforce at least one item per courier    *******
    for i in range(m):
        solver.add(Or([x[i, j, k] for j in range(n) for k in range(n)]))


    # # Link assignments to route arcs:
    # If courier i delivers item j at position k and item l at position k+1,
    # then the arc from j to l must be activated.
    for i in range(m):
        for k in range(n - 1):
            for j in range(n):
                for l in range(n):
                    solver.add(Implies(And(x[i, j, k], x[i, l, k+1]), y[i, j, l]))

    # 6. Forbid self-loops
    for i in range(m):
        for u in range(n + 1):  # items + origin
            solver.add(Not(y[i, u, u]))

    # 7. Enforce courier must leave origin once and return once (Like 6)
    for i in range(m):
        for j in range(n):
            solver.add(Implies(x[i, j, 0], y[i, origin, j]))

    for i in range(m):
        for k in range(n):
            for j in range(n):
                if k == n-1:
                    # For the last possible position, enforce the arc to origin.
                    solver.add(Implies(x[i, j, k], y[i, j, origin]))
                else:
                    # If position k is used and position k+1 is not used at all, then j is last.
                    solver.add(Implies(And(x[i, j, k],
                                             Sum([If(x[i, l, k+1], 1, 0) for l in range(n)]) == 0),
                                           y[i, j, origin]))

    # 8. Distance Calculation
    # Compute each courier's total distance directly from the activated route arcs.
    for i in range(m):
        route_distance = Sum([If(y[i, u, v], D_matrix[u][v], 0) 
                              for u in range(n + 1) for v in range(n + 1)])
        solver.add(distance_i[i] == route_distance)

    # 9. Bound each courier's distance by D
    # Each courier’s distance must be less than or equal to D.
    for i in range(m):
        solver.add(distance_i[i] <= D)

    # 10. MTZ variables: u[i, j] for courier i and item j.
    u = {}
    for i in range(m):
        for j in range(n):
            u[i, j] = Int(f"u_{i}_{j}")
            # u[i, j] is between 1 and n (if item j is delivered by courier i)
            solver.add(u[i, j] >= 1)
            solver.add(u[i, j] <= n)

    # 11. Add MTZ subtour elimination constraints:
    # If courier i travels directly from item j to item k, then
    # u[i, k] must be at least u[i, j] + 1, adjusted by a big-M formulation.
    for i in range(m):
        for j in range(n):
            for k in range(n):
                if j != k:
                    # When y[i, j, k] is True then enforce u[i,k] >= u[i,j] + 1.
                    # When y[i, j, k] is False, the constraint is relaxed by subtracting n.
                    solver.add(u[i, k] >= u[i, j] + 1 - n * (1 - If(y[i, j, k], 1, 0)))

    # 12. Integrate Lower and Upper Bounds
    solver.add(D >= lower_bound)
    solver.add(D <= upper_bound)

    # 13. Objective: minimize D
    solver.set(timeout=300000)
    objective = solver.minimize(D)

    print(solver.sexpr())
    # Capture the SMT2-like representation
    smt2_str = solver.sexpr()

    # Save to a .smt2 file
    with open("model.smt2", "w") as f:
        f.write(smt2_str)
    # Solve
    result = solver.check()
    total_time = int(time.time() - start_time)
    if result == sat:
        model = solver.model()
        assigned_matrix, D_val = extract_solution(model, x, y, distance_i, D, m, n, s, capacities)
        
        final_dict = {
                "time": total_time,
                "optimal": True,
                "obj": int(D_val.as_string()),
                "sol": assigned_matrix
            }
        print(final_dict)
        save_json(final_dict, model_name, f"{int(instance)}.json", "res/SMT")
        # Optionally, compute and print overall statistics (e.g., time taken)
        # For example, if you recorded a start time, you might have:
        # total_time = time.time() - start_time
        # print(f"Total time taken: {total_time} seconds")
        
        # Optionally, store the result in JSON or another format as required.
    else:
        print("No solution or UNSAT.")
        model = solver.model()
        assigned_matrix, D_val = extract_solution(model, x, y, distance_i, D, m, n, s, capacities)
        final_dict = {
                "time": total_time,
                "optimal": False,
                "obj": int(D_val.as_string()),
                "sol": assigned_matrix
            }
        print(final_dict)
        save_json(final_dict, model_name, f"{int(instance)}.json", "res/SMT")


# m, n, l, s, D_matrix = read_dat_file('/Users/aaronsalazar/LocalDocs/Bologna/CDMO/Instances/inst02.dat')
# run_model_3d(m,n,l,s,D_matrix, n, symmetry=False, instance=2)
