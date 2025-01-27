from z3 import *

# Problem Parameters
num_couriers = 2  # Number of couriers
num_load = 6  # Number of loads
courier_capacity = [15, 10]  # Capacity of each courier
load_size = [3, 2, 6, 5, 4, 4]  # Size of each load

distance = [  # Distance matrix (n+1 x n+1), where the last index (n+1) is the origin
    [0, 3, 4, 5, 6, 6, 2],
    [3, 0, 1, 4, 5, 7, 3],
    [4, 1, 0, 5, 6, 6, 4],
    [5, 4, 5, 0, 3, 3, 2],
    [6, 5, 6, 3, 0, 2, 4],
    [6, 7, 6, 3, 2, 0, 4],
    [2, 3, 4, 3, 4, 4, 0]
]

# Decision Variables
assign = [
    [Bool(f"assign_{i}_{j}") for j in range(num_load)]
    for i in range(num_couriers)
]  # assign[i][j]: Whether courier i is assigned to load j

tour = [
    [Int(f"tour_{i}_{k}") for k in range(num_load + 2)]
    for i in range(num_couriers)
]  # tour[i][k]: Location at position k in courier i's route

total_distance = [Int(f"total_distance_{i}") for i in range(num_couriers)]

# Solver
solver = Optimize()

# Constraints

# 1. Each load must be assigned to exactly one courier
for j in range(num_load):
    solver.add(Sum([If(assign[i][j], 1, 0) for i in range(num_couriers)]) == 1)

# 2. Each courier must not exceed their capacity
for i in range(num_couriers):
    solver.add(Sum([If(assign[i][j], load_size[j], 0) for j in range(num_load)]) <= courier_capacity[i])

# 3. Each courier's tour must start and end at the origin
for i in range(num_couriers):
    solver.add(tour[i][0] == num_load + 1)  # Start at origin (index num_load + 1)
    solver.add(tour[i][num_load + 1] == num_load + 1)  # End at origin

# 4. Prevent revisits: No location (except origin) appears more than once per tour
for i in range(num_couriers):
    for j in range(1, num_load + 1):
        solver.add(Sum([If(tour[i][k] == j, 1, 0) for k in range(1, num_load + 1)]) <= 1)

# 5. Ensure couriers cannot return to the origin before completing all deliveries
for i in range(num_couriers):
    for k in range(1, num_load + 1):  # Check all positions except the last (which must be the origin)
        solver.add(Implies(tour[i][k] == num_load + 1, Sum([If(tour[i][m] == j, 1, 0) for j in range(1, num_load + 1) for m in range(k + 1, num_load + 1)]) == 0))

# 6. Total distance calculation (fixed for symbolic indices)
for i in range(num_couriers):
    solver.add(total_distance[i] == Sum([
        Sum([
            If(And(tour[i][k] == p1, tour[i][k + 1] == p2), distance[p1 - 1][p2 - 1], 0)
            for p1 in range(1, num_load + 2)  # Include items (1..num_load) and origin (num_load + 1)
            for p2 in range(1, num_load + 2)
        ])
        for k in range(num_load + 1)
    ]))

# Objective: Minimize the maximum distance traveled by any courier
max_distance = Int("max_distance")
solver.add(max_distance >= total_distance[i] for i in range(num_couriers))
solver.minimize(max_distance)

# Solve and Output
if solver.check() == sat:
    model = solver.model()
    for i in range(num_couriers):
        assigned_items = [j for j in range(num_load) if model.evaluate(assign[i][j])]
        courier_tour = [model.evaluate(tour[i][k]) for k in range(num_load + 2)]
        total_dist = model.evaluate(total_distance[i])
        print(f"Courier {i} is assigned items: {assigned_items}")
        print(f"Courier {i}'s tour: {[int(courier_tour[k].as_long()) for k in range(len(courier_tour))]}")
        print(f"Courier {i}'s total distance: {total_dist}")
else:
    print("No solution exists.")
