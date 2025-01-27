from z3 import Solver, Int, Sum, If, And, Optimize, Distinct

# Input Data
num_couriers = 2
num_load = 6
courier_capacity = [15, 10]
load_size = [3, 2, 6, 5, 4, 4]
distance = [
    [0, 3, 4, 5, 6, 6, 2],
    [3, 0, 1, 4, 5, 7, 3],
    [4, 1, 0, 5, 6, 6, 4],
    [5, 4, 5, 0, 3, 3, 2],
    [6, 5, 6, 3, 0, 2, 4],
    [6, 7, 6, 3, 2, 0, 4],
    [2, 3, 4, 3, 4, 4, 0]
]
origin = num_load  # Origin index in the distance matrix (last row/column)

# Z3 Solver
solver = Optimize()

# Decision variables
load_assigned = [[Int(f"load_assigned_{i}_{j}") for j in range(num_load + 2)] for i in range(num_couriers)]
total_distance = [Int(f"total_distance_{i}") for i in range(num_couriers)]
weights = [Int(f"weights_{i}") for i in range(num_couriers)]
max_distance = Int("max_distance")  # Objective: minimize max distance

# Constraints

# 1. Route starts and ends at the base
for i in range(num_couriers):
    solver.add(load_assigned[i][0] == origin)  # Start at base
    solver.add(load_assigned[i][num_load + 1] == origin)  # End at base

# 2. Load assignment: each load must be assigned to exactly one courier and position
for load in range(num_load):
    solver.add(Sum([
        If(And(load_assigned[i][j] == load + 1, 1 <= j <= num_load), 1, 0)
        for i in range(num_couriers) for j in range(1, num_load + 1)
    ]) == 1)

# 3. Total weight for each courier must not exceed their capacity
for i in range(num_couriers):
    solver.add(weights[i] == Sum([
        If(load_assigned[i][j] == load + 1, load_size[load], 0)
        for j in range(1, num_load + 1) for load in range(num_load)
    ]))
    solver.add(weights[i] <= courier_capacity[i])

# 4. Total distance calculation for each courier
for i in range(num_couriers):
    solver.add(total_distance[i] == Sum([
        If(And(load_assigned[i][j] == load1 + 1, load_assigned[i][j + 1] == load2 + 1),
           distance[load1][load2], 0)
        for j in range(num_load + 1)  # Iterate over route positions
        for load1 in range(num_load + 1)  # Iterate over all possible loads (including base)
        for load2 in range(num_load + 1)  # Iterate over all possible loads (including base)
    ]))

# 5. Couriers cannot return to the base before completing all deliveries
for i in range(num_couriers):
    for j in range(1, num_load + 1):
        solver.add(If(load_assigned[i][j] == origin, 
                      And([load_assigned[i][k] == origin for k in range(j + 1, num_load + 2)]),
                      True))

# All positions in a route must be valid (1..num_load + 1)
for i in range(num_couriers):
    for j in range(num_load + 2):
        solver.add(And(load_assigned[i][j] >= 1, load_assigned[i][j] <= num_load + 1))

# Ensure loads within a courier's route are distinct (excluding the base)
for i in range(num_couriers):
    solver.add(Distinct([
        load_assigned[i][j]
        for j in range(1, num_load + 1)
    ] + [origin]))  # Ensure the base is part of the distinct check



# 6. Minimize maximum distance
solver.add(max_distance == Sum(total_distance))
solver.minimize(max_distance)

# Verify that the loads assigned to each courier fall within the valid range
for i in range(num_couriers):
    for j in range(num_load + 2):  # All positions in the route
        solver.add(And(load_assigned[i][j] >= 1, load_assigned[i][j] <= num_load + 1))


if solver.check().__str__() == "sat":
    model = solver.model()
    print("Solution found:")
    for i in range(num_couriers):
        route = [model.evaluate(load_assigned[i][j]).as_long() for j in range(num_load + 2)]
        dist = model.evaluate(total_distance[i]).as_long()
        print(f"Courier {i + 1}: Route {route}, Distance: {dist}")
    print(f"Max Distance: {model.evaluate(max_distance).as_long()}")
else:
    print("No solution exists.")

